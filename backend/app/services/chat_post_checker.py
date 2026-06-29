"""
Post-generation safety checker for Chat answers.

Scans LLM output for forbidden claims and appends corrections if found.
"""
from __future__ import annotations

import re
from typing import Any

FORBIDDEN_PATTERNS = [
    (r"保证录取|肯定能上|100%录取|一定录取", "⚠️ 以上分析仅供参考，不构成录取承诺。最终以省教育考试院和高校实际录取为准。"),
    (r"就业率\s*\d+[%％]", "⚠️ 当前 CHSI 官方库中没有就业质量报告，上述就业率数据无法溯源验证。"),
    (r"录取概率\s*\d+[%％]", "⚠️ 录取概率为模型估算，非官方数据，仅供参考。"),
    (r"招生计划增加|扩招.*\d+人", "⚠️ 招生计划数据未经官方确认，请以省考试院招生计划表为准。"),
]

GENERAL_DISCLAIMER = (
    "\n\n以上分析仅供志愿填报参考，不构成录取承诺。"
    "最终录取结果以江苏省教育考试院和高校招生网官方公布为准。"
    "择境 ZENPATH 基于历年公开数据进行智能分析，无法替代官方信息。"
)


def check_answer(answer: str) -> dict[str, Any]:
    """Check an LLM-generated answer for forbidden content.

    Returns {answer, warnings[], modified: bool}
    """
    warnings = []
    modified = False

    for pattern, warning in FORBIDDEN_PATTERNS:
        if re.search(pattern, answer):
            warnings.append(warning)
            modified = True

    # Always append general disclaimer if not already present
    if "不构成录取承诺" not in answer and "仅供参考" not in answer[-200:]:
        answer += GENERAL_DISCLAIMER
        modified = True

    return {
        "answer": answer,
        "warnings": warnings,
        "modified": modified,
    }
