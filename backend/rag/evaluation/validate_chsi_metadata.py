from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[3]
EXPORT_DIR = PROJECT_ROOT / "rag_output" / "chsi" / "export"
REPORT_DIR = PROJECT_ROOT / "rag_output" / "chsi" / "reports"

DEFAULT_DB = EXPORT_DIR / "zenpath_chsi_rag.sqlite"
DEFAULT_EMBEDDING = EXPORT_DIR / "rag_chunks_for_embedding_v2.jsonl"
DEFAULT_REPORT = REPORT_DIR / "chsi_metadata_validation_report.md"
DEFAULT_RESULT_JSON = REPORT_DIR / "chsi_metadata_validation_result.json"

ALLOWED_DOMAIN = "gaokao.chsi.com.cn"
ALLOWED_DOC_TYPES = {
    "school_profile",
    "department_info",
    "major_general_profile",
    "major_analysis",
    "major_school_distribution",
    "admission_policy",
    "admission_policy_clause",
    "invalid",
}
ALLOWED_SCOPES = {"school", "global", "major", "admission", "invalid"}
ALLOWED_QUALITY_STATUSES = {
    "valid",
    "pending",
    "too_short",
    "nav_menu",
    "link_list",
    "search_result",
    "login_page",
    "captcha_page",
    "duplicate",
    "low_quality",
    "year_missing",
    "metadata_incomplete",
    "invalid",
}
REQUIRED_COLUMNS = {
    "id",
    "content",
    "content_hash",
    "source_url",
    "source_domain",
    "source_type",
    "doc_type",
    "quality_status",
    "is_valid_for_rag",
    "scope",
    "school_name",
    "chsi_school_id",
    "normalized_school_name",
    "major_name",
    "major_code",
    "major_category",
    "discipline_category",
    "year",
    "title",
    "section",
    "chunk_index",
    "source_doc_id",
    "parent_url",
    "created_at",
    "crawled_at",
}

DRYRUN_CASES = [
    ("南京大学学校简介", "school_profile", "school_name=? AND doc_type='school_profile'", ("南京大学",), {"school_name": "南京大学", "doc_types": {"school_profile"}}),
    ("北京大学招生章程", "admission_policy", "school_name=? AND doc_type IN ('admission_policy','admission_policy_clause')", ("北京大学",), {"school_name": "北京大学", "doc_types": {"admission_policy", "admission_policy_clause"}}),
    ("复旦大学招生章程", "admission_policy", "school_name=? AND doc_type IN ('admission_policy','admission_policy_clause')", ("复旦大学",), {"school_name": "复旦大学", "doc_types": {"admission_policy", "admission_policy_clause"}}),
    ("计算机专业介绍", "major_general_profile", "major_name=? AND doc_type='major_general_profile' AND section IN ('专业介绍','核心课程')", ("计算机科学与技术",), {"major_name": "计算机科学与技术", "doc_types": {"major_general_profile"}}),
    ("临床医学专业解读", "major_analysis", "major_name=? AND doc_type='major_analysis'", ("临床医学",), {"major_name": "临床医学", "doc_types": {"major_analysis"}}),
    ("人工智能专业学什么", "major_general_profile", "major_name=? AND doc_type='major_general_profile' AND section IN ('专业介绍','核心课程')", ("人工智能",), {"major_name": "人工智能", "doc_types": {"major_general_profile"}}),
    ("法学专业就业方向", "major_general_profile", "major_name=? AND doc_type='major_general_profile' AND section='就业方向'", ("法学",), {"major_name": "法学", "doc_types": {"major_general_profile"}}),
    ("厦门大学院系设置", "department_info", "school_name=? AND doc_type='department_info'", ("厦门大学",), {"school_name": "厦门大学", "doc_types": {"department_info"}}),
    ("重庆大学招生章程", "admission_policy", "school_name=? AND doc_type IN ('admission_policy','admission_policy_clause')", ("重庆大学",), {"school_name": "重庆大学", "doc_types": {"admission_policy", "admission_policy_clause"}}),
    ("某学校就业率是多少", "employment_report", "doc_type='employment_report'", (), {"no_results_required": True}),
]


def normalize_name(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"\s+", "", value)
    return normalized or None


def one_line(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def truncate(value: str | None, limit: int = 300) -> str:
    text = one_line(value)
    return text if len(text) <= limit else text[:limit] + "..."


def placeholders(values: set[str]) -> str:
    return ",".join("?" for _ in values)


def scalar(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    return int(conn.execute(sql, params).fetchone()[0])


def rows(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = (), limit: int = 20) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql + f" LIMIT {limit}", params)]


def dict_counts(conn: sqlite3.Connection, sql: str) -> dict[str, int]:
    return {str(row[0]): int(row[1]) for row in conn.execute(sql)}


def add_finding(findings: list[dict[str, Any]], conn: sqlite3.Connection, rule: str, sql: str, params: tuple[Any, ...] = ()) -> None:
    sample = rows(conn, sql, params)
    if sample:
        findings.append({"severity": "P0", "rule": rule, "sample": sample})


def extract_school_id(url: str | None) -> str | None:
    if not url:
        return None
    for pattern in (r"schId-(\d+)", r"schId=(\d+)", r"/schinfo/(\d+)"):
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_spec_id(url: str | None) -> str | None:
    if not url:
        return None
    match = re.search(r"/(?:detail|kskcPage|kskc|specialityDetail)/([^/?#]+)", url)
    if match:
        return match.group(1)
    match = re.search(r"[?&]specId=([^&#]+)", url)
    if match:
        return match.group(1)
    return None


def sample_audits(conn: sqlite3.Connection) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    school_samples: list[dict[str, Any]] = []
    sql = """
        SELECT c.id, c.doc_type, c.school_name, c.chsi_school_id, c.normalized_school_name,
               c.title, c.source_url, c.content, s.school_name AS expected_school_name
        FROM rag_chunks c
        LEFT JOIN schools s ON c.chsi_school_id=s.chsi_school_id
        WHERE c.quality_status='valid'
          AND c.is_valid_for_rag=1
          AND c.scope='school'
        ORDER BY ((c.id * 1103515245 + 12345) & 2147483647)
        LIMIT 50
    """
    for row in conn.execute(sql):
        expected_name = row["expected_school_name"] or row["school_name"]
        consistent = normalize_name(expected_name) == normalize_name(row["school_name"])
        school_samples.append(
            {
                "chunk_id": row["id"],
                "doc_type": row["doc_type"],
                "school_name": row["school_name"],
                "chsi_school_id": row["chsi_school_id"],
                "normalized_school_name": row["normalized_school_name"],
                "title": row["title"],
                "source_url": row["source_url"],
                "content_300": truncate(row["content"], 300),
                "consistent": consistent,
                "reason": "chsi_school_id maps to same school_name" if consistent else "school id/name mismatch",
            }
        )

    major_samples: list[dict[str, Any]] = []
    sql = """
        SELECT c.id, c.doc_type, c.major_name, c.major_code, c.major_category, c.discipline_category,
               c.title, c.source_url, c.content, m.major_name AS expected_major_name
        FROM rag_chunks c
        LEFT JOIN major_catalog m ON c.major_code=m.major_code
        WHERE c.quality_status='valid'
          AND c.is_valid_for_rag=1
          AND c.scope IN ('major','global')
        ORDER BY ((c.id * 1103515245 + 12345) & 2147483647)
        LIMIT 50
    """
    for row in conn.execute(sql):
        expected_name = row["expected_major_name"] or row["major_name"]
        consistent = normalize_name(expected_name) == normalize_name(row["major_name"])
        major_samples.append(
            {
                "chunk_id": row["id"],
                "doc_type": row["doc_type"],
                "major_name": row["major_name"],
                "major_code": row["major_code"],
                "major_category": row["major_category"],
                "discipline_category": row["discipline_category"],
                "title": row["title"],
                "source_url": row["source_url"],
                "content_300": truncate(row["content"], 300),
                "consistent": consistent,
                "reason": "major_code maps to same major_name" if consistent else "major code/name mismatch",
            }
        )
    return school_samples, major_samples


def run_dryrun(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for query, intent, where_sql, params, expected in DRYRUN_CASES:
        result_rows = [
            dict(row)
            for row in conn.execute(
                "SELECT id, school_name, major_name, doc_type, source_url, title "
                "FROM rag_chunks WHERE quality_status='valid' AND is_valid_for_rag=1 AND "
                + where_sql
                + " ORDER BY id LIMIT 5",
                params,
            )
        ]
        failure_reasons: list[str] = []
        if expected.get("no_results_required"):
            passed = len(result_rows) == 0
            if not passed:
                failure_reasons.append("就业率问题没有 employment_report 时不应返回 chunk")
        else:
            passed = len(result_rows) > 0
            if not result_rows:
                failure_reasons.append("metadata filter 未返回结果")
            for row in result_rows:
                if expected.get("school_name") and row["school_name"] != expected["school_name"]:
                    passed = False
                    failure_reasons.append(f"返回了其他学校：{row['school_name']}")
                if expected.get("major_name") and row["major_name"] != expected["major_name"]:
                    passed = False
                    failure_reasons.append(f"返回了其他专业：{row['major_name']}")
                if row["doc_type"] not in expected["doc_types"]:
                    passed = False
                    failure_reasons.append(f"返回了错误 doc_type：{row['doc_type']}")
        results.append(
            {
                "query": query,
                "parsed_intent": intent,
                "metadata_filter": where_sql,
                "returned_chunk_ids": [row["id"] for row in result_rows],
                "rows": result_rows,
                "passed": passed,
                "failure_reason": "; ".join(dict.fromkeys(failure_reasons)) if failure_reasons else "",
            }
        )
    return results


def validate_embedding_jsonl(conn: sqlite3.Connection, embedding_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    valid_ids = {
        int(row[0])
        for row in conn.execute("SELECT id FROM rag_chunks WHERE quality_status='valid' AND is_valid_for_rag=1")
    }
    seen_ids: set[int] = set()
    bad_rows: list[dict[str, Any]] = []
    required_metadata = REQUIRED_COLUMNS - {"id", "content"}

    if not embedding_path.exists():
        return [{"severity": "P0", "rule": "embedding_v2_missing", "detail": str(embedding_path)}], {"embedding_lines": 0}

    with embedding_path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                bad_rows.append({"line": line_no, "error": str(exc)})
                continue
            chunk_id = payload.get("chunk_id")
            metadata = payload.get("metadata") or {}
            seen_ids.add(int(chunk_id)) if isinstance(chunk_id, int) else None
            row_errors: list[str] = []
            if not payload.get("content"):
                row_errors.append("missing content")
            if chunk_id not in valid_ids:
                row_errors.append("chunk_id not in DB valid chunk set")
            for field in required_metadata:
                if field not in metadata:
                    row_errors.append(f"missing metadata.{field}")
            if metadata.get("quality_status") != "valid" or int(metadata.get("is_valid_for_rag", 0)) != 1:
                row_errors.append("non-valid metadata included")
            if metadata.get("doc_type") not in ALLOWED_DOC_TYPES:
                row_errors.append("doc_type not allowed")
            if metadata.get("scope") not in ALLOWED_SCOPES:
                row_errors.append("scope not allowed")
            if metadata.get("source_domain") != ALLOWED_DOMAIN:
                row_errors.append("source_domain not official")
            if row_errors and len(bad_rows) < 20:
                bad_rows.append({"line": line_no, "chunk_id": chunk_id, "errors": row_errors})

    if bad_rows:
        findings.append({"severity": "P0", "rule": "embedding_v2_bad_rows", "sample": bad_rows[:20]})
    missing_ids = sorted(valid_ids - seen_ids)
    extra_ids = sorted(seen_ids - valid_ids)
    if missing_ids:
        findings.append({"severity": "P0", "rule": "embedding_v2_missing_valid_ids", "sample": missing_ids[:20], "count": len(missing_ids)})
    if extra_ids:
        findings.append({"severity": "P0", "rule": "embedding_v2_extra_invalid_ids", "sample": extra_ids[:20], "count": len(extra_ids)})

    stats = {
        "embedding_lines": len(seen_ids),
        "db_valid_chunks": len(valid_ids),
        "embedding_matches_valid": seen_ids == valid_ids,
    }
    return findings, stats


def validate(db_path: Path, embedding_path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    findings: list[dict[str, Any]] = []

    columns = {row["name"] for row in conn.execute("PRAGMA table_info(rag_chunks)")}
    missing_columns = sorted(REQUIRED_COLUMNS - columns)
    if missing_columns:
        findings.append({"severity": "P0", "rule": "missing_metadata_columns", "detail": missing_columns})
        # Continue so the report still contains as much context as possible.

    stats: dict[str, Any] = {
        "rag_chunks": scalar(conn, "SELECT COUNT(*) FROM rag_chunks"),
        "valid_chunks": scalar(conn, "SELECT COUNT(*) FROM rag_chunks WHERE quality_status='valid' AND is_valid_for_rag=1"),
        "invalid_chunks": scalar(conn, "SELECT COUNT(*) FROM rag_chunks WHERE NOT (quality_status='valid' AND is_valid_for_rag=1)"),
        "schools": scalar(conn, "SELECT COUNT(*) FROM schools"),
        "majors": scalar(conn, "SELECT COUNT(*) FROM major_catalog"),
        "admission_policies": scalar(conn, "SELECT COUNT(*) FROM admission_policies"),
        "doc_type_distribution": dict_counts(conn, "SELECT doc_type, COUNT(*) FROM rag_chunks GROUP BY doc_type"),
        "scope_distribution": dict_counts(conn, "SELECT scope, COUNT(*) FROM rag_chunks GROUP BY scope"),
        "quality_status_distribution": dict_counts(conn, "SELECT quality_status, COUNT(*) FROM rag_chunks GROUP BY quality_status"),
    }

    add_finding(
        findings,
        conn,
        "valid_missing_required_metadata",
        """
        SELECT id, title
        FROM rag_chunks
        WHERE quality_status='valid'
          AND is_valid_for_rag=1
          AND (
            source_url IS NULL OR trim(source_url)='' OR
            content_hash IS NULL OR trim(content_hash)='' OR
            doc_type IS NULL OR trim(doc_type)='' OR
            scope IS NULL OR trim(scope)='' OR
            source_type IS NULL OR trim(source_type)='' OR
            source_domain IS NULL OR trim(source_domain)='' OR
            source_doc_id IS NULL OR trim(source_doc_id)='' OR
            parent_url IS NULL OR trim(parent_url)='' OR
            section IS NULL OR trim(section)='' OR
            content IS NULL OR trim(content)=''
          )
        """,
    )
    add_finding(
        findings,
        conn,
        "school_valid_missing_school_name_or_id",
        """
        SELECT id, title, school_name, chsi_school_id
        FROM rag_chunks
        WHERE quality_status='valid'
          AND is_valid_for_rag=1
          AND scope='school'
          AND (school_name IS NULL OR trim(school_name)='' OR chsi_school_id IS NULL OR trim(chsi_school_id)='')
        """,
    )
    add_finding(
        findings,
        conn,
        "major_valid_missing_major_name_or_code",
        """
        SELECT id, title, major_name, major_code
        FROM rag_chunks
        WHERE quality_status='valid'
          AND is_valid_for_rag=1
          AND scope IN ('major','global')
          AND (
            (major_name IS NULL OR trim(major_name)='')
            AND (major_code IS NULL OR trim(major_code)='')
          )
        """,
    )
    add_finding(
        findings,
        conn,
        "major_valid_missing_catalog_metadata",
        """
        SELECT id, title, major_name, major_code, major_category, discipline_category
        FROM rag_chunks
        WHERE quality_status='valid'
          AND is_valid_for_rag=1
          AND scope IN ('major','global')
          AND (major_code IS NULL OR trim(major_code)='' OR major_category IS NULL OR trim(major_category)='' OR discipline_category IS NULL OR trim(discipline_category)='')
        """,
    )
    add_finding(
        findings,
        conn,
        "admission_valid_missing_school_or_year",
        """
        SELECT id, title, school_name, year
        FROM rag_chunks
        WHERE quality_status='valid'
          AND is_valid_for_rag=1
          AND doc_type IN ('admission_policy','admission_policy_clause')
          AND (school_name IS NULL OR trim(school_name)='' OR year IS NULL)
        """,
    )
    add_finding(
        findings,
        conn,
        "non_valid_marked_for_rag",
        "SELECT id, title, quality_status FROM rag_chunks WHERE quality_status!='valid' AND is_valid_for_rag=1",
    )
    add_finding(
        findings,
        conn,
        "doc_type_not_allowed",
        "SELECT id, title, doc_type FROM rag_chunks WHERE doc_type NOT IN (%s)" % placeholders(ALLOWED_DOC_TYPES),
        tuple(ALLOWED_DOC_TYPES),
    )
    add_finding(
        findings,
        conn,
        "scope_not_allowed",
        "SELECT id, title, scope FROM rag_chunks WHERE scope NOT IN (%s)" % placeholders(ALLOWED_SCOPES),
        tuple(ALLOWED_SCOPES),
    )
    add_finding(
        findings,
        conn,
        "quality_status_not_allowed",
        "SELECT id, title, quality_status FROM rag_chunks WHERE quality_status NOT IN (%s)" % placeholders(ALLOWED_QUALITY_STATUSES),
        tuple(ALLOWED_QUALITY_STATUSES),
    )
    add_finding(
        findings,
        conn,
        "duplicate_content_hash",
        "SELECT content_hash, COUNT(*) AS n FROM rag_chunks GROUP BY content_hash HAVING COUNT(*) > 1",
    )
    add_finding(
        findings,
        conn,
        "source_url_not_chsi",
        """
        SELECT id, title, source_url
        FROM rag_chunks
        WHERE quality_status='valid'
          AND is_valid_for_rag=1
          AND source_url NOT LIKE 'https://gaokao.chsi.com.cn/%'
        """,
    )
    add_finding(
        findings,
        conn,
        "source_domain_not_chsi",
        """
        SELECT id, title, source_domain
        FROM rag_chunks
        WHERE quality_status='valid'
          AND is_valid_for_rag=1
          AND source_domain!='gaokao.chsi.com.cn'
        """,
    )
    add_finding(
        findings,
        conn,
        "school_id_name_mismatch",
        """
        SELECT c.id, c.title, c.school_name, c.chsi_school_id, s.school_name AS expected_school_name
        FROM rag_chunks c
        JOIN schools s ON c.chsi_school_id=s.chsi_school_id
        WHERE c.quality_status='valid'
          AND c.is_valid_for_rag=1
          AND c.scope='school'
          AND c.school_name!=s.school_name
        """,
    )
    add_finding(
        findings,
        conn,
        "major_code_name_mismatch",
        """
        SELECT c.id, c.title, c.major_name, c.major_code, m.major_name AS expected_major_name
        FROM rag_chunks c
        JOIN major_catalog m ON c.major_code=m.major_code
        WHERE c.quality_status='valid'
          AND c.is_valid_for_rag=1
          AND c.scope IN ('major','global')
          AND c.major_name!=m.major_name
        """,
    )

    # Python-side URL/id checks are easier than trying to regex in SQLite.
    school_url_mismatches = []
    for row in conn.execute(
        "SELECT id, title, source_url, chsi_school_id FROM rag_chunks WHERE quality_status='valid' AND is_valid_for_rag=1 AND scope='school'"
    ):
        source_school_id = extract_school_id(row["source_url"])
        if source_school_id and str(row["chsi_school_id"]) != source_school_id and len(school_url_mismatches) < 20:
            school_url_mismatches.append(dict(row) | {"source_url_school_id": source_school_id})
    if school_url_mismatches:
        findings.append({"severity": "P0", "rule": "school_source_url_id_mismatch", "sample": school_url_mismatches})

    major_url_mismatches = []
    for row in conn.execute(
        """
        SELECT c.id, c.title, c.source_url, c.major_name, c.major_code, m.spec_id, m.major_name AS expected_major_name
        FROM rag_chunks c
        LEFT JOIN major_catalog m ON c.major_code=m.major_code
        WHERE c.quality_status='valid'
          AND c.is_valid_for_rag=1
          AND c.scope IN ('major','global')
        """
    ):
        source_spec_id = extract_spec_id(row["source_url"])
        if source_spec_id and row["spec_id"] and str(row["spec_id"]) != source_spec_id and len(major_url_mismatches) < 20:
            major_url_mismatches.append(dict(row) | {"source_url_spec_id": source_spec_id})
    if major_url_mismatches:
        findings.append({"severity": "P0", "rule": "major_source_url_spec_id_mismatch", "sample": major_url_mismatches})

    year_mismatches = []
    for row in conn.execute(
        """
        SELECT id, title, source_url, content, year
        FROM rag_chunks
        WHERE quality_status='valid'
          AND is_valid_for_rag=1
          AND doc_type IN ('admission_policy','admission_policy_clause')
        """
    ):
        markers = re.findall(r"20[0-9]{2}", (row["title"] or "") + " " + (row["source_url"] or "") + " " + (row["content"] or "")[:500])
        if not markers:
            year_mismatches.append({"id": row["id"], "title": row["title"], "year": row["year"], "reason": "no year marker found"})
        elif str(row["year"]) not in markers:
            year_mismatches.append({"id": row["id"], "title": row["title"], "year": row["year"], "markers": markers[:5]})
        if len(year_mismatches) >= 20:
            break
    if year_mismatches:
        findings.append({"severity": "P0", "rule": "admission_year_not_supported_by_title_url_or_content", "sample": year_mismatches})

    embedding_findings, embedding_stats = validate_embedding_jsonl(conn, embedding_path)
    findings.extend(embedding_findings)
    stats.update(embedding_stats)

    dryrun_results = run_dryrun(conn)
    dryrun_failures = [item for item in dryrun_results if not item["passed"]]
    if dryrun_failures:
        findings.append({"severity": "P0", "rule": "metadata_retrieval_dryrun_failed", "sample": dryrun_failures})

    school_samples, major_samples = sample_audits(conn)
    stats["school_sample_count"] = len(school_samples)
    stats["major_sample_count"] = len(major_samples)
    stats["dryrun_passed"] = len(dryrun_failures) == 0
    stats["source_domains_valid"] = dict_counts(
        conn,
        "SELECT source_domain, COUNT(*) FROM rag_chunks WHERE quality_status='valid' AND is_valid_for_rag=1 GROUP BY source_domain",
    )
    conn.close()

    passed = not any(finding["severity"] == "P0" for finding in findings)
    return {
        "passed": passed,
        "findings": findings,
        "stats": stats,
        "school_sample_audit": school_samples,
        "major_sample_audit": major_samples,
        "dryrun": dryrun_results,
    }


def write_report(result: dict[str, Any], report_path: Path, result_json_path: Path, db_path: Path, embedding_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    result_json_path.parent.mkdir(parents=True, exist_ok=True)
    result_json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# CHSI Metadata Validation Report",
        "",
        f"- db: `{db_path}`",
        f"- embedding_v2: `{embedding_path}`",
        f"- passed: `{result['passed']}`",
        "",
        "## Stats",
        "",
        "```json",
        json.dumps(result["stats"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Findings",
        "",
        "```json",
        json.dumps(result["findings"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## School Sample Audit (50)",
        "",
        "| chunk_id | doc_type | school_name | chsi_school_id | title | source_url | content 前 300 字 | 判断 |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for row in result["school_sample_audit"]:
        lines.append(
            f"| {row['chunk_id']} | {row['doc_type']} | {row['school_name']} | {row['chsi_school_id']} | "
            f"{row['title']} | {row['source_url']} | {row['content_300']} | {row['consistent']}：{row['reason']} |"
        )

    lines.extend(
        [
            "",
            "## Major Sample Audit (50)",
            "",
            "| chunk_id | doc_type | major_name | major_code | major_category | discipline_category | title | source_url | content 前 300 字 | 判断 |",
            "|---:|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in result["major_sample_audit"]:
        lines.append(
            f"| {row['chunk_id']} | {row['doc_type']} | {row['major_name']} | {row['major_code']} | "
            f"{row['major_category'] or ''} | {row['discipline_category'] or ''} | {row['title']} | "
            f"{row['source_url']} | {row['content_300']} | {row['consistent']}：{row['reason']} |"
        )

    lines.extend(
        [
            "",
            "## Retrieval Dryrun",
            "",
            "| query | parsed_intent | metadata_filter | returned_chunk_ids | 是否通过 | 失败原因 |",
            "|---|---|---|---|---|---|",
        ]
    )
    for item in result["dryrun"]:
        lines.append(
            f"| {item['query']} | {item['parsed_intent']} | `{item['metadata_filter']}` | "
            f"`{item['returned_chunk_ids']}` | {item['passed']} | {item['failure_reason'] or '无'} |"
        )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--embedding-file", type=Path, default=DEFAULT_EMBEDDING)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--result-json", type=Path, default=DEFAULT_RESULT_JSON)
    args = parser.parse_args()

    result = validate(args.db, args.embedding_file)
    write_report(result, args.report, args.result_json, args.db, args.embedding_file)
    print(json.dumps({"passed": result["passed"], "findings": result["findings"], "stats": result["stats"]}, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
