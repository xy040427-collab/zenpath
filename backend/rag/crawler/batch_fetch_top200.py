"""
batch_fetch_top200 — 全量抓取前200所高校RAG
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
TIMEOUT = 15; DELAY = 1; MAX_FOLLOW = 5

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
            return {'ok':True, 'url':str(r.url), 'html':r.text}
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
    links = list(set(urljoin(url, a.get('href','')) for a in soup.find_all('a') if a.get('href','') and not a.get('href','').startswith('#') and not a.get('href','').startswith('javascript:')))
    return {'title':title, 'text':body.strip(), 'chars':chinese, 'links':links}

def detect_type(url, title, text):
    c = (url+' '+title+' '+text[:300]).lower()
    # Only exact employment report phrases — do NOT match bare '就业'
    if any(k in c for k in ['就业质量报告','毕业生就业质量报告','就业质量年度报告',
                              '就业质量报告.pdf']): return 'employment_report'
    if any(k in c for k in ['招生章程','录取规则']): return 'admission_policy'
    if any(k in c for k in ['专业介绍','培养目标','核心课程']): return 'major_profile'
    if any(k in c for k in ['学科','一流专业']): return 'discipline_evaluation'
    if '招生' in c or 'zs' in url.lower(): return 'admission_policy'
    return 'school_profile'

async def crawl_one(name, domain, city=''):
    url = f'https://{domain}' if not domain.startswith('http') else domain
    hp = await fetch(url)
    if not hp['ok']:
        # Try http
        if url.startswith('https'):
            hp = await fetch(url.replace('https://','http://'))
    if not hp['ok']: return 0
    
    parsed = parse(hp['html'], hp['url'])
    total = 0
    done = get_done_urls()
    
    # Index homepage if new
    if hp['url'] not in done and parsed['chars'] >= 100:
        dt = detect_type(url, parsed['title'], parsed['text'])
        chunks = chunk_document(text=parsed['text'], doc_type=dt, school_name=name, city=city,
                                year=2025, source_url=hp['url'], source_name=domain,
                                source_type='official_university', data_source='official', confidence='high')
        total += index_chunks(chunks)['inserted']
    
    # Follow up to MAX_FOLLOW new article links
    domain_key = '.'.join(domain.split('.')[-2:])  # last 2 parts of domain
    same_site = [l for l in parsed['links'] if domain_key in l and l != hp['url']]
    article_pats = ['/art/', '/info/', '/content/', '.htm', 'detail', '/col/']
    candidates = [l for l in same_site if any(p in l for p in article_pats)][:MAX_FOLLOW*3]
    new = [l for l in candidates if l not in done][:MAX_FOLLOW]
    
    for link in new:
        await asyncio.sleep(DELAY)
        ap = await fetch(link)
        if not ap['ok']: continue
        apd = parse(ap['html'], ap['url'])
        if apd['chars'] < 150: continue
        dt = detect_type(link, apd['title'], apd['text'])
        chunks = chunk_document(text=apd['text'], doc_type=dt, school_name=name, city=city,
                                year=2025, source_url=ap['url'], source_name=domain,
                                source_type='official_university', data_source='official', confidence='high')
        total += index_chunks(chunks)['inserted']
    
    return total

async def main():
    with open(PROJECT_ROOT / 'rag_output' / 'crawl_targets_top200.json') as f:
        targets = json.load(f)
    
    print(f"\n{'='*60}")
    print(f"  全量抓取 {len(targets)} 所高校")
    print(f"  每校抓首页 + 跟{MAX_FOLLOW}个链接")
    print(f"{'='*60}\n")
    
    total_chunks = 0
    results = []
    batch = 0
    
    for i, t in enumerate(targets):
        name, domain, city = t['name'], t['domain'], t.get('city','')
        n = await crawl_one(name, domain, city)
        total_chunks += n
        results.append({'name': name, 'chunks': n})
        batch += 1
        
        # Print progress every 10
        if batch % 10 == 0:
            print(f"  [{i+1}/{len(targets)}] {total_chunks} chunks total | last: {name} +{n}")
        
        await asyncio.sleep(DELAY)
    
    print(f"\n{'='*60}")
    print(f"  完成: {len(targets)} 校, 入库 {total_chunks} chunks")
    
    # Save report
    report = {'timestamp': datetime.utcnow().isoformat(), 'schools': len(targets),
              'total_chunks': total_chunks, 'results': results}
    with open(PROJECT_ROOT / 'rag_output' / 'crawl_report_top200.json', 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return total_chunks

if __name__ == "__main__":
    asyncio.run(main())
