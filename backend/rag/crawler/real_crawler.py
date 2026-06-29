"""
择境 ZENPATH — Real Web Crawler for RAG Knowledge Base

Crawls official university websites for:
- 招生章程 (Admission Policies)
- 专业介绍 (Major Descriptions)  
- 就业质量报告 (Employment Reports)
- 学科建设 (Discipline Info)

Uses Google search to discover real content, then fetches and indexes.
"""

import asyncio
import hashlib
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag.chunker import chunk_document, clean_text
from rag.pipeline import index_chunks_sync

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; ZENPATH-RAG-Crawler/1.0; +https://zenpath.cn)"
REQUEST_TIMEOUT = 30
MIN_DELAY = 3  # seconds between requests
MAX_PAGES_PER_SCHOOL = 5

# Priority search queries for each doc type
SEARCH_QUERIES = {
    "admission_policy": [
        '{school} 招生章程 2025',
        '{school} 本科招生章程',
        '{school} 招生章程 site:edu.cn',
    ],
    "school_profile": [
        '{school} 学校简介',
        '{school} 学校概况 site:edu.cn',
    ],
    "major_profile": [
        '{school} 专业介绍 本科',
        '{school} 计算机科学与技术 专业介绍',
        '{school} 软件工程 专业介绍',
    ],
    "employment_report": [
        '{school} 就业质量报告 2024',
        '{school} 毕业生就业质量年度报告',
        '{school} 应届毕业生就业质量报告 site:edu.cn',
    ],
    "discipline_evaluation": [
        '{school} 一流本科专业',
        '{school} 学科建设 site:edu.cn',
        '{school} 重点学科',
    ],
}


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    parsed = urlparse(url)
    return parsed.netloc or parsed.path.split('/')[0]


def validate_source(url: str) -> tuple:
    """Validate source domain. Returns (source_name, source_type, confidence)."""
    domain = extract_domain(url).lower()
    
    if 'moe.gov.cn' in domain:
        return '教育部', 'official_moe', 'high'
    if 'chsi.com.cn' in domain or 'gaokao.chsi' in domain:
        return '阳光高考平台', 'official_exam_authority', 'high'
    # Only .edu.cn domains (or zsb.*.edu.cn) are official universities
    if '.edu.cn' in domain:
        if 'zsb.' in domain or 'zhaosheng' in domain:
            return domain, 'official_university', 'high'
        return domain, 'official_university', 'high'
    if 'gov.cn' in domain:
        return domain, 'official_exam_authority', 'high'
    return domain, 'third_party', 'low'


async def search_google(query: str, max_results: int = 5) -> list[str]:
    """Search Google and return result URLs."""
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            resp = await client.get(
                "https://www.google.com/search",
                params={"q": query, "num": max_results}
            )
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            urls = []
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if href.startswith('/url?q='):
                    url = href.split('/url?q=')[1].split('&')[0]
                    if url.startswith('http') and 'google.com' not in url:
                        urls.append(url)
            return urls[:max_results]
    except Exception as e:
        logger.warning(f"Search failed for '{query}': {e}")
        return []


async def search_bing(query: str, max_results: int = 5) -> list[str]:
    """Search Bing as an alternative."""
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            resp = await client.get(
                "https://www.bing.com/search",
                params={"q": query, "count": max_results}
            )
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            urls = []
            for cite in soup.find_all('cite'):
                text = cite.get_text().strip()
                if text.startswith('http'):
                    urls.append(text)
            return urls[:max_results]
    except Exception as e:
        logger.warning(f"Bing search failed: {e}")
        return []


async def fetch_page(url: str) -> dict:
    """Fetch and parse a web page."""
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            
            content_type = resp.headers.get('content-type', '')
            if 'pdf' in content_type:
                return {'success': True, 'url': str(resp.url), 'html': '',
                       'content_type': content_type, 'status': resp.status_code}
            
            # Parse HTML
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Get title
            title = ''
            if soup.title:
                title = soup.title.get_text().strip()
            
            # Remove noise
            for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
            
            text = soup.get_text(separator='\n')
            text = clean_raw_text(text)
            
            return {
                'success': True,
                'url': str(resp.url),
                'title': title,
                'html': text,
                'content_type': content_type,
                'status': resp.status_code,
            }
    except Exception as e:
        return {'success': False, 'url': url, 'error': str(e)}


def clean_raw_text(text: str) -> str:
    """Aggressive cleaning of raw scraped text."""
    # Remove boilerplate
    text = re.sub(r'版权所有[^\n]*', '', text)
    text = re.sub(r'Copyright[^\n]*', '', text)
    text = re.sub(r'ICP[备证].*?\n', '\n', text)
    text = re.sub(r'地址[：:][^\n]*', '', text)
    text = re.sub(r'电话[：:][^\n]*', '', text)
    text = re.sub(r'邮箱[：:][^\n]*', '', text)
    text = re.sub(r'邮编[：:][^\n]*', '', text)
    text = re.sub(r'分享到[^\n]*', '', text)
    text = re.sub(r'关注[^\n]*', '', text)
    text = re.sub(r'设为首页.*?\n', '\n', text)
    text = re.sub(r'加入收藏.*?\n', '\n', text)
    text = re.sub(r'首页.*?关于我们.*?\n', '\n', text)
    text = re.sub(r'友情链接.*?\n', '\n', text)
    text = re.sub(r'网站地图.*?\n', '\n', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {3,}', ' ', text)
    
    # Remove navigation-like short lines
    lines = text.split('\n')
    filtered = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            filtered.append('')
            continue
        # Skip very short navigation lines
        if len(stripped) < 10 and any(kw in stripped for kw in ['首页', '返回', '跳转', '导航', '导航栏', '分享']):
            continue
        filtered.append(line)
    
    return '\n'.join(filtered).strip()


def detect_doc_type(url: str, title: str) -> str:
    """Heuristic doc type detection."""
    combined = (url + ' ' + title).lower()
    
    if any(kw in combined for kw in ['招生章程', '录取规则', '录取办法']):
        return 'admission_policy'
    if any(kw in combined for kw in ['就业质量', '就业报告', '毕业生就业', '就业率', '毕业去向']):
        return 'employment_report'
    if any(kw in combined for kw in ['专业介绍', '专业简介', '培养方案', '培养目标', '主干课程']):
        return 'major_profile'
    if any(kw in combined for kw in ['学科建设', '重点学科', '一流专业', '学科评估', '学科介绍']):
        return 'discipline_evaluation'
    if any(kw in combined for kw in ['学校简介', '学校概况', '大学简介', '学院简介', '学校介绍']):
        return 'school_profile'
    
    return 'general'


async def crawl_school(school: dict, max_pages: int = 5) -> dict:
    """
    Crawl a single school: search → fetch → parse → chunk → index.
    Returns stats dict.
    """
    name = school['school_name']
    province = school.get('province', '')
    city = school.get('city', '')
    
    logger.info(f"🕷️ Crawling: {name}")
    
    all_chunks = []
    pages_fetched = 0
    chunks_created = 0
    
    for doc_type, queries in SEARCH_QUERIES.items():
        if pages_fetched >= max_pages:
            break
        
        for query_template in queries:
            if pages_fetched >= max_pages:
                break
            
            query = query_template.format(school=name)
            logger.info(f"  Searching: {query}")
            
            # Try Google, fallback to Bing
            urls = await search_google(query, max_results=3)
            if not urls:
                urls = await search_bing(query, max_results=3)
            
            for url in urls[:2]:  # Max 2 URLs per query
                if pages_fetched >= max_pages:
                    break
                
                # Validate source
                source_name_domain, source_type_detected, confidence = validate_source(url)
                
                # Rate limit
                await asyncio.sleep(MIN_DELAY)
                
                # Fetch
                result = await fetch_page(url)
                if not result['success']:
                    continue
                
                pages_fetched += 1
                text = result.get('html', '')
                if not text or len(text) < 200:
                    continue
                
                # Detect doc type from URL/title
                detected_type = detect_doc_type(url, result.get('title', ''))
                if detected_type == 'general':
                    detected_type = doc_type  # Use search intent
                
                # Chunk
                chunks = chunk_document(
                    text=text,
                    doc_type=detected_type,
                    school_name=name,
                    city=city,
                    province=None,  # School-specific content, not province-specific
                    year=2025,
                    source_url=result['url'],
                    source_name=source_name_domain,
                    source_type=source_type_detected,
                    data_source=source_type_detected,
                    confidence=confidence,
                )
                
                all_chunks.extend(chunks)
                chunks_created += len(chunks)
                logger.info(f"  ✅ {result['url'][:80]} → {len(chunks)} chunks ({detected_type})")
    
    # Index all chunks
    if all_chunks:
        stats = index_chunks_sync(all_chunks)
        logger.info(f"  📊 {name}: {stats['inserted']} inserted, {stats['updated']} updated, {stats['skipped']} skipped")
        return {
            'school': name,
            'pages_fetched': pages_fetched,
            'chunks_created': chunks_created,
            **stats,
        }
    
    return {
        'school': name,
        'pages_fetched': pages_fetched,
        'chunks_created': 0,
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
    }


async def crawl_batch(schools: list[dict], max_per_school: int = 3) -> list[dict]:
    """Crawl multiple schools sequentially."""
    results = []
    for i, sch in enumerate(schools):
        print(f"\n[{i+1}/{len(schools)}] {sch['school_name']}")
        try:
            result = await crawl_school(sch, max_pages=max_per_school)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to crawl {sch['school_name']}: {e}")
            results.append({'school': sch['school_name'], 'error': str(e)})
        
        # Rate limit between schools
        if i < len(schools) - 1:
            await asyncio.sleep(MIN_DELAY)
    
    return results


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    import json
    
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    
    # Load priority list
    priority_file = Path(__file__).resolve().parent.parent.parent.parent / "rag_output" / "school_rag_priority_list.json"
    with open(priority_file, 'r', encoding='utf-8') as f:
        all_schools = json.load(f)
    
    # P0 schools only
    p0_schools = [s for s in all_schools if s['priority_tier'] == 'P0']
    
    # Take top N for demo (adjust based on time)
    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    target = p0_schools[:top_n]
    
    print(f"\n{'='*60}")
    print(f"  Real Web Crawler - 择境 RAG")
    print(f"  Target: {len(target)} P0 schools (top {top_n})")
    print(f"{'='*60}\n")
    
    results = asyncio.run(crawl_batch(target, max_per_school=3))
    
    # Summary
    total_inserted = sum(r.get('inserted', 0) for r in results)
    total_pages = sum(r.get('pages_fetched', 0) for r in results)
    total_chunks = sum(r.get('chunks_created', 0) for r in results)
    
    print(f"\n{'='*60}")
    print(f"  Crawl Complete")
    print(f"  Schools: {len(target)}")
    print(f"  Pages fetched: {total_pages}")
    print(f"  Chunks created: {total_chunks}")
    print(f"  Chunks inserted: {total_inserted}")
    print(f"{'='*60}")
    
    # Save crawl report
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'schools_crawled': len(target),
        'total_pages': total_pages,
        'total_chunks': total_chunks,
        'total_inserted': total_inserted,
        'results': results,
    }
    report_path = Path(__file__).resolve().parent.parent.parent.parent / "rag_output" / "crawl_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  Report saved to {report_path}")


if __name__ == "__main__":
    main()
