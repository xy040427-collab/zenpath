"""
择境 ZENPATH — RAG 爬虫 v3

策略：
  1. Google site:xxx.edu.cn 搜索发现真实 URL
  2. 直接 fetch 这些真实页面
  3. 检测文档类型、清洗、切分、入库
"""

import asyncio, hashlib, json, logging, re, sqlite3, sys, time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

# ─── Project root ───────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve()
while _PROJECT_ROOT.name:
    if (_PROJECT_ROOT / "backend" / "gaokao.db").exists():
        break
    _PROJECT_ROOT = _PROJECT_ROOT.parent
PROJECT_ROOT = _PROJECT_ROOT
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
from rag.chunker import chunk_document, clean_text

logger = logging.getLogger(__name__)
UA = "Mozilla/5.0 (compatible; ZENPATH-RAG/3.0; +https://zenpath.cn)"
TIMEOUT = 20
DELAY = 3

# ─── Database ───────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(str(PROJECT_ROOT / "backend" / "gaokao.db"))
    conn.row_factory = sqlite3.Row
    return conn

def get_p0_schools(limit=None):
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM schools WHERE level IN ('985','211','双一流') ORDER BY ranking").fetchall()
        schools = [dict(r) for r in rows]
        return schools[:limit] if limit else schools
    finally:
        conn.close()

def get_existing_hashes():
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT content_hash FROM rag_chunks WHERE data_source!='mock' AND source_type='official_university'").fetchall()
    conn.close()
    return set(r[0] for r in rows if r[0])

def index_chunks(chunks):
    conn = get_db()
    stats = {'inserted': 0, 'skipped': 0}
    now = datetime.utcnow().isoformat()
    hashes = get_existing_hashes()
    try:
        for c in chunks:
            content = c.get('content','')
            if len(content.strip()) < 100:
                stats['skipped'] += 1; continue
            ch = c.get('content_hash') or hashlib.md5(content.encode()).hexdigest()[:12]
            if ch in hashes:
                stats['skipped'] += 1; continue
            cid = c.get('chunk_id', f"{c.get('school_name','')}_{c.get('doc_type','')}_{ch}")
            if conn.execute("SELECT 1 FROM rag_chunks WHERE chunk_id=?",(cid,)).fetchone():
                stats['skipped'] += 1; continue
            conn.execute("""INSERT INTO rag_chunks(chunk_id,doc_type,school_name,major_name,city,province,year,title,section,content,source_url,source_name,source_type,data_source,confidence,content_hash,crawled_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                cid, c.get('doc_type'), c.get('school_name'), c.get('major_name'),
                c.get('city'), c.get('province'), c.get('year',2025),
                c.get('title',''), c.get('section',''), content,
                c.get('source_url'), c.get('source_name'), c.get('source_type','official_university'),
                c.get('data_source','official'), c.get('confidence','high'),
                ch, now, now, now))
            hashes.add(ch); stats['inserted'] += 1
        conn.commit()
    except Exception as e:
        logger.error(f"Index error: {e}"); conn.rollback()
    finally:
        conn.close()
    return stats


# ─── URL Discovery via Google site search ───────────────────────────────────

async def discover_urls(school_name: str, website: str) -> list[tuple[str, str]]:
    """
    Use Google site: search to find real content URLs.
    Returns list of (url, intended_doc_type).
    """
    domain = website.replace('https://','').replace('http://','').split('/')[0]
    
    searches = [
        (f'site:{domain} 招生章程', 'admission_policy'),
        (f'site:{domain} 招生章程 2025', 'admission_policy'),
        (f'site:{domain} 专业介绍', 'major_profile'),
        (f'site:{domain} 专业介绍 本科', 'major_profile'),
        (f'site:{domain} 计算机 专业 培养', 'major_profile'),
        (f'site:{domain} 就业质量报告', 'employment_report'),
        (f'site:{domain} 毕业生就业', 'employment_report'),
        (f'site:{domain} 学校简介', 'school_profile'),
        (f'site:{domain} 学校概况', 'school_profile'),
        (f'site:{domain} 一流本科专业', 'discipline_evaluation'),
        (f'site:{domain} 转专业', 'admission_policy'),
    ]
    
    all_urls = []
    async with httpx.AsyncClient(timeout=TIMEOUT, headers={'User-Agent': UA}) as client:
        for query, doc_type in searches:
            try:
                resp = await client.get('https://www.google.com/search', params={'q': query, 'num': 5})
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a'):
                    href = a.get('href', '')
                    if href.startswith('/url?q='):
                        url = href.split('/url?q=')[1].split('&')[0]
                        if url.startswith('http') and domain in url and 'google.com' not in url:
                            all_urls.append((url, doc_type))
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"  Search failed '{query[:30]}': {e}")
    
    # Deduplicate, keep up to 15 per school
    seen = set()
    unique = []
    for url, dt in all_urls:
        if url not in seen:
            seen.add(url)
            unique.append((url, dt))
    return unique[:15]


# ─── Fetch & Parse ──────────────────────────────────────────────────────────

async def fetch_and_parse(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={'User-Agent': UA}) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            content_type = resp.headers.get('content-type','')
            if 'pdf' in content_type:
                return {'ok':False, 'url':url, 'reason':'pdf'}
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.title.get_text().strip() if soup.title else ''
            for tag in soup.find_all(['script','style','nav','footer','header']):
                tag.decompose()
            text = soup.get_text(separator='\n')
            # Clean
            for pat in [r'版权所有[^\n]*', r'Copyright[^\n]*', r'ICP[备证].*?\n',
                        r'地址[：:][^\n]*', r'电话[：:][^\n]*', r'邮箱[：:][^\n]*',
                        r'邮编[：:][^\n]*', r'传真[：:][^\n]*', r'分享到[^\n]*',
                        r'设为首页.*?\n', r'加入收藏.*?\n', r'友情链接.*?\n']:
                text = re.sub(pat, '', text)
            text = re.sub(r'\n{3,}', '\n\n', text)
            chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
            return {'ok':True, 'url':str(resp.url), 'title':title, 'text':text.strip(),
                    'chinese_chars': chinese}
    except Exception as e:
        return {'ok':False, 'url':url, 'reason': str(e)[:80]}

def detect_type(url, title, text):
    combined = (url+' '+title+' '+text[:300]).lower()
    # Only exact employment report phrases — do NOT match bare '就业' or '/jy/'
    if any(kw in combined for kw in ['就业质量报告','毕业生就业质量报告','就业质量年度报告',
                                      '就业质量报告.pdf']): return 'employment_report'
    if any(kw in combined for kw in ['招生章程','录取规则','录取办法']): return 'admission_policy'
    if any(kw in combined for kw in ['专业介绍','培养方案','培养目标','主干课程','核心课程']): return 'major_profile'
    if any(kw in combined for kw in ['学科建设','重点学科','一流专业','学科评估','双一流']): return 'discipline_evaluation'
    if any(kw in combined for kw in ['学校简介','学校概况','学院简介','大学简介','学校介绍']): return 'school_profile'
    if '/zs' in url.lower() or 'zhaosheng' in url.lower(): return 'admission_policy'
    if '/zy' in url.lower(): return 'major_profile'
    if '/xxgk' in url.lower() or '/about' in url.lower(): return 'school_profile'
    return 'general'


# ─── Main crawl ─────────────────────────────────────────────────────────────

async def crawl_school(school, max_fetch=15):
    name = school['name']
    website = school.get('website','')
    if not website or '.edu.cn' not in website:
        return {'school': name, 'urls_found': 0, 'fetched': 0, 'indexed': 0, 'sources': [], 'error': 'no .edu.cn website'}
    
    logger.info(f"🕷️ {name} ({website})")
    
    # Discover URLs
    urls = await discover_urls(name, website)
    logger.info(f"  Found {len(urls)} URLs")
    
    if not urls:
        return {'school': name, 'urls_found': 0, 'fetched': 0, 'indexed': 0, 'sources': []}
    
    # Fetch each
    all_chunks = []
    sources = []
    fetched = 0
    
    for url, intended_dt in urls[:max_fetch]:
        await asyncio.sleep(DELAY)
        result = await fetch_and_parse(url)
        if not result['ok']:
            continue
        text = result['text']
        if result.get('chinese_chars',0) < 200:
            continue  # too short
        fetched += 1
        
        doc_type = detect_type(url, result['title'], text)
        if doc_type == 'general':
            doc_type = intended_dt
        
        city = school.get('city','')
        chunks = chunk_document(text=text, doc_type=doc_type, school_name=name,
                                city=city, province=None, year=2025,
                                source_url=result['url'],
                                source_name=website.replace('https://','').rstrip('/'),
                                source_type='official_university',
                                data_source='official', confidence='high')
        all_chunks.extend(chunks)
        sources.append({'url': result['url'][:120], 'doc_type': doc_type, 'chunks': len(chunks),
                        'chars': result.get('chinese_chars',0)})
        logger.info(f"  ✅ {result['url'][:70]} → {len(chunks)} chunks [{doc_type}]")
    
    stats = index_chunks(all_chunks)
    return {'school': name, 'urls_found': len(urls), 'fetched': fetched,
            'chunks_created': len(all_chunks), 'indexed': stats['inserted'], 'sources': sources}


async def crawl_batch(schools, max_fetch=15):
    results = []
    for i, s in enumerate(schools):
        print(f"\n[{i+1}/{len(schools)}] {s['name']}")
        try:
            r = await crawl_school(s, max_fetch)
            results.append(r)
        except Exception as e:
            results.append({'school': s['name'], 'error': str(e)[:100]})
        if i < len(schools)-1:
            await asyncio.sleep(2)
    return results


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    schools = get_p0_schools(n)
    
    print(f"\n{'='*60}")
    print(f"  择境 RAG 爬虫 v3 — site:edu.cn 搜索 + 真实页面抓取")
    print(f"  目标: {len(schools)} 所P0高校")
    print(f"{'='*60}\n")
    
    results = asyncio.run(crawl_batch(schools, max_fetch=12))
    
    total_fetched = sum(r.get('fetched',0) for r in results)
    total_indexed = sum(r.get('indexed',0) for r in results)
    
    print(f"\n{'='*60}")
    print(f"  完成: {len(schools)}校, 抓取{total_fetched}页, 入库{total_indexed}chunks")
    print(f"{'='*60}")
    
    # Save
    report = {'timestamp': datetime.utcnow().isoformat(), 'schools': len(schools),
              'total_fetched': total_fetched, 'total_indexed': total_indexed,
              'results': results}
    path = PROJECT_ROOT / "rag_output" / "crawl_report_v3.json"
    with open(path, 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"报告: {path}")

if __name__ == "__main__":
    main()
