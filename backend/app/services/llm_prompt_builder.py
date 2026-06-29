"""
LLM Prompt Builder for ZENPATH AI Chat.

Assembles the system prompt with:
  - User context (province, score, rank, subjects, preferences)
  - Chat history summary
  - Structured recommendation data (if available)
  - RAG evidence
  - Answer boundaries and citation requirements
"""
from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """你是择境 ZENPATH 的 AI 志愿顾问，专为高考考生和家长提供志愿填报分析与建议。

## 核心原则

1. 结构化数据优先：分数、位次、冲稳保判断、录取机会评估必须基于结构化数据库，不得由 RAG 资料推断。
2. RAG 资料用于解释：学校简介、专业介绍、招生章程条款、官方来源引用由 CHSI 阳光高考平台资料提供。
3. 禁止编造：不能编造就业率、录取概率、招生计划人数、学科排名等无来源数据。
4. 资料不足时诚实说明：如果当前没有足够的官方资料支撑回答，必须明确告知用户，不要强行编造。
5. 不能承诺录取：任何情况下都不能说"保证录取"、"肯定能上"，只能给出基于历史数据的参考分析。
6. 引用来源：使用 CHSI 官方资料时，说明来源为"教育部阳光高考平台 (gaokao.chsi.com.cn)"。
7. 回答结构：直接结论 → 依据说明 → 风险点 → 下一步建议 → 引用来源。

## 回答风格

- 使用自然段落，不要用 ** 加粗、不要用 # 标题符号、不要用 - 列表符号、不要用 --- 分隔线。
- 用空行分段，每段说清一个要点。
- 关键数字和重要提醒可以在段内加「」括号标注。
- 面向考生和家长，语气亲切但不啰嗦。
- 不确定性要明确标注，用「注意：」「提醒：」开头。
- 结尾统一附一句简短声明，不要用分隔线。
"""


def build_chat_prompt(
    query: str,
    intent: str = "",
    user_context: dict[str, Any] | None = None,
    recommendation_context: dict[str, Any] | None = None,
    rag_evidence: list[dict[str, Any]] | None = None,
    answerable: bool = True,
    missing_data: list[str] | None = None,
    chat_history: list[dict[str, str]] | None = None,
    membership_tier: str = "free",
) -> list[dict[str, str]]:
    """Build the messages array for an LLM chat completion call.

    Returns a list of {"role": "system"|"user", "content": "..."} dicts.
    """
    system_parts = [SYSTEM_PROMPT]

    # ── User context ──
    if user_context:
        ctx_lines = ["\n## 用户背景\n"]
        if user_context.get("province"):
            ctx_lines.append(f"- 省份：{user_context['province']}")
        if user_context.get("subject_type"):
            ctx_lines.append(f"- 科类：{user_context['subject_type']}")
        if user_context.get("score"):
            ctx_lines.append(f"- 分数：{user_context['score']} 分")
        if user_context.get("rank"):
            ctx_lines.append(f"- 位次：{user_context['rank']}")
        subjs = user_context.get("selected_subjects") or []
        if subjs:
            ctx_lines.append(f"- 选科：{'、'.join(subjs)}")
        majors = user_context.get("preferred_majors") or []
        if majors:
            ctx_lines.append(f"- 专业偏好：{'、'.join(majors)}")
        cities = user_context.get("preferred_cities") or []
        if cities:
            ctx_lines.append(f"- 城市偏好：{'、'.join(cities)}")
        tiers = user_context.get("preferred_tiers") or []
        if tiers:
            ctx_lines.append(f"- 学校层次偏好：{'、'.join(tiers)}")
        system_parts.append("\n".join(ctx_lines))

    # ── Recommendation context ──
    if recommendation_context:
        rec_lines = ["\n## 当前志愿方案\n"]
        rec = recommendation_context
        if rec.get("school_name"):
            rec_lines.append(f"- 讨论学校：{rec['school_name']}")
        if rec.get("major_group_full_name"):
            rec_lines.append(f"- 讨论专业组：{rec['major_group_full_name']}")
        if rec.get("bucket"):
            rec_lines.append(f"- 推荐层级：{rec['bucket']}")
        if rec.get("rank_delta"):
            delta = rec["rank_delta"]
            direction = "高于" if delta > 0 else "低于"
            rec_lines.append(f"- 位次差：{direction}你 {abs(delta)} 位")
        system_parts.append("\n".join(rec_lines))

    # ── RAG evidence ──
    if rag_evidence:
        ev_lines = ["\n## CHSI 官方资料 (可用于回答)\n"]
        for i, ev in enumerate(rag_evidence[:8], 1):
            title = ev.get("title", "")
            content = ev.get("content", "")[:1000]
            source = ev.get("source_url", "")
            school = ev.get("school_name", "")
            dt = ev.get("doc_type", "")
            label = f"{school} - {dt}" if school else dt
            ev_lines.append(f"\n### [{i}] {title or label}")
            ev_lines.append(f"来源：{source}")
            ev_lines.append(content)
        if not answerable:
            ev_lines.append(
                "\n⚠️ 以上 CHSI 资料可能不足以完整回答用户问题，"
                "请结合你的通用知识补充，但必须区分哪些来自 CHSI、哪些来自你的知识。"
            )
        system_parts.append("\n".join(ev_lines))
    else:
        system_parts.append(
            "\n## 资料状态\n未检索到 CHSI 官方资料。请基于你的通用知识回答，"
            "但必须标注[以下回答基于通用知识，可能不包含最新官方数据]。"
            "如涉及具体录取数据、招生计划，请提示用户查阅官方渠道。"
        )

    # ── Membership limits ──
    if membership_tier == "free":
        system_parts.append(
            "\n## 限制\n当前为免费版，回答应简洁，不超过 500 字。"
            "深度分析（专业组风险、章程逐条解读）请在回答中提示升级。"
        )

    # ── Answer boundaries ──
    system_parts.append(
        "\n## 回答边界\n"
        "- 不能承诺录取。\n"
        "- 不能编造就业率、录取概率。\n"
        "- 不能编造招生计划变化。\n"
        "- 如果没有足够资料，明确指出。\n"
        "- 引用 CHSI 资料时注明来源。\n"
        "- 最终建议以省教育考试院和高校招生网为准。"
    )

    messages = [{"role": "system", "content": "\n".join(system_parts)}]

    # ── Chat history ──
    if chat_history:
        messages.extend(chat_history[-10:])  # Last 10 messages

    # ── User query ──
    messages.append({"role": "user", "content": query})

    return messages


def build_simple_answer(
    query: str,
    rag_evidence: list[dict[str, Any]] | None,
    intent: str,
    answerable: bool,
    missing_data: list[str] | None = None,
) -> str:
    """Build a simple answer when LLM is not available (mock mode)."""
    if not answerable:
        missing = "、".join(missing_data or ["相关资料"])
        return (
            f"当前 CHSI 官方库中没有可验证的{missing}，不能给出可靠回答。\n\n"
            "建议：查阅高校官方就业质量报告、省教育考试院公告或学校招生网获取准确信息。"
        )

    if not rag_evidence:
        return (
            "当前未检索到足够的 CHSI 官方资料来回答此问题。\n\n"
            "建议：直接访问高校官网招生栏目或教育部阳光高考平台 (gaokao.chsi.com.cn) 获取最新信息。"
        )

    parts = []
    for ev in rag_evidence[:5]:
        title = ev.get("title", "")
        content = ev.get("content", "")[:500]
        source = ev.get("source_url", "")
        if content:
            parts.append(f"{title}\n{content}\n\n来源：{source}")

    return (
        "根据教育部阳光高考平台 (CHSI) 官方资料：\n\n"
        + "\n\n".join(parts)
        + "\n\n以上信息来自 CHSI 官方数据，仅供参考。"
        "最终以高校招生网和省教育考试院公布为准。"
    )
