"""
report_quality_guard.py — Pre-PDF quality check.

Scans report_json for:
- Raw field names (matched_majors, match_note, etc.)
- JSON strings ("province":, {"tier":, etc.)
- Debug/placeholder text (undefined, null, NaN, Test, debug)
- Raw numeric data (score 601, rank 12561 appearing as standalone text)

Runs before PDF generation. Returns (passed: bool, violations: list[str]).
"""

import json
import re
from typing import Tuple, List, Dict, Any

# Patterns that MUST NOT appear in the final report rendering
FORBIDDEN_RAW_FIELDS = [
    "matched_majors", "match_note", "no_data_warning",
    "high_risk_groups", "priority",
]

FORBIDDEN_PATTERNS = [
    # Raw JSON fragments
    (r'\{"province":', 'Raw JSON object fragment in report text'),
    (r'\{"tier":', 'Raw JSON object fragment in report text'),
    (r'"score":\s*\d+', 'Raw JSON key-value in report text'),
    (r'"rank":\s*\d+', 'Raw JSON key-value in report text'),

    # Debug/placeholder
    (r'\bundefined\b', 'JavaScript "undefined" in report text'),
    (r'\bnull\b', 'Literal "null" in report text'),
    (r'\bNaN\b', '"NaN" in report text'),
    (r'\bTest\b.*\bbutton\b', 'Test button text'),
    (r'Loading:false', 'Debug state in report text'),
    (r'\bdebug\b', 'Debug text in report'),
]

FORBIDDEN_STANDALONE_NUMBERS = [
    # Patterns like "score 601" or "rank 12561" appearing as standalone
    (r'(?<!\w)score\s+\d+(?!\w)', 'Raw "score N" in report text'),
    (r'(?<!\w)rank\s+\d+(?!\w)', 'Raw "rank N" in report text'),
]


def _flatten_text(obj: Any, depth: int = 0) -> str:
    """Extract all string values from nested JSON for scanning."""
    if depth > 20:
        return ""
    if isinstance(obj, str):
        return obj + " "
    if isinstance(obj, dict):
        return " ".join(_flatten_text(v, depth + 1) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(_flatten_text(item, depth + 1) for item in obj)
    return ""


def _check_field_names(obj: Any, path: str = "") -> List[str]:
    """Recursively check dict keys for forbidden raw field names."""
    violations = []
    if isinstance(obj, dict):
        for key in obj:
            current_path = f"{path}.{key}" if path else key
            if key in FORBIDDEN_RAW_FIELDS:
                violations.append(f"Forbidden field name '{key}' at {current_path}")
            violations.extend(_check_field_names(obj[key], current_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            violations.extend(_check_field_names(item, f"{path}[{i}]"))
    return violations


def validate_report_json(report_json: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate report_json before PDF generation.

    Returns:
        (passed, violations) — passed=True means no issues found.
    """
    violations: List[str] = []

    # 1. Check for forbidden field names in dict keys
    violations.extend(_check_field_names(report_json))

    # 2. Flatten all text values and check patterns
    all_text = _flatten_text(report_json)

    for pattern, description in FORBIDDEN_PATTERNS:
        if re.search(pattern, all_text, re.IGNORECASE):
            violations.append(f"Pattern violation: {description}")

    for pattern, description in FORBIDDEN_STANDALONE_NUMBERS:
        if re.search(pattern, all_text, re.IGNORECASE):
            violations.append(f"Pattern violation: {description}")

    # 3. Check for empty required sections (not an error, but warn)
    warnings = []
    ai_narratives = report_json.get("ai_narratives", {})
    if isinstance(ai_narratives, dict):
        for key in ("executive_summary", "final_advice"):
            if not ai_narratives.get(key):
                warnings.append(f"AI narrative '{key}' is empty")

    school_dives = report_json.get("school_deep_dives", [])
    if isinstance(school_dives, list):
        for i, sd in enumerate(school_dives):
            if isinstance(sd, dict):
                ai = sd.get("ai_analysis", {})
                if isinstance(ai, dict) and not ai.get("recommendation_conclusion"):
                    warnings.append(f"School deep dive #{i+1} ({sd.get('school_name','?')}) missing recommendation_conclusion")

    # Log warnings (not failures)
    for w in warnings:
        violations.append(f"WARNING: {w}")

    passed = not any(
        not v.startswith("WARNING:") for v in violations
    )

    return passed, violations


def guard_or_raise(report_json: Dict[str, Any], report_id: str = "") -> None:
    """Validate and raise ValueError if report has fatal quality issues."""
    passed, violations = validate_report_json(report_json)
    if not passed:
        fatal = [v for v in violations if not v.startswith("WARNING:")]
        msg = f"Report {report_id} quality check FAILED:\n" + "\n".join(f"  - {v}" for v in fatal)
        raise ValueError(msg)
