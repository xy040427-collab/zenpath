"""
School Detail Generator v2 — enriched CHSI RAG → DeepSeek → file cache.

v2 changes:
  - top_k 5→10, content limit 500→3000 chars
  - 8 items per doc_type instead of 3
  - Richer output: campus_info, contact, major_categories, history, annual_summary
  - Admission policies with full clause text
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI
from rag.evidence_packer import pack_evidence
from rag.retrieval.chsi_vector_retriever import ChsiVectorRetriever

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parents[3] / "rag_output" / "cache" / "schools"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEEPSEEK_API_KEY = "os.environ.get("DEEPSEEK_API_KEY", "")"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-v4-pro"

SYSTEM_PROMPT = """你是高考志愿填报助手，基于教育部阳光高考平台官方数据生成院校详细介绍。

## 输出格式（严格 JSON）

{
  "school_name": "学校全称",
  "overview": "学校概况（300-500字，涵盖历史沿革、办学层次、学科特色、社会声誉）",
  "basic_info": {
    "province": "所在省份",
    "city": "所在城市",
    "department": "主管部门（教育部/省教育厅等）",
    "level": "办学层次（如：双一流/985/211/省重点）",
    "type": "院校类型（综合/理工/师范/医药/农林/政法/艺术/体育等）",
    "is_public": true
  },
  "campuses": [
    {"name": "校区名称", "address": "详细地址", "phone": "电话"}
  ],
  "official_site": "https://...",
  "admission_site": "https://...",
  "contact_phone": "招生咨询电话",
  "tags": ["985", "211", "双一流", "综合类", "C9联盟"],
  "major_categories": [
    {"name": "学科门类/专业大类名称", "majors": ["具体专业1", "具体专业2"]}
  ],
  "departments": [
    {"name": "院系名称", "description": "院系简介（50-100字）"}
  ],
  "admission_policies": [
    {
      "clause_number": "第X条",
      "title": "条款主题",
      "content": "条款完整内容"
    }
  ],
  "admission_summary": "招生政策总体概述（150字内，总结招生模式、录取规则要点）",
  "source": "数据来源：教育部阳光高考平台 (gaokao.chsi.com.cn)",
  "generated_at": "生成时间ISO字符串"
}

## 数据提取规则

1. **overview**: 从 school_profile 的"学校简介"和"基础信息"中提取，必须涵盖：
   - 学校历史沿革（建校时间、重要发展节点）
   - 办学层次与定位
   - 学科特色与优势领域
   - 300-500字，内容充实

2. **basic_info**: 从 school_profile "基础信息"中精确提取
   - department 字段：教育部直属/省属等
   - level: 根据 tags 推断（有"双一流"tag→双一流，有985→985，有211→211）
   - type: 从数据中提取，如"综合类""理工类"

3. **campuses**: 从详细地址中解析每个校区名称、地址、电话
   示例：仙林校区 南京市栖霞区仙林大道163号 (86)-25-89683186

4. **official_site / admission_site**: 从基础信息中提取

5. **contact_phone**: 从基础信息中提取官方电话

6. **tags**: 从基础信息"院校特性"和学校层次推断
   常见标签：985, 211, 双一流, C9联盟, 省重点, 综合类, 理工类, 师范类等

7. **major_categories**: 从 department_info "专业介绍入口及专业列表"中提取
   - 将散列的专业按学科门类归类（哲学类、经济学类、法学类、文学类、理学类、工学类、医学类等）
   - 每类下列举所有专业名称
   - 这是最重要的数据，不要遗漏任何专业

8. **departments**: 基于 major_categories 和学校实际情况推断院系名称和简介
   - 院系名参考：哲学系、法学院、文学院、数学系、物理学院、计算机学院等
   - 简介基于该领域的学科实力和特点
   - 最多8个院系

9. **admission_policies**: 从 admission_policy_clause 中提取关键条款
   - 保留条款编号（第X条）
   - 保留完整内容，不要缩写
   - 至少包含：学校性质条款、招生模式条款、录取规则条款
   - 最多6条

10. **admission_summary**: 基于所有招生章程条款总结关键招生政策

## 严格规则
- 所有信息必须来源于提供的 RAG 数据，不编造
- 如果数据缺失某字段，填写 null 或空数组
- 中文输出，专业严谨
- major_categories 中的专业列表要尽量完整
- campuses 从地址中完整解析"""


def _cache_key(school_name: str) -> str:
    return hashlib.sha256(f"school_detail_v2_{school_name}".encode()).hexdigest()[:16] + ".json"


def _cache_path(school_name: str) -> Path:
    return CACHE_DIR / _cache_key(school_name)


def _read_cache(school_name: str) -> dict[str, Any] | None:
    path = _cache_path(school_name)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        age = time.time() - data.get("_cached_at", 0)
        if age > 7 * 86400:
            return None
        data.pop("_cached_at", None)
        return data
    except Exception:
        return None


def _write_cache(school_name: str, data: dict[str, Any]) -> None:
    data["_cached_at"] = time.time()
    _cache_path(school_name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


_retriever: ChsiVectorRetriever | None = None
_client: AsyncOpenAI | None = None


def _get_retriever() -> ChsiVectorRetriever:
    global _retriever
    if _retriever is None:
        _retriever = ChsiVectorRetriever()
    return _retriever


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    return _client


async def generate_school_detail(school_name: str) -> dict[str, Any]:
    cached = _read_cache(school_name)
    if cached:
        cached["from_cache"] = True
        return cached

    retriever = _get_retriever()
    client = _get_client()

    # Query — increased top_k and broader scope
    rag_results = {}
    queries = {
        "school_profile": f"{school_name} 学校概况 办学层次 历史沿革 基本信息",
        "department_info": f"{school_name} 院系设置 学科建设 专业列表",
        "admission_policy_clause": f"{school_name} 招生章程 录取规则 招生政策",
    }

    for doc_type, query in queries.items():
        result = retriever.search(
            query, top_k=10, school_name=school_name, doc_type=doc_type
        )
        rag_results[doc_type] = pack_evidence(result, max_items=10)

    # Build prompt — much richer context
    context_sections = []
    for doc_type, evidence in rag_results.items():
        items = evidence.get("evidence") or []
        if not items:
            continue
        context_sections.append(f"\n## {doc_type}\n")
        for item in items[:8]:  # up to 8 items per doc type
            content = item.get("content", "")
            context_sections.append(
                f"**[{item.get('title', '')}]**\n{content[:3000]}\n"
            )

    if not context_sections:
        return {
            "school_name": school_name,
            "overview": "暂无该院校的详细数据",
            "basic_info": None,
            "campuses": [],
            "official_site": "",
            "admission_site": "",
            "contact_phone": "",
            "tags": [],
            "major_categories": [],
            "departments": [],
            "admission_policies": [],
            "admission_summary": "",
            "source": "数据来源：教育部阳光高考平台 (gaokao.chsi.com.cn)",
            "generated_at": None,
            "from_cache": False,
            "error": "no_rag_data",
        }

    user_prompt = f"""请根据以下 CHSI RAG 检索结果生成「{school_name}」的详细介绍。

检索数据：
{"".join(context_sections)}

请严格按 JSON 格式输出，内容要尽可能丰富详实。"""

    try:
        response = await client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=8192,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        result = json.loads(content)
        result["from_cache"] = False
        result["generated_at"] = result.get("generated_at") or time.strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        _write_cache(school_name, result)
        return result

    except json.JSONDecodeError:
        logger.error(f"DeepSeek invalid JSON for {school_name}")
        return {
            "school_name": school_name,
            "overview": "AI生成失败，请稍后重试",
            "basic_info": None,
            "campuses": [],
            "official_site": "", "admission_site": "", "contact_phone": "",
            "tags": [],
            "major_categories": [], "departments": [],
            "admission_policies": [], "admission_summary": "",
            "source": "数据来源：教育部阳光高考平台 (gaokao.chsi.com.cn)",
            "generated_at": None, "from_cache": False,
            "error": "ai_generation_failed",
        }
    except Exception as e:
        logger.error(f"DeepSeek API error for {school_name}: {e}")
        return {
            "school_name": school_name,
            "overview": f"生成失败: {str(e)[:100]}",
            "basic_info": None,
            "campuses": [],
            "official_site": "", "admission_site": "", "contact_phone": "",
            "tags": [],
            "major_categories": [], "departments": [],
            "admission_policies": [], "admission_summary": "",
            "source": "数据来源：教育部阳光高考平台 (gaokao.chsi.com.cn)",
            "generated_at": None, "from_cache": False,
            "error": "api_error",
        }
