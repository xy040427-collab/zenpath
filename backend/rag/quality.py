"""
RAG Quality Module — classify chunk quality, page type detection, navigation filtering.

Rules:
- Navigation menus, link lists, home pages → invalid for RAG
- Content pages with continuous paragraphs → valid
- Short fragments (<150 chars) → invalid (unless policy clause)
- Fixes the garbage chunk problem identified in audit.
"""
import re
from typing import Optional

# ─── Navigation keyword detection ───────────────────────────────────────────

NAV_KEYWORDS = [
    '首页', '学校概况', '招生信息', '招生计划', '历年分数', '历年分数线',
    '报考指南', '招生问答', '联系我们', '政策导航', '分省', '更多',
    '通知公告', '快速链接', '友情链接', '返回首页', '当前位置',
    '招生简章', '招生政策', '录取查询', '成绩查询', '网上报名',
    '校园风光', '校园地图', '学校邮箱', '公共服务', '信息公开',
    '新闻动态', '综合新闻', '学术动态', '媒体聚焦', '学校新闻',
    '组织机构', '师资队伍', '教育教学', '科学研究', '学科建设',
    '招生就业', '国际合作', '校园文化', '图书资料', '档案信息',
    'English', '网站地图', '版权信息', '法律声明', '隐私保护',
    '院长信箱', '书记信箱', '校长信箱', '学校标识', '校训校歌',
    '专题网站', '信息服务', '网络服务', 'VPN', 'OA系统',
]

LINK_LIST_PATTERNS = [
    # Professional/major name lists without description
    r'^(?:电子信息类|计算机类|机械类|土木类|化工与制药类|材料类)[^\n]{0,20}$',
    r'^(?:工科试验班|理科试验班|经济管理试验班|医学试验班)[^\n]{0,30}$',
    r'^(?:自动化|电气工程|软件工程|通信工程|信息安全)[^\n]{0,20}$',
]

# Known junk patterns that indicate navigation debris
NAV_LINE_PATTERN = re.compile(
    r'^[ \t]*(?:' + '|'.join(re.escape(kw) for kw in NAV_KEYWORDS) + r')[ \t]*$',
    re.MULTILINE
)

def _count_nav_keywords(text: str) -> int:
    """Count navigation keywords in text."""
    count = 0
    for kw in NAV_KEYWORDS:
        count += text.count(kw)
    return count

def _is_navigation_menu(text: str) -> bool:
    """Check if text is primarily a navigation menu (not content)."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) < 4:
        return False
    
    # Count short lines (<30 chars) vs long lines (>80 chars)
    short_lines = [l for l in lines if len(l) < 30]
    long_lines = [l for l in lines if len(l) > 80]
    
    nav_count = _count_nav_keywords(text)
    chinese_chars = _chinese_char_count(text)
    
    # MUST have complete sentences to not be nav
    has_complete_sentences = bool(re.search(r'[。！？]', text))
    sentence_count = len(re.findall(r'[。！？]', text))
    
    # If text has at least 3 complete sentences AND long content lines, it's probably real content
    if sentence_count >= 3 and len(long_lines) >= 2:
        return False
    
    # If text has at least 3 complete sentences and significant Chinese text (>200 chars), 
    # it's probably content with some nav debris, not pure nav
    if sentence_count >= 3 and chinese_chars > 200:
        return False
    
    # Single period in a sea of nav keywords = nav with stray sentence fragment
    if sentence_count <= 2 and nav_count >= 5:
        if len(short_lines) > len(long_lines) * 2:
            return True
    
    # Pure navigation: high nav keyword count + mostly short lines + no complete sentences
    if nav_count >= 6 and not has_complete_sentences:
        return True
    
    # Very short lines domination (>80% are short lines)
    if len(short_lines) / max(len(lines), 1) > 0.8 and nav_count >= 3:
        if not has_complete_sentences:
            return True
    
    # Extremely high nav keyword density without real content
    if nav_count >= 8 and chinese_chars < 400:
        if not has_complete_sentences or len(long_lines) == 0:
            return True
    
    return False

def _is_link_list(text: str) -> bool:
    """Check if text is a link list / major list without descriptions."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) < 2:
        return False
    
    # Check for list patterns: all lines are short and match list-like patterns
    short_lines = [l for l in lines if len(l) < 50]
    if len(short_lines) < len(lines) * 0.6:
        return False
    
    # Check if content looks like a list of majors/links
    list_indicators = 0
    for l in short_lines:
        if re.search(r'^(?:电子信息|计算机|机械|土木|化工|材料|自动化|电气|软件|通信|信息安全|物联网|大数据|人工智能|机器人|新能源|环境|生物|医学|药学|护理|法学|经济|管理|金融|会计|外语|新闻|艺术|设计|体育)', l):
            list_indicators += 1
        if re.search(r'(?:招生计划|历年分数|报考指南|招生问答|更多|查看详情)', l):
            list_indicators += 1
    
    if list_indicators >= len(short_lines) * 0.4:
        return True
    
    # Bare URL or link-like text
    if re.search(r'https?://', text) and len(text) < 200:
        return True
    
    return False

def _is_home_page(text: str, title: str = '') -> bool:
    """Check if content is from a homepage (not a content page)."""
    title_lower = title.lower()
    home_indicators = [
        '首页', '欢迎访问', '欢迎光临', '门户网站', '官方网站',
        'home', 'index', 'portal',
    ]
    for indicator in home_indicators:
        if indicator in title_lower or (indicator in text[:100] and len(text) > 200):
            pass  # Continue checking
    
    # If title is just school name + 官网/首页
    if re.search(r'(?:官网|首页|主页|门户)$', title) and _count_nav_keywords(text) >= 6:
        return True
    
    # High nav density + short text = homepage
    nav_count = _count_nav_keywords(text)
    if nav_count >= 6 and len(text) < 600:
        return True
    
    return False

def _is_empty_or_boilerplate(text: str) -> bool:
    """Check if text is copyright footer, contact info, or other boilerplate."""
    chinese_chars = _chinese_char_count(text)
    
    # Don't flag substantial content as boilerplate
    if chinese_chars > 300:
        return False
    
    boilerplate_patterns = [
        r'^版权所有\s*[©©]?\s*\d{4}', 
        r'^Copyright\s*[©©]?\s*\d{4}',
        r'^\s*(?:ICP|公安|公网安备|网站备案)\s*(?:备|号)',
        r'^\s*(?:建议使用|推荐使用|最佳分辨率|浏览器)',
        r'^\s*(?:总访问量|今日访问|您是第)',
    ]
    for pattern in boilerplate_patterns:
        if re.search(pattern, text, re.MULTILINE):
            # Only flag if the pattern dominates the text
            if chinese_chars < 200:
                return True
    
    # Pure contact info (address+phone+email with no real content)
    contact_lines = len(re.findall(r'(?:地址|电话|传真|邮箱|邮编)[：:]', text))
    if contact_lines >= 2 and chinese_chars < 200:
        sentence_count = len(re.findall(r'[。！？]', text))
        if sentence_count < 3:
            return True
    
    return False

def _chinese_char_count(text: str) -> int:
    """Count actual Chinese characters."""
    return len(re.findall(r'[\u4e00-\u9fff]', text))

# ─── Public API ─────────────────────────────────────────────────────────────

def classify_chunk_quality(
    content: str,
    title: str = '',
    source_url: str = '',
    doc_type: str = '',
) -> dict:
    """
    Classify chunk quality.
    
    Returns:
        {
            "quality": "valid" | "nav_menu" | "link_list" | "too_short" | 
                       "low_content" | "duplicate" | "invalid",
            "reason": str,
            "content_chars": int,
            "chinese_chars": int,
            "is_valid_for_rag": bool,
        }
    """
    content_chars = len(content)
    chinese_chars = _chinese_char_count(content)
    
    # Rule 1: Too short
    if chinese_chars < 20:
        return {
            'quality': 'too_short',
            'reason': f'Only {chinese_chars} Chinese chars',
            'content_chars': content_chars,
            'chinese_chars': chinese_chars,
            'is_valid_for_rag': False,
        }
    
    # Rule 2: Boilerplate
    if _is_empty_or_boilerplate(content):
        return {
            'quality': 'invalid',
            'reason': 'Copyright/contact boilerplate',
            'content_chars': content_chars,
            'chinese_chars': chinese_chars,
            'is_valid_for_rag': False,
        }
    
    # Rule 3: Navigation menu
    if _is_navigation_menu(content):
        return {
            'quality': 'nav_menu',
            'reason': 'Navigation menu detected',
            'content_chars': content_chars,
            'chinese_chars': chinese_chars,
            'is_valid_for_rag': False,
        }
    
    # Rule 4: Link list
    if _is_link_list(content):
        return {
            'quality': 'link_list',
            'reason': 'Link list / major list without description',
            'content_chars': content_chars,
            'chinese_chars': chinese_chars,
            'is_valid_for_rag': False,
        }
    
    # Rule 5: Home page
    if _is_home_page(content, title):
        return {
            'quality': 'nav_menu',
            'reason': 'Homepage / index page',
            'content_chars': content_chars,
            'chinese_chars': chinese_chars,
            'is_valid_for_rag': False,
        }
    
    # Rule 6: Too short for RAG (<150 Chinese chars, unless policy)
    if chinese_chars < 150:
        # Exception: policy clause with complete sentence
        has_complete_sentence = bool(re.search(r'[。！？]', content))
        is_policy = any(kw in content for kw in [
            '录取', '调档', '投档', '加分', '体检', '语种',
            '学费', '住宿费', '学制', '学位', '毕业',
        ])
        if is_policy and has_complete_sentence:
            return {
                'quality': 'valid',
                'reason': 'Short policy clause',
                'content_chars': content_chars,
                'chinese_chars': chinese_chars,
                'is_valid_for_rag': True,
            }
        return {
            'quality': 'too_short',
            'reason': f'Only {chinese_chars} Chinese chars (min 150)',
            'content_chars': content_chars,
            'chinese_chars': chinese_chars,
            'is_valid_for_rag': False,
        }
    
    # Rule 7: Low content — very few Chinese characters in total
    ratio = chinese_chars / max(content_chars, 1)
    if ratio < 0.15 and chinese_chars < 100:
        return {
            'quality': 'low_content',
            'reason': f'Low Chinese ratio ({ratio:.1%})',
            'content_chars': content_chars,
            'chinese_chars': chinese_chars,
            'is_valid_for_rag': False,
        }
    
    # Valid
    return {
        'quality': 'valid',
        'reason': 'Quality check passed',
        'content_chars': content_chars,
        'chinese_chars': chinese_chars,
        'is_valid_for_rag': True,
    }


def classify_page_type(html: str, url: str = '', title: str = '') -> str:
    """
    Classify a web page as content_page, list_page, home_page, pdf_page, or unknown.
    
    Used before chunking to decide whether to chunk or just extract links.
    """
    if not html or len(html) < 100:
        return 'unknown'
    
    # PDF
    if url.lower().endswith('.pdf') or 'application/pdf' in html[:500].lower():
        return 'pdf_page'
    
    # Count structural elements
    link_count = len(re.findall(r'<a\s[^>]*href=', html, re.IGNORECASE))
    p_count = len(re.findall(r'<p[\s>]', html, re.IGNORECASE))
    li_count = len(re.findall(r'<li[\s>]', html, re.IGNORECASE))
    
    # Extract visible text (basic)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    chinese_chars = _chinese_char_count(text)
    
    # Home page detection: high link density, low paragraph count
    if link_count > 30 and p_count < 8:
        # Check for home page indicators
        if any(kw in title for kw in ['首页', '官网', '门户', 'Home']):
            return 'home_page'
        if link_count > 50 and p_count < 5:
            return 'home_page'
    
    # List page detection
    if link_count > 15 and p_count < 10:
        list_indicators = [
            r'更多', r'通知公告', r'招生信息', r'新闻动态',
            r'分页', r'page', r'上一页', r'下一页',
            r'<ul\s', r'<ol\s',
        ]
        indicator_count = sum(1 for p in list_indicators if re.search(p, html, re.IGNORECASE))
        if indicator_count >= 2 or (link_count > 25 and p_count < 4):
            return 'list_page'
    
    # Content page: reasonable paragraph count + enough Chinese text
    if p_count >= 3 and chinese_chars > 500:
        return 'content_page'
    
    # Content indicators: article tags, publication date
    content_indicators = [
        r'<article', r'class="[^"]*content[^"]*"', r'class="[^"]*article[^"]*"',
        r'发布时间', r'发布日期', r'来源[：:]', r'作者[：:]',
        r'class="[^"]*detail[^"]*"', r'class="[^"]*news[^"]*"',
    ]
    if any(re.search(p, html, re.IGNORECASE) for p in content_indicators):
        if chinese_chars > 300:
            return 'content_page'
    
    # Default
    if chinese_chars > 200:
        return 'content_page'
    if link_count > 20:
        return 'list_page'
    return 'unknown'


# ─── HTML Body Extraction ──────────────────────────────────────────────────

CONTENT_CONTAINERS = [
    'article',
    'main',
    '#content',
    '.content',
    '.article',
    '.article-content',
    '.article_content',
    '.news-content',
    '.news_content',
    '.v_news_content',
    '.wp_articlecontent',
    '#vsb_content',
    '#vsb_content_2',
    '.TRS_Editor',
    '.detail',
    '.detail-content',
    '.post',
    '.post-content',
    '.entry-content',
    '#Article',
    '.text',
    '.main-text',
    '#BodyLabel',
    '.con',
    '.main_con',
]

STRIP_SELECTORS = [
    'script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'iframe',
    '.breadcrumb', '.menu', '.nav', '.navbar', '.footer', '.header',
    '.sidebar', '.left', '.right', '.links', '.pagination',
    '.share', '.toolbar', '.comment', '.related', '.recommend',
    '#footer', '#header', '#nav', '#sidebar',
]


def extract_body_html(html: str) -> str | None:
    """
    Extract the main content container from HTML.
    Uses BeautifulSoup (lazy import) for robust parsing.
    Returns cleaned HTML string or None if no content found.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None
    
    soup = BeautifulSoup(html, 'lxml' if _has_lxml() else 'html.parser')
    
    # Remove unwanted elements
    for selector in STRIP_SELECTORS:
        if selector.startswith('.') or selector.startswith('#'):
            for el in soup.select(selector):
                el.decompose()
        else:
            for el in soup.find_all(selector):
                el.decompose()
    
    # Try to find content container
    content = None
    for selector in CONTENT_CONTAINERS:
        if selector.startswith('.') or selector.startswith('#'):
            found = soup.select_one(selector)
        else:
            found = soup.find(selector)
        if found and len(found.get_text(strip=True)) > 100:
            content = found
            break
    
    # Fallback: use body
    if content is None:
        content = soup.find('body') or soup
    
    return str(content) if content else None


def extract_body_text(html: str) -> str:
    """
    Extract clean text from HTML, prioritizing content containers.
    Returns plain text with navigation/boilerplate stripped.
    """
    body_html = extract_body_html(html)
    if not body_html:
        # Fallback: regex strip tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(body_html, 'lxml' if _has_lxml() else 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    except ImportError:
        text = re.sub(r'<[^>]+>', '\n', body_html)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()


def _has_lxml() -> bool:
    try:
        import lxml
        return True
    except ImportError:
        return False
