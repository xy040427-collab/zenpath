"""
batch_fetch_v3: 抓主站首页→提取招生子站链接→深入抓取
"""

import asyncio, hashlib, json, re, sqlite3, sys, time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

_PROJECT_ROOT = Path(__file__).resolve()
while _PROJECT_ROOT.name:
    if (_PROJECT_ROOT / "backend" / "gaokao.db").exists(): break
    _PROJECT_ROOT = _PROJECT_ROOT.parent
PROJECT_ROOT = _PROJECT_ROOT
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
from rag.chunker import chunk_document

UA = "Mozilla/5.0 (compatible; ZENPATH/1.0)"; TIMEOUT = 15; DELAY = 1

def get_db():
    conn = sqlite3.connect(str(PROJECT_ROOT / "backend" / "gaokao.db"))
    conn.row_factory = sqlite3.Row; return conn

def get_done(): 
    conn = get_db(); urls = set(r[0] for r in conn.execute("SELECT DISTINCT source_url FROM rag_chunks WHERE source_url IS NOT NULL").fetchall() if r[0]); conn.close(); return urls

def index_chunks(chunks):
    conn = get_db(); stats = {'i':0,'s':0}; now = datetime.utcnow().isoformat()
    hashes = set(r[0] for r in conn.execute("SELECT DISTINCT content_hash FROM rag_chunks WHERE source_type='official_university'").fetchall() if r[0])
    try:
        for c in chunks:
            ct = c.get('content','')
            if len(ct.strip()) < 80: stats['s']+=1; continue
            ch = c.get('content_hash') or hashlib.md5(ct.encode()).hexdigest()[:12]
            if ch in hashes: stats['s']+=1; continue
            cid = c.get('chunk_id', f"{c.get('school_name','')}_{c.get('doc_type','')}_{ch}")
            if conn.execute("SELECT 1 FROM rag_chunks WHERE chunk_id=?",(cid,)).fetchone(): stats['s']+=1; continue
            conn.execute("""INSERT INTO rag_chunks(chunk_id,doc_type,school_name,city,province,year,title,section,content,source_url,source_name,source_type,data_source,confidence,content_hash,crawled_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(
                cid,c.get('doc_type'),c.get('school_name'),c.get('city'),c.get('province'),c.get('year',2025),c.get('title',''),c.get('section',''),ct,c.get('source_url'),c.get('source_name'),c.get('source_type','official_university'),c.get('data_source','official'),c.get('confidence','high'),ch,now,now,now))
            hashes.add(ch); stats['i']+=1
        conn.commit()
    except Exception as e: print(f"  idx err: {e}"); conn.rollback()
    finally: conn.close()
    return stats

async def fetch(url):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={'User-Agent':UA}) as c:
            r = await c.get(url); r.raise_for_status()
            return {'ok':True, 'url':str(r.url), 'html':r.text}
    except: return {'ok':False}

def parse(text, url):
    soup = BeautifulSoup(text, 'html.parser')
    title = soup.title.get_text().strip() if soup.title else ''
    for t in soup.find_all(['script','style','nav','footer','header']): t.decompose()
    body = soup.get_text(separator='\n')
    for pat in [r'版权所有[^\n]*',r'Copyright[^\n]*',r'ICP[备证].*?\n',r'地址[：:][^\n]*',r'电话[：:][^\n]*',r'邮箱[：:][^\n]*']: body = re.sub(pat,'',body)
    body = re.sub(r'\n{3,}','\n\n',body); chinese = len(re.findall(r'[\u4e00-\u9fff]',body))
    links = []
    for a in soup.find_all('a'):
        href = a.get('href','')
        if not href or href.startswith('#') or href.startswith('javascript:'): continue
        text_label = (a.get_text() or '').strip()
        full = urljoin(url, href)
        links.append({'url':full, 'label':text_label})
    return {'title':title, 'text':body.strip(), 'chars':chinese, 'links':links}

def detect_type(url, title, text):
    c = (url+' '+title+' '+text[:300]).lower()
    # Only exact employment report phrases — do NOT match bare '就业'
    if any(k in c for k in ['就业质量报告','毕业生就业质量报告','就业质量年度报告',
                              '就业质量报告.pdf']): return 'employment_report'
    if any(k in c for k in ['招生章程','录取规则']): return 'admission_policy'
    if any(k in c for k in ['专业介绍','培养目标','核心课程']): return 'major_profile'
    if any(k in c for k in ['学科','一流专业']): return 'discipline_evaluation'
    if '招生' in c: return 'admission_policy'
    return 'school_profile'

def is_admission_link(link):
    """Check if a link points to an admission-related page."""
    url = link['url'].lower(); label = link['label']
    keywords = ['zsb','zhaosheng','admission','bkzs','undergraduate','recruit',
                '招生','报考','录取','本科招生','zsjy','jwzs']
    for kw in keywords:
        if kw in url or kw in label: return True
    
    # Subdomain pattern: xxx.xxx.edu.cn (not www)
    domain = urlparse(link['url']).netloc
    parts = domain.split('.')
    if len(parts) >= 4 and parts[-1] in ('cn','edu') and parts[0] != 'www':
        for kw in ['zs','zb','admission','recruit','join','apply']:
            if kw in parts[0]: return True
    return False


async def crawl_deep(url, school_name, city, depth=1, max_pages=8):
    """Recursively crawl a sub-site, following links up to depth levels."""
    if depth <= 0 or max_pages <= 0: return 0
    
    result = await fetch(url)
    if not result['ok']: return 0
    
    parsed = parse(result['html'], result['url'])
    total = 0
    done_urls = get_done()
    domain = urlparse(result['url']).netloc
    
    # Index this page
    if result['url'] not in done_urls and parsed['chars'] >= 100:
        dt = detect_type(url, parsed['title'], parsed['text'])
        chunks = chunk_document(text=parsed['text'], doc_type=dt, school_name=school_name, city=city,
                                year=2025, source_url=result['url'], source_name=domain,
                                source_type='official_university', data_source='official', confidence='high')
        total += index_chunks(chunks)['i']
    
    # Follow links on same domain
    same_domain = [l for l in parsed['links'] if domain in l['url'] and l['url'] != result['url']]
    article_pats = ['/art/', '/info/', '/content/', '.htm', 'detail', '/col/']
    candidates = [l['url'] for l in same_domain if any(p in l['url'] for p in article_pats)]
    new = [u for u in candidates if u not in done_urls][:max_pages]
    
    for link in new:
        await asyncio.sleep(DELAY)
        n = await crawl_deep(link, school_name, city, depth-1, max_pages//2)
        total += n
    
    return total


async def crawl_school(name, website, city):
    """Fetch main site, find admission links, crawl deeply."""
    print(f"\n  {name}: {website[:50]}")
    
    # Step 1: Fetch main homepage
    hp = await fetch(website)
    if not hp['ok']: 
        print(f"    ❌ unreachable")
        return 0
    
    parsed = parse(hp['html'], hp['url'])
    total = 0
    done = get_done()
    
    # Index homepage if new and has content
    if hp['url'] not in done and parsed['chars'] >= 100:
        dt = detect_type(website, parsed['title'], parsed['text'])
        chunks = chunk_document(text=parsed['text'], doc_type=dt, school_name=name, city=city,
                                year=2025, source_url=hp['url'], source_name=urlparse(website).netloc,
                                source_type='official_university', data_source='official', confidence='high')
        total += index_chunks(chunks)['i']
    
    # Step 2: Find admission sub-site links
    admission_links = [l for l in parsed['links'] if is_admission_link(l)]
    print(f"    {len(admission_links)} admission links found")
    
    # Step 3: Deep crawl each admission link (sub-site)
    for al in admission_links[:3]:  # Max 3 sub-sites
        url = al['url']
        if url in done: continue
        label = al['label'][:30]
        await asyncio.sleep(DELAY)
        n = await crawl_deep(url, name, city, depth=2, max_pages=8)
        total += n
        if n > 0:
            print(f"    ✅ {label} → +{n}")
    
    return total


async def main():
    conn = get_db()
    covered = set(r[0] for r in conn.execute(
        "SELECT DISTINCT school_name FROM rag_chunks WHERE source_type='official_university'"
    ).fetchall())
    
    # Get uncovered top 200 with .edu.cn
    targets = []
    for r in conn.execute("""
        SELECT name, website, city, ranking FROM schools 
        WHERE ranking > 0 AND ranking <= 200 AND website LIKE '%.edu.cn%'
        ORDER BY ranking
    """).fetchall():
        if r['name'] not in covered:
            targets.append((r['name'], r['website'], r['city']))
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"  Deep crawl: {len(targets)} schools (sub-site discovery)")
    print(f"{'='*60}")
    
    total = 0
    for name, website, city in targets:
        n = await crawl_school(name, website, city)
        total += n
        print(f"    total +{n} (running: {total})")
        await asyncio.sleep(DELAY)
    
    print(f"\n{'='*60}")
    print(f"  Total: {total} chunks")
    return total

if __name__ == "__main__":
    asyncio.run(main())
