"""
Sources — source validation, confidence assignment, and dedup utilities.
"""
import hashlib
from typing import Optional

SOURCE_CONFIDENCE = {
    'official_exam_authority': 'high',      # 省教育考试院
    'official_moe': 'high',                  # 教育部
    'official_university': 'high',           # 高校招生网
    'official_employment_report': 'high',    # 就业质量报告
    'manual': 'medium',                      # 人工整理
    'third_party': 'low',                    # 第三方
    'mock': 'mock',                          # 仅测试
}

SOURCE_TYPE_PRIORITY = [
    'official_exam_authority',
    'official_moe',
    'official_university',
    'official_employment_report',
    'manual',
    'third_party',
    'mock',
]


def get_confidence(source_type: str) -> str:
    """Map source type to confidence level."""
    return SOURCE_CONFIDENCE.get(source_type, 'low')


def compute_content_hash(content: str) -> str:
    """MD5 hash for dedup."""
    return hashlib.md5(content.encode()).hexdigest()[:12]


def resolve_source_conflict(existing: dict, new: dict) -> dict:
    """When two sources conflict, pick the more authoritative one."""
    existing_type = existing.get('source_type', '')
    new_type = new.get('source_type', '')

    existing_pri = SOURCE_TYPE_PRIORITY.index(existing_type) if existing_type in SOURCE_TYPE_PRIORITY else 99
    new_pri = SOURCE_TYPE_PRIORITY.index(new_type) if new_type in SOURCE_TYPE_PRIORITY else 99

    if new_pri < existing_pri:
        return new  # new is more authoritative

    if new_pri == existing_pri:
        # Newer year wins
        if new.get('year', 0) > existing.get('year', 0):
            return new

    return existing  # keep existing


def validate_source_url(url: Optional[str]) -> bool:
    """Basic URL validation."""
    if not url:
        return False
    return url.startswith(('http://', 'https://'))


def build_chunk_id(doc_type: str, school_name: Optional[str], content_hash: str) -> str:
    """Build unique chunk ID."""
    parts = [doc_type, content_hash]
    if school_name:
        parts.insert(0, school_name)
    # Sanitize: remove special chars from school name
    if school_name:
        parts[0] = school_name.replace('（', '(').replace('）', '(').replace(' ', '_')[:40]
    return '_'.join(parts)
