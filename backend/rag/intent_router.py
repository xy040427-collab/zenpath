from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


MAJOR_ALIASES = {
    "计算机": "计算机科学与技术",
    "人工智能": "人工智能",
    "临床医学": "临床医学",
    "口腔医学": "口腔医学",
    "法学": "法学",
    "电子信息类": None,
    "电子信息": None,
}


@dataclass
class IntentResult:
    query: str
    intent: str
    filters: dict[str, Any]
    missing_data: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "intent": self.intent,
            "filters": self.filters,
            "missing_data": self.missing_data,
            "warnings": self.warnings,
        }


class ChsiIntentRouter:
    """Small deterministic router for CHSI official RAG metadata filters."""

    def __init__(self, school_names: list[str] | None = None, major_names: list[str] | None = None):
        self.school_names = sorted(set(school_names or []), key=len, reverse=True)
        self.major_names = sorted(set(major_names or []), key=len, reverse=True)

    def route(self, query: str, **explicit_filters: Any) -> IntentResult:
        query = (query or "").strip()
        school_name = explicit_filters.get("school_name") or self._find_name(query, self.school_names)
        major_name = explicit_filters.get("major_name") or self._find_name(query, self.major_names)
        warnings: list[str] = []
        missing_data: list[str] = []

        if major_name is None:
            for alias, canonical in MAJOR_ALIASES.items():
                if alias in query:
                    major_name = canonical
                    if canonical is None:
                        warnings.append(f"'{alias}' is a broad category/query term; using doc_type filter plus vector search.")
                    break

        if any(token in query for token in ["就业率", "就业质量", "就业报告", "毕业去向落实率"]):
            return IntentResult(
                query=query,
                intent="employment_query",
                filters={"doc_type": "employment_report"},
                missing_data=["employment_report"],
                warnings=["CHSI official seed library does not contain employment_report documents."],
            )

        if "院系" in query or "院系设置" in query or "学院设置" in query:
            filters = {"doc_type": "department_info", "scope": ["school", "admission"]}
            if school_name:
                filters["school_name"] = school_name
            return IntentResult(query, "department_info", filters | self._explicit_filter_overrides(explicit_filters), [], warnings)

        if "招生章程" in query or "章程" in query or "录取规则" in query or "专业调剂" in query:
            filters = {"doc_type": ["admission_policy", "admission_policy_clause"], "scope": ["school", "admission"]}
            if school_name:
                filters["school_name"] = school_name
            year = explicit_filters.get("year") or self._find_year(query)
            if year:
                filters["year"] = year
            return IntentResult(query, "admission_policy", filters | self._explicit_filter_overrides(explicit_filters), [], warnings)

        if "专业解读" in query or "报考指南" in query or "专业与就业" in query:
            filters = {"doc_type": "major_analysis", "scope": ["major", "global"]}
            if major_name:
                filters["major_name"] = major_name
            return IntentResult(query, "major_analysis", filters | self._explicit_filter_overrides(explicit_filters), [], warnings)

        if "专业" in query or "学什么" in query or "就业方向" in query or "课程" in query:
            filters = {"doc_type": ["major_general_profile", "major_analysis"], "scope": ["major", "global"]}
            if "开设" in query or "哪些学校" in query or "院校" in query:
                filters["doc_type"] = "major_school_distribution"
            if "就业方向" in query:
                filters["doc_type"] = "major_general_profile"
                filters["section"] = "就业方向"
            if major_name:
                filters["major_name"] = major_name
            return IntentResult(query, "major_profile", filters | self._explicit_filter_overrides(explicit_filters), [], warnings)

        if "学校简介" in query or "学校介绍" in query or "简介" in query or school_name:
            filters = {"doc_type": "school_profile", "scope": "school"}
            if school_name:
                filters["school_name"] = school_name
            return IntentResult(query, "school_profile", filters | self._explicit_filter_overrides(explicit_filters), [], warnings)

        return IntentResult(query, "unknown", self._explicit_filter_overrides(explicit_filters), [], ["No deterministic intent matched."])

    @staticmethod
    def _find_name(query: str, names: list[str]) -> str | None:
        for name in names:
            if name and name in query:
                return name
        return None

    @staticmethod
    def _find_year(query: str) -> int | None:
        match = re.search(r"(20[0-9]{2})", query)
        return int(match.group(1)) if match else None

    @staticmethod
    def _explicit_filter_overrides(explicit_filters: dict[str, Any]) -> dict[str, Any]:
        allowed = {"school_name", "major_name", "doc_type", "scope", "year", "source_type", "section"}
        return {key: value for key, value in explicit_filters.items() if key in allowed and value not in (None, "", [])}
