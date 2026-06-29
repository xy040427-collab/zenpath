"""
Web Crawler — fetches web pages and extracts clean text.

Sources (by priority):
1. 教育部官网 (moe.gov.cn)
2. 阳光高考平台 (gaokao.chsi.com.cn)
3. 各省教育考试院
4. 高校本科招生网
5. 高校官网
6. 高校就业质量报告
"""
import re
import logging
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# Source discovery: known URLs for key data types
KNOWN_SOURCES = {
    'gaokao_chsi': {
        'name': '阳光高考平台',
        'url': 'https://gaokao.chsi.com.cn',
        'source_type': 'official_exam_authority',
        'confidence': 'high',
    },
    'moe': {
        'name': '教育部',
        'url': 'https://www.moe.gov.cn',
        'source_type': 'official_moe',
        'confidence': 'high',
    },
}

# University official sites (partial list for bootstrap)
UNIVERSITY_SITES = {
    '南京大学': 'https://www.nju.edu.cn',
    '东南大学': 'https://www.seu.edu.cn',
    '南京航空航天大学': 'https://www.nuaa.edu.cn',
    '南京理工大学': 'https://www.njust.edu.cn',
    '南京邮电大学': 'https://www.njupt.edu.cn',
    '南京信息工程大学': 'https://www.nuist.edu.cn',
    '南京农业大学': 'https://www.njau.edu.cn',
    '南京医科大学': 'https://www.njmu.edu.cn',
    '南京中医药大学': 'https://www.njucm.edu.cn',
    '南京工业大学': 'https://www.njtech.edu.cn',
    '南京林业大学': 'https://www.njfu.edu.cn',
    '南京财经大学': 'https://www.nufe.edu.cn',
    '南京审计大学': 'https://www.nau.edu.cn',
}


async def fetch_page(url: str, timeout: int = 30) -> dict:
    """Fetch a web page and return raw HTML + metadata."""
    try:
        import httpx
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; ZENPATH RAG Crawler/1.0; +https://zenpath.cn)',
                'Accept': 'text/html,application/xhtml+xml',
            }
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return {
                'success': True,
                'url': str(resp.url),
                'status': resp.status_code,
                'content_type': resp.headers.get('content-type', ''),
                'html': resp.text,
            }
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return {'success': False, 'url': url, 'error': str(e)}


def extract_text_from_html(html: str) -> str:
    """Extract clean text from HTML, removing scripts, styles, nav, etc."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Remove non-content elements
        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            tag.decompose()

        # Remove common CSS classes for nav/ads
        for tag in soup.find_all(class_=re.compile(r'(nav|menu|sidebar|footer|ad|banner|toolbar)')):
            tag.decompose()

        text = soup.get_text(separator='\n')
        return text
    except ImportError:
        # Fallback: basic regex clean
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text


def detect_doc_type(url: str, title: str) -> str:
    """Heuristic doc type detection from URL and title."""
    url_lower = url.lower()
    title_lower = title.lower()

    if any(kw in url_lower + title_lower for kw in ['招生章程', '录取规则', 'admission']):
        return 'admission_policy'
    if any(kw in url_lower + title_lower for kw in ['就业', 'employment', '毕业去向']):
        return 'employment_report'
    if any(kw in url_lower + title_lower for kw in ['专业', 'major', '培养']):
        return 'major_profile'
    if any(kw in url_lower + title_lower for kw in ['城市', '产业', '经济']):
        return 'city_industry'
    if any(kw in url_lower + title_lower for kw in ['简介', 'about', '概况']):
        return 'school_profile'
    return 'general'


def validate_source(url: str) -> tuple[str, str, str]:
    """Validate source domain. Returns (source_name, source_type, confidence)."""
    domain = urlparse(url).netloc.lower()

    if 'moe.gov.cn' in domain:
        return '教育部', 'official_moe', 'high'
    if 'chsi.com.cn' in domain or 'gaokao.chsi' in domain:
        return '阳光高考平台', 'official_exam_authority', 'high'
    if any(d in domain for d in ['.edu.cn', 'zsb.']):
        # Try to extract university name from domain
        name = domain.split('.')[0].replace('-', ' ')
        return name, 'official_university', 'high'
    if 'gov.cn' in domain:
        return domain, 'official_exam_authority', 'high'

    return domain, 'third_party', 'low'
