"""
Chunker — semantic text chunking for RAG documents.

v2 Rules (2026-06-16):
- Min chunk: 300 Chinese characters (up from 80)
- Target chunk: 600-1000 Chinese characters
- Max chunk: 1800 Chinese characters
- Overlap: 80-120 Chinese characters
- Merge short paragraphs instead of keeping 80-char fragments
- Quality check via quality.classify_chunk_quality()
- Navigation menus and link lists are stripped before chunking
"""
import re
import hashlib
from typing import Optional

# ─── Sizing constants ────────────────────────────────────────────────────────

MIN_CHINESE_CHARS = 300       # Minimum Chinese chars per chunk
TARGET_MIN = 600              # Target min size
TARGET_MAX = 1000             # Target max size
MAX_CHUNK_CHARS = 1800        # Hard max
OVERLAP_MIN = 80              # Overlap between consecutive chunks
OVERLAP_MAX = 120

# Section boundary patterns
SECTION_PATTERNS = [
    r'^(?:#+|第[一二三四五六七八九十]+[章节条]|[一二三四五六七八九十]+[、．.])',
    r'^(?:学校简介|学校概况|院系设置|学科建设|师资力量)',
    r'^(?:招生章程|招生简章|录取规则|专业调剂)',
    r'^(?:选科要求|身体条件|收费标准|转专业|退学|联系方式)',
    r'^(?:专业介绍|培养目标|核心课程|就业方向|考研方向|深造方向)',
    r'^(?:总体就业率|主要就业行业|主要就业城市|主要就业单位)',
    r'^(?:升学深造|薪资水平|毕业生规模|就业质量报告)',
    r'^(?:城市定位|主要产业|互联网|制造业|金融|高校资源|生活成本)',
    r'^(?:职业名称|对应专业|所需技能|典型行业|适合城市|成长路径)',
    r'^(?:一[、．.]|二[、．.]|三[、．.]|四[、．.]|五[、．.])',
    r'^(?:\([一二三四五]\)|（[一二三四五]）)',
]


def _chinese_char_count(text: str) -> int:
    return len(re.findall(r'[\u4e00-\u9fff]', text))


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences on Chinese/English sentence boundaries."""
    # Split on Chinese sentence endings + English periods
    sentences = re.split(r'(?<=[。！？；\n])\s*', text)
    return [s.strip() for s in sentences if s.strip()]


def chunk_document(
    text: str,
    doc_type: str,
    school_name: Optional[str] = None,
    major_name: Optional[str] = None,
    city: Optional[str] = None,
    province: Optional[str] = None,
    year: Optional[int] = None,
    source_url: Optional[str] = None,
    source_name: Optional[str] = None,
    source_type: str = 'official',
    data_source: str = 'official',
    confidence: str = 'high',
) -> list[dict]:
    """
    Split document into semantic chunks with full metadata.
    
    Strategy:
    1. Strip navigation/boilerplate
    2. Split into sections by headers
    3. Merge consecutive short paragraphs
    4. Split over-long sections at sentence boundaries
    5. Apply overlap for continuity
    """
    if not text or _chinese_char_count(text) < 50:
        return []

    # Strip navigation debris
    text = _strip_navigation(text)

    # Split into sections
    sections = _split_by_sections(text)

    chunks = []
    for section_title, section_text in sections:
        # Merge short paragraphs into cohesive blocks
        merged_blocks = _merge_paragraphs(section_text)

        for block in merged_blocks:
            cc = _chinese_char_count(block)
            if cc < MIN_CHINESE_CHARS:
                # Skip fragments that are too small
                # Exception: policy clauses with complete sentences
                if cc >= 100 and _looks_like_policy(block):
                    pass  # Keep short policy clauses
                else:
                    continue

            # If block exceeds target, split with overlap
            if cc > MAX_CHUNK_CHARS:
                sub_chunks = _split_long_block(block, section_title or doc_type)
                chunks.extend(sub_chunks)
            else:
                content_hash = hashlib.md5(block.encode()).hexdigest()[:12]
                chunk_id_parts = [doc_type, content_hash]
                if school_name:
                    safe_name = re.sub(r'[（(][^）)]*[）)]', '', school_name).strip()[:40]
                    chunk_id_parts.insert(0, safe_name)

                chunk = {
                    'chunk_id': '_'.join(chunk_id_parts),
                    'doc_type': doc_type,
                    'school_name': school_name,
                    'major_name': major_name,
                    'city': city,
                    'province': province,
                    'year': year,
                    'title': section_title or '',
                    'section': section_title or doc_type,
                    'content': block,
                    'source_url': source_url,
                    'source_name': source_name,
                    'source_type': source_type,
                    'data_source': data_source,
                    'confidence': confidence,
                    'content_hash': content_hash,
                }
                chunks.append(chunk)

    return chunks


def _strip_navigation(text: str) -> str:
    """Remove navigation menu lines from text before chunking."""
    lines = text.split('\n')
    nav_keywords = {
        '首页', '学校概况', '招生信息', '招生计划', '历年分数', '历年分数线',
        '报考指南', '招生问答', '联系我们', '政策导航', '更多', '通知公告',
        '快速链接', '友情链接', '返回首页', '当前位置', 'English',
        '组织机构', '教育教学', '科学研究', '招生就业', '国际合作',
        '校园文化', '网站地图', '版权信息', '信息公开',
        '招生简章', '招生政策', '录取查询', '成绩查询', '网上报名',
    }
    
    kept_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            kept_lines.append('')
            continue
        # Skip lines that are only navigation keywords
        if stripped in nav_keywords or len(stripped) < 5:
            continue
        # Skip lines like "招生信息 | 招生计划 | 历年分数"
        if re.match(r'^[\s|｜·\u00b7\u2022\-—]+$', stripped):
            continue
        if len(re.findall(r'[\u4e00-\u9fff]', stripped)) < 4 and len(stripped) < 20:
            continue
        kept_lines.append(line)
    
    return '\n'.join(kept_lines)


def _merge_paragraphs(text: str) -> list[str]:
    """
    Merge consecutive short paragraphs into cohesive blocks.
    Target: 600-1000 Chinese chars per block.
    """
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    if not paragraphs:
        return []

    merged = []
    current = ''
    current_cc = 0

    for para in paragraphs:
        para_cc = _chinese_char_count(para)

        if current_cc + para_cc <= TARGET_MAX:
            current += '\n' + para if current else para
            current_cc += para_cc
        else:
            # Current block is full, save it
            if current_cc >= MIN_CHINESE_CHARS:
                merged.append(current)
            elif current_cc >= 100:
                # Short but might be policy - keep with warning
                merged.append(current)
            # Start new block
            current = para
            current_cc = para_cc

    # Don't forget the last block
    if current:
        cc = _chinese_char_count(current)
        if cc >= MIN_CHINESE_CHARS or (cc >= 100 and _looks_like_policy(current)):
            merged.append(current)

    return merged


def _split_long_block(text: str, section: str = '') -> list[dict]:
    """
    Split an over-long block into sub-chunks with overlap.
    Keeps chunks under MAX_CHUNK_CHARS with ~100 char overlap.
    """
    sentences = _split_into_sentences(text)
    sub_chunks = []
    current = ''
    current_cc = 0

    for sent in sentences:
        sent_cc = _chinese_char_count(sent)
        
        if current_cc + sent_cc <= TARGET_MAX:
            current += sent
            current_cc += sent_cc
        else:
            if current_cc >= MIN_CHINESE_CHARS:
                sub_chunks.append(current)
            # Start new block with overlap: carry last 1-2 sentences
            carry_sents = _split_into_sentences(current)
            overlap_text = ''
            overlap_cc = 0
            for cs in reversed(carry_sents):
                cs_cc = _chinese_char_count(cs)
                if overlap_cc + cs_cc <= OVERLAP_MAX:
                    overlap_text = cs + overlap_text
                    overlap_cc += cs_cc
                else:
                    break
            current = overlap_text + sent if overlap_text else sent
            current_cc = _chinese_char_count(current)

    if current and _chinese_char_count(current) >= MIN_CHINESE_CHARS:
        sub_chunks.append(current)

    return sub_chunks


def _split_by_sections(text: str) -> list[tuple[str, str]]:
    """Split text by section headers."""
    section_pattern = re.compile('|'.join(SECTION_PATTERNS), re.MULTILINE)
    parts = section_pattern.split(text)
    sections = []

    for i in range(0, len(parts) - 1, 2):
        title = parts[i + 1] if i + 1 < len(parts) else ''
        content = parts[i + 2] if i + 2 < len(parts) else ''
        if content.strip():
            sections.append((title.strip(), content))

    if len(parts) == 1 and parts[0].strip():
        sections.append(('', parts[0]))

    return sections


def _looks_like_policy(text: str) -> bool:
    """Check if short text looks like a policy/admission clause."""
    policy_keywords = [
        '录取', '调档', '投档', '加分', '体检', '语种',
        '学费', '住宿费', '学制', '学位', '毕业', '授予',
        '志愿', '平行', '顺序', '批次', '控制线',
    ]
    return any(kw in text for kw in policy_keywords) and '。' in text
