"""
batch_fetch_v2 — 抓首页 → 提取所有链接 → 跟进抓取内容页
"""

import asyncio, hashlib, json, re, sqlite3, sys, time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

_PROJECT_ROOT = Path(__file__).resolve()
while _PROJECT_ROOT.name:
    if (_PROJECT_ROOT / "backend" / "gaokao.db").exists(): break
    _PROJECT_ROOT = _PROJECT_ROOT.parent
PROJECT_ROOT = _PROJECT_ROOT
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
from rag.chunker import chunk_document

UA = "Mozilla/5.0 (compatible; ZENPATH/1.0)"
TIMEOUT = 20; DELAY = 2; MAX_LINKS = 20

def get_db():
    conn = sqlite3.connect(str(PROJECT_ROOT / "backend" / "gaokao.db"))
    conn.row_factory = sqlite3.Row; return conn

def get_done_urls():
    conn = get_db()
    urls = set(r[0] for r in conn.execute("SELECT DISTINCT source_url FROM rag_chunks WHERE source_url IS NOT NULL").fetchall() if r[0])
    conn.close(); return urls

def index_chunks(chunks):
    conn = get_db(); stats = {'inserted':0,'skipped':0}
    now = datetime.utcnow().isoformat()
    hashes = set(r[0] for r in conn.execute("SELECT DISTINCT content_hash FROM rag_chunks WHERE source_type='official_university'").fetchall() if r[0])
    done_urls = get_done_urls()
    try:
        for c in chunks:
            content = c.get('content','')
            if len(content.strip()) < 80: stats['skipped']+=1; continue
            ch = c.get('content_hash') or hashlib.md5(content.encode()).hexdigest()[:12]
            if ch in hashes: stats['skipped']+=1; continue
            cid = c.get('chunk_id', f"{c.get('school_name','')}_{c.get('doc_type','')}_{ch}")
            if conn.execute("SELECT 1 FROM rag_chunks WHERE chunk_id=?",(cid,)).fetchone(): stats['skipped']+=1; continue
            conn.execute("""INSERT INTO rag_chunks(chunk_id,doc_type,school_name,city,province,year,title,section,content,source_url,source_name,source_type,data_source,confidence,content_hash,crawled_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(
                cid,c.get('doc_type'),c.get('school_name'),c.get('city'),c.get('province'),c.get('year',2025),c.get('title',''),c.get('section',''),content,c.get('source_url'),c.get('source_name'),c.get('source_type','official_university'),c.get('data_source','official'),c.get('confidence','high'),ch,now,now,now))
            hashes.add(ch); stats['inserted']+=1
        conn.commit()
    except Exception as e: print(f"  Index err: {e}"); conn.rollback()
    finally: conn.close()
    return stats

async def fetch(url):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={'User-Agent':UA}) as c:
            r = await c.get(url); r.raise_for_status()
            return {'ok':True, 'url':str(r.url), 'html':r.text, 'status':r.status_code}
    except: return {'ok':False}

def parse(text, url):
    soup = BeautifulSoup(text, 'html.parser')
    title = soup.title.get_text().strip() if soup.title else ''
    for t in soup.find_all(['script','style','nav','footer','header']): t.decompose()
    body = soup.get_text(separator='\n')
    for pat in [r'版权所有[^\n]*',r'Copyright[^\n]*',r'ICP[备证].*?\n',r'地址[：:][^\n]*',r'电话[：:][^\n]*',r'邮箱[：:][^\n]*']:
        body = re.sub(pat,'',body)
    body = re.sub(r'\n{3,}','\n\n',body)
    chinese = len(re.findall(r'[\u4e00-\u9fff]',body))
    
    # Also extract all links from this page
    links = []
    seen = set()
    for a in soup.find_all('a'):
        href = a.get('href','')
        if not href or href.startswith('#') or href.startswith('javascript:'): continue
        full = urljoin(url, href)
        if full in seen: continue; seen.add(full)
        links.append(full)
    
    return {'title':title, 'text':body.strip(), 'chars':chinese, 'links':links}

def detect_type(url, title, text):
    c = (url+' '+title+' '+text[:300]).lower()
    # Only exact employment report phrases — do NOT match bare '就业'
    if any(k in c for k in ['就业质量报告','毕业生就业质量报告','就业质量年度报告',
                              '就业质量报告.pdf']): return 'employment_report'
    if any(k in c for k in ['招生章程','录取规则']): return 'admission_policy'
    if any(k in c for k in ['专业介绍','培养目标','核心课程']): return 'major_profile'
    if any(k in c for k in ['学科','一流专业','重点学科']): return 'discipline_evaluation'
    if any(k in c for k in ['简介','概况']): return 'school_profile'
    if '招生' in c or 'zs' in url.lower(): return 'admission_policy'
    return 'school_profile'


async def crawl_school(name, domain, city='', max_follow=15):
    """Fetch homepage, extract links, follow content pages."""
    url = f'https://{domain}' if not domain.startswith('http') else domain
    print(f"\n📚 {name}: {domain}")
    
    # 1. Fetch homepage
    hp = await fetch(url)
    if not hp['ok']:
        print(f"  ❌ Homepage unreachable")
        return 0
    
    parsed = parse(hp['html'], hp['url'])
    print(f"  Homepage: {parsed['chars']} Chinese chars, {len(parsed['links'])} links")
    
    total = 0
    
    # Index homepage
    if parsed['chars'] >= 100:
        dt = detect_type(url, parsed['title'], parsed['text'])
        chunks = chunk_document(text=parsed['text'], doc_type=dt, school_name=name, city=city,
                                year=2025, source_url=hp['url'], source_name=domain,
                                source_type='official_university', data_source='official', confidence='high')
        s = index_chunks(chunks)
        total += s['inserted']
        print(f"  HP → {s['inserted']} chunks [{dt}]")
    
    # 2. Filter and follow links
    # Filter: same domain, likely article page (has /art/, /info/, /col/, .htm, .html)
    same_domain = [l for l in parsed['links'] if domain in l and l != url]
    article_patterns = ['/art/', '/info/', '/content/', '.htm', 'detail']
    candidates = [l for l in same_domain if any(p in l for p in article_patterns)]
    
    done = get_done_urls()
    new_candidates = [l for l in candidates if l not in done][:max_follow]
    
    print(f"  Following {len(new_candidates)} new article links...")
    
    for i, link in enumerate(new_candidates):
        await asyncio.sleep(DELAY)
        ap = await fetch(link)
        if not ap['ok']: continue
        
        apd = parse(ap['html'], ap['url'])
        if apd['chars'] < 150: continue
        
        dt = detect_type(link, apd['title'], apd['text'])
        chunks = chunk_document(text=apd['text'], doc_type=dt, school_name=name, city=city,
                                year=2025, source_url=ap['url'], source_name=domain,
                                source_type='official_university', data_source='official', confidence='high')
        s = index_chunks(chunks)
        total += s['inserted']
        if s['inserted'] > 0:
            print(f"  [{i+1}] {apd['chars']}c → {s['inserted']} [{dt}] {link[:70]}")
    
    return total


async def main():
    with open(PROJECT_ROOT / 'rag_output' / 'admission_domains.json') as f:
        data = json.load(f)
    conn = get_db()
    schools_db = {r['name']: dict(r) for r in conn.execute("SELECT name, city FROM schools").fetchall()}
    conn.close()
    
    known = [(k, v['known_admission']) for k, v in data.items() if v['known_admission']]
    
    # Filter to accessible ones (skip known failures)
    skip = ['北京大学', '复旦大学', '北京航空航天大学', '四川大学', '西北工业大学', '山东大学', '大连理工大学', '湖南大学']
    targets = [(n, d) for n, d in known if n not in skip]
    
    print(f"\n{'='*60}")
    print(f"  batch_fetch_v2: 首页+跟链接, {len(targets)} 所学校")
    print(f"{'='*60}")
    
    total = 0
    for name, domain in targets:
        sch = schools_db.get(name, {})
        n = await crawl_school(name, domain, sch.get('city',''))
        if n: total += n
    
    print(f"\n{'='*60}")
    print(f"  总计入库: {total} chunks")
    return total

if __name__ == "__main__":
    asyncio.run(main())
