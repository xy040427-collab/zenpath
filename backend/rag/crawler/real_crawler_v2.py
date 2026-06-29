"""
择境 ZENPATH — 真实官方来源 RAG 爬虫 (v2)

策略：
  1. 从 schools 表获取高校官网 URL
  2. 构造常见子路径直接访问(.edu.cn only)
  3. 提取正文、检测文档类型、语义切分、入库
  4. 不爬非 .edu.cn 站点，不依赖搜索引擎

Usage:
  python -m rag.crawler.real_crawler_v2 30    # 爬前30所P0
  python -m rag.crawler.real_crawler_v2 all   # 爬所有P0
"""

import asyncio
import hashlib
import json
import logging
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

# Resolve project root: find the directory containing "backend/gaokao.db"
_PROJECT_ROOT = Path(__file__).resolve()
while _PROJECT_ROOT.name:
    if (_PROJECT_ROOT / "backend" / "gaokao.db").exists():
        break
    _PROJECT_ROOT = _PROJECT_ROOT.parent
PROJECT_ROOT = _PROJECT_ROOT

sys.path.insert(0, str(PROJECT_ROOT / "backend"))
from rag.chunker import chunk_document, clean_text

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; ZENPATH-RAG-Crawler/2.0; +https://zenpath.cn)"
TIMEOUT = 30
DELAY = 3  # seconds between requests
MAX_PAGES_PER_SCHOOL = 8

# ─── University URL Construction ───────────────────────────────────────────

# Common sub-paths on Chinese university websites
SCHOOL_PROFILE_PATHS = [
    '/xxgk/xxjj.htm',      # 学校简介
    '/xxgk/xxjj/',          # 学校简介 (dir)
    '/xxgk/xxgk.htm',       # 信息公开
    '/xxgk/',               # 信息公开
    '/about/',              # 关于
    '/about/intro.htm',     # 简介
    '/',                    # 首页 (fallback)
]

ADMISSION_PATHS = [
    '/zsgz.htm',            # 招生章程
    '/zhaosheng/zsgz.htm',  # 招生/招生章程
    '/zhaosheng/zc.htm',    # 招生/章程
    '/zhaosheng/',          # 招生首页
    '/zsb/',                # 招生办
    '/zhaosheng/list.jsp',  # 招生公告列表
]

MAJOR_PATHS = [
    '/zhaosheng/zyjs.htm',  # 专业介绍
    '/zhaosheng/zy.htm',    # 专业
    '/zsb/zyjs/',           # 招生办/专业介绍
    '/jxjg/',               # 教学机构→院系列表
]

EMPLOYMENT_PATHS = [
    '/jyzd/',               # 就业指导
    '/jyzd/jyzlbg.htm',     # 就业质量报告
    '/jyzd/bysjyzlndbg.htm', # 毕业生就业质量年度报告
    '/jybgs/',              # 就业办公室
]

# ─── Database ───────────────────────────────────────────────────────────────

def get_db():
    import sqlite3
    conn = sqlite3.connect(str(PROJECT_ROOT / "backend" / "gaokao.db"))
    conn.row_factory = sqlite3.Row
    return conn


def get_p0_schools(limit: int = None) -> list[dict]:
    """Get P0 schools with website URLs."""
    conn = get_db()
    try:
        # Get P0 schools from priority list
        prio_file = PROJECT_ROOT / "rag_output" / "school_rag_priority_list.json"
        if prio_file.exists():
            with open(prio_file, 'r', encoding='utf-8') as f:
                all_schools = json.load(f)
            p0 = [s for s in all_schools if s['priority_tier'] == 'P0']
        else:
            rows = conn.execute("SELECT * FROM schools WHERE level IN ('985','211','双一流') ORDER BY ranking").fetchall()
            p0 = [dict(r) for r in rows]
        
        # Enrich with website URLs from schools table
        db_schools = {r['name']: dict(r) for r in conn.execute("SELECT * FROM schools").fetchall()}
        for s in p0:
            name = s.get('school_name', '')
            db_sch = db_schools.get(name, {})
            s['website'] = db_sch.get('website', '')
        
        return p0[:limit] if limit else p0
    finally:
        conn.close()


def get_existing_hashes() -> set:
    """Get all existing content hashes for dedup."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT content_hash FROM rag_chunks WHERE data_source != 'mock'"
        ).fetchall()
        return set(r[0] for r in rows if r[0])
    finally:
        conn.close()


def index_chunk_sync(chunks: list[dict]) -> dict:
    """Index chunks into rag_chunks."""
    conn = get_db()
    stats = {'inserted': 0, 'skipped': 0, 'updated': 0}
    now = datetime.utcnow().isoformat()
    existing_hashes = get_existing_hashes()
    
    try:
        for chunk in chunks:
            content = chunk.get('content', '')
            if not content or len(content.strip()) < 100:
                stats['skipped'] += 1
                continue
            
            content_hash = chunk.get('content_hash') or hashlib.md5(content.encode()).hexdigest()[:12]
            
            if content_hash in existing_hashes:
                stats['skipped'] += 1
                continue
            
            chunk_id = chunk.get('chunk_id', f"{chunk.get('school_name','')}_{chunk.get('doc_type','')}_{content_hash}")
            
            # Check existing
            existing = conn.execute(
                "SELECT id FROM rag_chunks WHERE chunk_id = ?", (chunk_id,)
            ).fetchone()
            
            if existing:
                stats['skipped'] += 1
                continue
            
            conn.execute("""
                INSERT INTO rag_chunks (
                    chunk_id, doc_type, school_name, major_name, city, province,
                    year, title, section, content,
                    source_url, source_name, source_type, data_source, confidence,
                    content_hash, crawled_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk_id, chunk.get('doc_type'), chunk.get('school_name'),
                chunk.get('major_name'), chunk.get('city'), chunk.get('province'),
                chunk.get('year', 2025), chunk.get('title', ''), chunk.get('section', ''),
                content,
                chunk.get('source_url'), chunk.get('source_name'),
                chunk.get('source_type', 'official_university'),
                chunk.get('data_source', 'official'),
                chunk.get('confidence', 'high'),
                content_hash, now, now, now
            ))
            existing_hashes.add(content_hash)
            stats['inserted'] += 1
        
        conn.commit()
    except Exception as e:
        logger.error(f"Index error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return stats


# ─── URL Discovery ──────────────────────────────────────────────────────────

def discover_urls(school: dict) -> list[dict]:
    """
    Construct likely URLs for a school's official content.
    Returns list of {url, doc_type, priority}.
    """
    name = school.get('school_name', '')
    website = school.get('website', '')
    
    urls = []
    base_domain = ''
    
    # 1. From schools table website field
    if website and website.startswith('http') and '.edu.cn' in website:
        base_domain = website.rstrip('/')
        urls.append({'url': website, 'doc_type': 'school_profile', 'priority': 1})
        # Try common sub-paths
        for path in SCHOOL_PROFILE_PATHS[1:]:
            urls.append({'url': urljoin(website, path), 'doc_type': 'school_profile', 'priority': 2})
    
    # 2. Construct from known patterns
    if not base_domain:
        # Common patterns: www.school.edu.cn, school.edu.cn
        # Try to construct from English name or slug
        slug = school.get('school_code', '')
        if slug:
            candidates = [
                f'https://www.{slug}.edu.cn',
                f'https://{slug}.edu.cn',
            ]
            for c in candidates:
                urls.append({'url': c, 'doc_type': 'school_profile', 'priority': 2})
                base_domain = base_domain or c
    
    # 3. Add sub-path URLs for each doc type
    if base_domain:
        # Admission paths
        for path in ADMISSION_PATHS:
            urls.append({'url': urljoin(base_domain, path), 'doc_type': 'admission_policy', 'priority': 2})
        
        # Major paths
        for path in MAJOR_PATHS:
            urls.append({'url': urljoin(base_domain, path), 'doc_type': 'major_profile', 'priority': 2})
        
        # Employment paths
        for path in EMPLOYMENT_PATHS:
            urls.append({'url': urljoin(base_domain, path), 'doc_type': 'employment_report', 'priority': 3})
    
    # Deduplicate by URL
    seen = set()
    unique = []
    for u in urls:
        if u['url'] not in seen:
            seen.add(u['url'])
            unique.append(u)
    
    return unique


# ─── Fetcher ────────────────────────────────────────────────────────────────

async def fetch_page(url: str) -> dict:
    """Fetch a page. Returns {success, url, final_url, title, text, content_type, status}."""
    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            follow_redirects=True,
            headers={'User-Agent': USER_AGENT},
        ) as client:
            resp = await client.get(url)
            
            content_type = resp.headers.get('content-type', '')
            final_url = str(resp.url)
            
            # Skip non-HTML
            if 'text/html' not in content_type and 'charset' not in content_type:
                return {'success': True, 'url': url, 'final_url': final_url,
                       'title': '', 'text': '', 'content_type': content_type,
                       'status': resp.status_code, 'is_html': False}
            
            # Parse HTML
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, 'html.parser')
            except:
                # Raw text fallback
                text = re.sub(r'<[^>]+>', '\n', resp.text)
                return {'success': True, 'url': url, 'final_url': final_url,
                       'title': '', 'text': text, 'content_type': content_type,
                       'status': resp.status_code, 'is_html': True}
            
            # Extract title
            title = soup.title.get_text().strip() if soup.title else ''
            
            # Remove noise
            for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            text = soup.get_text(separator='\n')
            text = clean_raw_text(text)
            
            return {
                'success': True,
                'url': url,
                'final_url': final_url,
                'title': title,
                'text': text,
                'content_type': content_type,
                'status': resp.status_code,
                'is_html': True,
            }
    except httpx.HTTPStatusError as e:
        return {'success': False, 'url': url, 'error': f'HTTP {e.response.status_code}',
                'status': e.response.status_code}
    except httpx.TimeoutException:
        return {'success': False, 'url': url, 'error': 'timeout', 'status': 0}
    except Exception as e:
        return {'success': False, 'url': url, 'error': str(e)[:100], 'status': 0}


def clean_raw_text(text: str) -> str:
    """Aggressive cleaning for scraped Chinese university pages."""
    # Remove boilerplate
    for pattern in [
        r'版权所有[^\n]*', r'Copyright[^\n]*', r'ICP[备证].*?\n',
        r'地址[：:][^\n]*', r'电话[：:][^\n]*', r'邮箱[：:][^\n]*',
        r'邮编[：:][^\n]*', r'传真[：:][^\n]*',
        r'分享到[^\n]*', r'设为首页.*?\n', r'加入收藏.*?\n',
        r'友情链接.*?\n', r'网站地图.*?\n', r'首页.*?上一页.*?\n',
    ]:
        text = re.sub(pattern, '', text)
    
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove short navigation lines
    lines = text.split('\n')
    filtered = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            filtered.append('')
            continue
        if len(stripped) < 15 and any(kw in stripped for kw in ['首页', '返回', '导航', '更多', '详情']):
            continue
        filtered.append(line)
    
    return '\n'.join(filtered).strip()


def detect_doc_type(url: str, title: str, text: str) -> str:
    """Detect doc type from URL, title, and content."""
    combined = (url + ' ' + title + ' ' + text[:500]).lower()
    
    if any(kw in combined for kw in ['招生章程', '录取规则', '录取办法']):
        return 'admission_policy'
    if any(kw in combined for kw in ['就业质量', '就业报告', '毕业生就业', '毕业去向']):
        return 'employment_report'
    if any(kw in combined for kw in ['专业介绍', '专业简介', '培养方案', '培养目标']):
        return 'major_profile'
    if any(kw in combined for kw in ['学科建设', '重点学科', '一流专业', '学科评估']):
        return 'discipline_evaluation'
    if any(kw in combined for kw in ['学校简介', '学校概况', '大学简介', '学院简介', 'xxgk', 'xxjj']):
        return 'school_profile'
    
    # Fallback: use URL path
    if '/zs' in url.lower() or 'zhaosheng' in url.lower():
        return 'admission_policy'
    if '/jy' in url.lower() or 'jiuye' in url.lower():
        return 'employment_report'
    if '/zy' in url.lower() or 'major' in url.lower():
        return 'major_profile'
    if '/xxgk' in url.lower() or '/about' in url.lower():
        return 'school_profile'
    
    return 'general'


def validate_content(text: str) -> bool:
    """Check if content is meaningful (not just navigation/boilerplate)."""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    return chinese_chars >= 150


def get_domain_name(url: str) -> str:
    """Extract domain for source naming."""
    parsed = urlparse(url)
    return parsed.netloc or 'unknown'


# ─── Main Crawler ───────────────────────────────────────────────────────────

async def crawl_school(school: dict, max_pages: int = 8) -> dict:
    """
    Crawl one school: construct URLs → fetch → parse → chunk → index.
    Returns detailed stats dict.
    """
    name = school.get('school_name', '')
    province = school.get('province', '')
    city = school.get('city', '')
    
    logger.info(f"🕷️ {name}")
    
    urls_to_try = discover_urls(school)
    logger.info(f"  URLs to try: {len(urls_to_try)}")
    
    report = {
        'school': name,
        'sources_attempted': 0,
        'sources_succeeded': 0,
        'sources_failed': 0,
        'chunks_created': 0,
        'chunks_indexed': 0,
        'sources': [],
        'errors': [],
    }
    
    all_chunks = []
    
    for url_info in urls_to_try:
        if report['sources_succeeded'] >= max_pages:
            break
        
        url = url_info['url']
        intended_doc_type = url_info['doc_type']
        
        report['sources_attempted'] += 1
        
        # Rate limit
        await asyncio.sleep(DELAY)
        
        # Fetch
        result = await fetch_page(url)
        
        if not result['success']:
            error = result.get('error', 'unknown')
            report['errors'].append({'url': url, 'error': error})
            report['sources_failed'] += 1
            # Only log non-404 errors
            if result.get('status') != 404:
                # Silently skip 404s (expected for most constructed URLs)
                pass
            continue
        
        if not result.get('is_html'):
            continue  # skip PDFs etc for now
        
        text = result.get('text', '')
        if not text or len(text.strip()) < 200:
            report['sources_failed'] += 1
            continue
        
        # Validate content quality
        if not validate_content(text):
            report['sources_failed'] += 1
            continue
        
        # Detect actual doc type
        actual_doc_type = detect_doc_type(
            url, result.get('title', ''), text
        )
        if actual_doc_type == 'general':
            actual_doc_type = intended_doc_type  # Use URL-intended type
        
        # Determine source info
        domain = get_domain_name(result['final_url'])
        source_type = 'official_university' if '.edu.cn' in domain.lower() else 'third_party'
        confidence = 'high' if source_type == 'official_university' else 'low'
        
        # Chunk
        chunks = chunk_document(
            text=text,
            doc_type=actual_doc_type,
            school_name=name,
            city=city,
            province=None,
            year=2025,
            source_url=result['final_url'],
            source_name=domain,
            source_type=source_type,
            data_source='official' if source_type == 'official_university' else 'third_party',
            confidence=confidence,
        )
        
        all_chunks.extend(chunks)
        report['sources_succeeded'] += 1
        report['sources'].append({
            'url': result['final_url'],
            'doc_type': actual_doc_type,
            'chunks': len(chunks),
            'source_type': source_type,
            'confidence': confidence,
        })
        
        logger.info(f"  ✅ {result['final_url'][:80]} → {len(chunks)} chunks [{actual_doc_type}]")
    
    # Index
    if all_chunks:
        stats = index_chunk_sync(all_chunks)
        report['chunks_created'] = len(all_chunks)
        report['chunks_indexed'] = stats['inserted']
    
    return report


async def crawl_batch(schools: list[dict], max_per_school: int = 8) -> list[dict]:
    """Crawl multiple schools sequentially."""
    results = []
    for i, sch in enumerate(schools):
        print(f"\n[{i+1}/{len(schools)}] {sch.get('school_name','')}")
        try:
            result = await crawl_school(sch, max_pages=max_per_school)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed: {sch.get('school_name','')}: {e}")
            results.append({'school': sch.get('school_name',''), 'error': str(e)})
        
        if i < len(schools) - 1:
            await asyncio.sleep(DELAY)
    
    return results


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    
    arg = sys.argv[1] if len(sys.argv) > 1 else '10'
    limit = None if arg == 'all' else int(arg)
    
    schools = get_p0_schools(limit)
    
    print(f"\n{'='*60}")
    print(f"  择境 ZENPATH — 真实官方 RAG 爬虫 v2")
    print(f"  目标: {len(schools)} 所P0高校")
    print(f"  策略: 直连 .edu.cn 官网 → 构造子路径 → 提取正文")
    print(f"{'='*60}\n")
    
    results = asyncio.run(crawl_batch(schools, max_per_school=8))
    
    # Summary
    total_sources_ok = sum(r.get('sources_succeeded', 0) for r in results)
    total_sources_fail = sum(r.get('sources_failed', 0) for r in results)
    total_chunks_indexed = sum(r.get('chunks_indexed', 0) for r in results)
    
    print(f"\n{'='*60}")
    print(f"  抓取完成")
    print(f"  学校: {len(schools)}")
    print(f"  成功访问: {total_sources_ok} 个页面")
    print(f"  失败: {total_sources_fail} 个URL")
    print(f"  入库 chunks: {total_chunks_indexed}")
    print(f"{'='*60}")
    
    # Save report
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'schools_targeted': len(schools),
        'total_sources_succeeded': total_sources_ok,
        'total_sources_failed': total_sources_fail,
        'total_chunks_indexed': total_chunks_indexed,
        'results': results,
    }
    
    report_path = PROJECT_ROOT / "rag_output" / "crawl_report_v2.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  报告: {report_path}")

if __name__ == "__main__":
    main()
