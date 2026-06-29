from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"
for path in (PROJECT_ROOT, BACKEND_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

try:
    from rag.evidence_packer import pack_evidence
    from rag.retrieval.chsi_vector_retriever import ChsiVectorRetriever
except ImportError:  # pragma: no cover
    from backend.rag.evidence_packer import pack_evidence
    from backend.rag.retrieval.chsi_vector_retriever import ChsiVectorRetriever


REPORT_DIR = PROJECT_ROOT / "rag_output" / "chsi" / "reports"
REPORT_MD = REPORT_DIR / "chsi_rag_evaluation_report.md"
REPORT_JSON = REPORT_DIR / "chsi_rag_evaluation_result.json"


CASES = [
    {"query": "南京大学学校简介", "expected_school": "南京大学", "allowed_doc_types": {"school_profile"}, "answerable": True},
    {"query": "北京大学招生章程", "expected_school": "北京大学", "allowed_doc_types": {"admission_policy", "admission_policy_clause"}, "answerable": True},
    {"query": "复旦大学招生章程", "expected_school": "复旦大学", "allowed_doc_types": {"admission_policy", "admission_policy_clause"}, "answerable": True},
    {"query": "计算机专业介绍", "expected_major": "计算机科学与技术", "allowed_doc_types": {"major_general_profile", "major_analysis"}, "answerable": True},
    {"query": "临床医学专业解读", "expected_major": "临床医学", "allowed_doc_types": {"major_analysis"}, "answerable": True},
    {"query": "人工智能专业学什么", "expected_major": "人工智能", "allowed_doc_types": {"major_general_profile", "major_analysis"}, "answerable": True},
    {"query": "法学专业介绍", "expected_major": "法学", "allowed_doc_types": {"major_general_profile", "major_analysis"}, "answerable": True},
    {"query": "厦门大学院系设置", "expected_school": "厦门大学", "allowed_doc_types": {"department_info"}, "answerable": True},
    {"query": "重庆大学招生章程", "expected_school": "重庆大学", "allowed_doc_types": {"admission_policy", "admission_policy_clause"}, "answerable": True},
    {"query": "某学校就业率是多少", "answerable": False, "missing_data": {"employment_report"}},
    {"query": "南京大学就业率是多少", "answerable": False, "missing_data": {"employment_report"}},
    {"query": "电子信息类专业学什么", "allowed_doc_types": {"major_general_profile", "major_analysis"}, "answerable": True},
    {"query": "口腔医学专业介绍", "expected_major": "口腔医学", "allowed_doc_types": {"major_general_profile", "major_analysis"}, "answerable": True},
    {"query": "武汉大学招生章程", "expected_school": "武汉大学", "allowed_doc_types": {"admission_policy", "admission_policy_clause"}, "answerable": True},
    {"query": "中国人民大学学校简介", "expected_school": "中国人民大学", "allowed_doc_types": {"school_profile"}, "answerable": True},
]


def evaluate_case(retriever: ChsiVectorRetriever, case: dict[str, Any], top_k: int) -> dict[str, Any]:
    search_result = retriever.search(case["query"], top_k=top_k)
    packed = pack_evidence(search_result, max_items=top_k)
    rows = packed.get("evidence") or []
    failures: list[str] = []

    if case.get("answerable") is False:
        expected_missing = set(case.get("missing_data") or [])
        actual_missing = set(packed.get("missing_data") or [])
        passed = (
            packed.get("answerable") is False
            and expected_missing.issubset(actual_missing)
            and packed.get("answer_mode") == "inferential_guidance"
            and packed.get("can_use_llm_inference") is True
        )
        if not passed:
            failures.append("expected inferential_guidance with missing_data=" + ",".join(sorted(expected_missing)))
        return _case_result(case, search_result, packed, passed, failures)

    passed = bool(rows) and packed.get("answerable") is True
    if not rows:
        failures.append("no evidence returned")
    if packed.get("answerable") is not True:
        failures.append("packed answerable is false")

    expected_school = case.get("expected_school")
    expected_major = case.get("expected_major")
    allowed_doc_types = set(case.get("allowed_doc_types") or [])
    for row in rows:
        if expected_school and row.get("school_name") != expected_school:
            passed = False
            failures.append(f"school mismatch: {row.get('school_name')} != {expected_school}")
        if expected_major and row.get("major_name") != expected_major:
            passed = False
            failures.append(f"major mismatch: {row.get('major_name')} != {expected_major}")
        if allowed_doc_types and row.get("doc_type") not in allowed_doc_types:
            passed = False
            failures.append(f"doc_type mismatch: {row.get('doc_type')} not in {sorted(allowed_doc_types)}")
        if not row.get("source_url"):
            passed = False
            failures.append(f"chunk {row.get('chunk_id')} missing source_url")
        if "就业率" in case["query"] and rows:
            passed = False
            failures.append("employment query returned evidence")

    return _case_result(case, search_result, packed, passed, failures)


def _case_result(case: dict[str, Any], search_result: dict[str, Any], packed: dict[str, Any], passed: bool, failures: list[str]) -> dict[str, Any]:
    compact_results = []
    for row in search_result.get("results", []):
        metadata = row.get("metadata") or {}
        compact_results.append(
            {
                "chunk_id": row.get("chunk_id"),
                "score": row.get("score"),
                "school_name": metadata.get("school_name"),
                "major_name": metadata.get("major_name"),
                "doc_type": metadata.get("doc_type"),
                "source_url": metadata.get("source_url"),
                "title": metadata.get("title"),
            }
        )
    return {
        "query": case["query"],
        "intent": search_result.get("intent"),
        "metadata_filter": search_result.get("filters"),
        "top_k_results": compact_results,
        "answerable": packed.get("answerable"),
        "answer_mode": packed.get("answer_mode"),
        "official_evidence_status": packed.get("official_evidence_status"),
        "can_use_llm_inference": packed.get("can_use_llm_inference"),
        "missing_data": packed.get("missing_data") or [],
        "expected_school": case.get("expected_school"),
        "expected_major": case.get("expected_major"),
        "allowed_doc_types": sorted(case.get("allowed_doc_types") or []),
        "has_source_url": all(row.get("source_url") for row in packed.get("evidence", [])),
        "passed": passed,
        "failure_reason": "; ".join(dict.fromkeys(failures)),
    }


def write_reports(results: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "total": len(results),
        "passed": sum(1 for row in results if row["passed"]),
        "failed": sum(1 for row in results if not row["passed"]),
        "failed_queries": [
            {"query": row["query"], "reason": row["failure_reason"]}
            for row in results
            if not row["passed"]
        ],
    }
    REPORT_JSON.write_text(json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# CHSI RAG Evaluation Report",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "| query | intent | answer_mode | metadata_filter | top chunk ids | passed | failure_reason |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in results:
        ids = [item["chunk_id"] for item in row["top_k_results"]]
        lines.append(
            f"| {row['query']} | {row['intent']} | {row.get('answer_mode') or ''} | "
            f"`{json.dumps(row['metadata_filter'], ensure_ascii=False)}` | "
            f"`{ids}` | {row['passed']} | {row['failure_reason'] or '无'} |"
        )
    lines.append("")
    lines.append("## Details")
    for row in results:
        lines.extend(
            [
                "",
                f"### {row['query']}",
                "",
                f"- intent: `{row['intent']}`",
                f"- answer_mode: `{row.get('answer_mode')}`",
                f"- official_evidence_status: `{row.get('official_evidence_status')}`",
                f"- can_use_llm_inference: `{row.get('can_use_llm_inference')}`",
                f"- missing_data: `{json.dumps(row.get('missing_data') or [], ensure_ascii=False)}`",
                f"- metadata_filter: `{json.dumps(row['metadata_filter'], ensure_ascii=False)}`",
                f"- passed: `{row['passed']}`",
                f"- failure_reason: {row['failure_reason'] or '无'}",
                "",
                "| chunk_id | school_name | major_name | doc_type | title | source_url |",
                "|---:|---|---|---|---|---|",
            ]
        )
        if row["top_k_results"]:
            for item in row["top_k_results"]:
                lines.append(
                    f"| {item['chunk_id']} | {item.get('school_name') or ''} | {item.get('major_name') or ''} | "
                    f"{item.get('doc_type') or ''} | {item.get('title') or ''} | {item.get('source_url') or ''} |"
                )
        else:
            lines.append("|  |  |  |  | 无可回答证据 |  |")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--vector-dir", type=Path)
    args = parser.parse_args()

    retriever = ChsiVectorRetriever(vector_dir=args.vector_dir) if args.vector_dir else ChsiVectorRetriever()
    results = [evaluate_case(retriever, case, args.top_k) for case in CASES]
    write_reports(results)
    summary = {
        "total": len(results),
        "passed": sum(1 for row in results if row["passed"]),
        "failed": sum(1 for row in results if not row["passed"]),
        "failed_queries": [
            {"query": row["query"], "reason": row["failure_reason"]}
            for row in results
            if not row["passed"]
        ],
        "report": str(REPORT_MD),
        "result_json": str(REPORT_JSON),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
