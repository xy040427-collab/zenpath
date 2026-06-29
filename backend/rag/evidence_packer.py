from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
for path in (PROJECT_ROOT, BACKEND_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

try:
    from rag.retrieval.chsi_vector_retriever import ChsiVectorRetriever
except ImportError:  # pragma: no cover
    from backend.rag.retrieval.chsi_vector_retriever import ChsiVectorRetriever


UNSUPPORTED_INTENTS = {
    "employment_query": {
        "missing_data": ["employment_report"],
        "official_message": "当前 CHSI 官方库中没有就业质量报告，不能给出可引用的就业率数字。",
        "allowed_inference": [
            "可以明确说明以下内容是模型基于一般经验的推理，不是官方数据。",
            "可以从学校层次、学科实力、城市产业、专业方向、升学深造倾向等维度给判断框架。",
            "可以提示用户补充学校就业质量报告、学校就业网或官方毕业生就业质量年度报告。",
        ],
        "forbidden_claims": [
            "不得编造就业率、升学率、薪资、就业单位比例等具体数字。",
            "不得把模型推理写成 CHSI 官方结论。",
            "不得声称已经引用就业质量报告。",
        ],
    },
    "admission_plan": {
        "missing_data": ["admission_plan"],
        "official_message": "当前 CHSI 官方库中没有招生计划数据，不能可靠判断扩招或缩招。",
        "allowed_inference": [
            "可以说明招生计划需要以省考试院和学校招生网正式计划表为准。",
            "可以基于招生章程、办学层次、专业设置变化给风险提示。",
            "可以建议用户补充对应省份、年份、批次和专业组招生计划。",
        ],
        "forbidden_claims": [
            "不得编造计划人数、专业组人数或扩招缩招幅度。",
            "不得把招生章程推断成招生计划明细。",
        ],
    },
    "major_group_detail": {
        "missing_data": ["major_group_detail"],
        "official_message": "当前 CHSI 官方库中没有专业组内专业明细，不能声称某专业组一定包含某专业。",
        "allowed_inference": [
            "可以说明专业组明细需要以省考试院招生专业目录为准。",
            "可以按专业名称、选科要求、学校院系给一般性匹配建议。",
            "可以提醒用户核对年份、省份、批次、院校专业组代码。",
        ],
        "forbidden_claims": [
            "不得编造专业组代码、组内专业或选科要求。",
            "不得把通用专业介绍当成某省某年专业组明细。",
        ],
    },
}


def pack_evidence(search_result: dict[str, Any], max_items: int = 5) -> dict[str, Any]:
    intent = search_result.get("intent") or "unknown"
    query = search_result.get("query") or ""
    warnings = list(search_result.get("warnings") or [])
    missing_data = list(search_result.get("missing_data") or [])

    if intent in UNSUPPORTED_INTENTS:
        info = UNSUPPORTED_INTENTS[intent]
        return _inferential_guidance_response(
            query=query,
            intent=intent,
            missing_data=info["missing_data"],
            warnings=warnings,
            official_message=info["official_message"],
            allowed_inference=info["allowed_inference"],
            forbidden_claims=info["forbidden_claims"],
        )

    evidence = []
    for result in (search_result.get("results") or [])[:max_items]:
        metadata = result.get("metadata") or {}
        source_url = metadata.get("source_url")
        if not source_url:
            warnings.append(f"chunk {result.get('chunk_id')} missing source_url")
            continue
        evidence.append(
            {
                "chunk_id": result.get("chunk_id"),
                "score": result.get("score"),
                "title": metadata.get("title"),
                "source_url": source_url,
                "doc_type": metadata.get("doc_type"),
                "scope": metadata.get("scope"),
                "school_name": metadata.get("school_name"),
                "major_name": metadata.get("major_name"),
                "year": metadata.get("year"),
                "section": metadata.get("section"),
                "content": result.get("content"),
            }
        )

    if not evidence:
        if not missing_data:
            missing_data.append((search_result.get("filters") or {}).get("doc_type") or "matching_chsi_evidence")
        return _inferential_guidance_response(
            query=query,
            intent=intent,
            missing_data=missing_data,
            warnings=warnings,
            official_message="当前 CHSI 官方库中没有命中可引用证据，不能作为官方事实回答。",
            allowed_inference=[
                "可以明确标注为模型基于一般经验的推理或建议。",
                "可以解释缺少哪些官方材料，并提示用户补充来源。",
                "可以给出通用判断框架，但不能给出无来源的具体事实数字。",
            ],
            forbidden_claims=[
                "不得把无来源推理写成官方数据。",
                "不得编造具体分数、位次、人数、比例、年份或文件名称。",
            ],
        )

    return {
        "answerable": True,
        "answer_mode": "official_evidence",
        "official_evidence_status": "sufficient",
        "can_use_llm_inference": True,
        "query": query,
        "intent": intent,
        "evidence": evidence,
        "missing_data": missing_data,
        "warnings": warnings,
        "disclaimer": "以下回答可以基于 CHSI 官方证据生成；如加入模型推理，需要和官方事实分开表述。",
    }


def _inferential_guidance_response(
    *,
    query: str,
    intent: str,
    missing_data: list[str],
    warnings: list[str],
    official_message: str,
    allowed_inference: list[str],
    forbidden_claims: list[str],
) -> dict[str, Any]:
    return {
        "answerable": False,
        "answer_mode": "inferential_guidance",
        "official_evidence_status": "insufficient",
        "can_use_llm_inference": True,
        "query": query,
        "intent": intent,
        "evidence": [],
        "missing_data": missing_data,
        "warnings": warnings,
        "message": official_message,
        "disclaimer": "以下只能作为模型基于一般经验的推理或建议，不是 CHSI 官方数据，也不能替代官方文件。",
        "allowed_inference": allowed_inference,
        "forbidden_claims": forbidden_claims,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--vector-dir", type=Path)
    args = parser.parse_args()
    retriever = ChsiVectorRetriever(vector_dir=args.vector_dir) if args.vector_dir else ChsiVectorRetriever()
    result = retriever.search(args.query, top_k=args.top_k)
    print(json.dumps(pack_evidence(result, max_items=args.top_k), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
