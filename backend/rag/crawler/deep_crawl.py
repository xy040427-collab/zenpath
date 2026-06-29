"""
Step3-5 combined: Deep crawl accessible schools to boost L2/L3/L4
Uses source_map entries → follows links → finds specific doc types
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

UA = "Mozilla/5.0 (compatible; ZENPATH/1.0)"; TIMEOUT=15; DELAY=1

def get_db():
    conn = sqlite3.connect(str(PROJECT_ROOT / "backend" / "gaokao.db"))
    conn.row_factory = sqlite3.Row; return conn

def get_done():
    conn=get_db(); urls=set(r[0] for r in conn.execute("SELECT DISTINCT source_url FROM rag_chunks WHERE source_url IS NOT NULL").fetchall() if r[0]); conn.close(); return urls

def index_chunks(chunks):
    conn=get_db(); s={'i':0,'s':0}; now=datetime.utcnow().isoformat()
    h=set(r[0] for r in conn.execute("SELECT DISTINCT content_hash FROM rag_chunks WHERE source_type='official_university'").fetchall() if r[0])
    try:
        for c in chunks:
            ct=c.get('content','')
            if len(ct.strip())<80: s['s']+=1; continue
            ch=c.get('content_hash') or hashlib.md5(ct.encode()).hexdigest()[:12]
            if ch in h: s['s']+=1; continue
            cid=c.get('chunk_id',f"{c.get('school_name','')}_{c.get('doc_type','')}_{ch}")
            if conn.execute("SELECT 1 FROM rag_chunks WHERE chunk_id=?",(cid,)).fetchone(): s['s']+=1; continue
            conn.execute("""INSERT INTO rag_chunks(chunk_id,doc_type,school_name,major_name,city,province,year,title,section,content,source_url,source_name,source_type,data_source,confidence,content_hash,crawled_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(cid,c.get('doc_type'),c.get('school_name'),c.get('major_name'),c.get('city'),c.get('province'),c.get('year',2025),c.get('title',''),c.get('section',''),ct,c.get('source_url'),c.get('source_name'),c.get('source_type','official_university'),c.get('data_source','official'),c.get('confidence','high'),ch,now,now,now))
            h.add(ch); s['i']+=1
        conn.commit()
    except Exception as e: print(f"  idx:{e}"); conn.rollback()
    finally: conn.close()
    return s

async def fetch(url):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={'User-Agent':UA}) as c:
            r=await c.get(url); r.raise_for_status()
            return {'ok':True,'url':str(r.url),'html':r.text}
    except: return {'ok':False}

def parse(html, url):
    soup=BeautifulSoup(html,'html.parser')
    title=soup.title.get_text().strip() if soup.title else ''
    for t in soup.find_all(['script','style','nav','footer','header']): t.decompose()
    body=soup.get_text(separator='\n')
    for p in [r'版权所有[^\n]*',r'Copyright[^\n]*',r'ICP[备证].*?\n',r'地址[：:][^\n]*',r'电话[：:][^\n]*',r'邮箱[：:][^\n]*']: body=re.sub(p,'',body)
    body=re.sub(r'\n{3,}','\n\n',body)
    cn=len(re.findall(r'[\u4e00-\u9fff]',body))
    links=[]
    for a in soup.find_all('a'):
        href=a.get('href','')
        if not href or href.startswith('#') or href.startswith('javascript:'): continue
        links.append({'url':urljoin(url,href),'label':(a.get_text()or'').strip()[:60]})
    return {'title':title,'text':body.strip(),'cn':cn,'links':links}

def detect_type(url, title, text):
    c=(url+' '+title+' '+text[:200]).lower()
    # Only exact employment report phrases — do NOT match bare '就业'
    if any(k in c for k in ['就业质量报告','毕业生就业质量报告','就业质量年度报告',
                              '毕业生就业质量年度报告','本科毕业生就业质量年度报告',
                              '就业质量报告.pdf']): return 'employment_report'
    if any(k in c for k in ['招生章程','录取规则','录取办法']): return 'admission_policy'
    if any(k in c for k in ['专业介绍','培养方案','培养目标','主干课程','核心课程','专业简介']): return 'major_profile'
    if any(k in c for k in ['学科建设','重点学科','一流专业','学科评估']): return 'discipline_evaluation'
    if any(k in c for k in ['学校简介','学校概况','学院简介']): return 'school_profile'
    if '招生' in c: return 'admission_policy'
    return 'school_profile'

def link_doc_type(link):
    """Guess doc_type from link URL+label."""
    u=link['url'].lower(); l=link['label']
    if any(k in u+l for k in ['招生章程','录取规则','录取办法']): return 'admission_policy'
    # Only exact employment report keywords — do NOT match bare '就业'
    if any(k in u+l for k in ['就业质量报告','jyzl','bysjy']): return 'employment_report'
    if any(k in u+l for k in ['专业介绍','培养方案','培养目标','zyjs','major']): return 'major_profile'
    if any(k in u+l for k in ['学科','一流专业','重点学科','xkjs']): return 'discipline_evaluation'
    if any(k in u+l for k in ['简介','概况','xxgk','about']): return 'school_profile'
    if '招生' in u+l: return 'admission_policy'
    return None

async def deep_crawl(start_url, school_name, city, domain, max_pages=20):
    """Crawl from start_url, following relevant links. Returns total chunks inserted."""
    done_urls = get_done()
    total = 0
    visited = set()
    queue = [(start_url, 0)]  # (url, depth)
    pages_processed = 0
    
    while queue and pages_processed < max_pages:
        url, depth = queue.pop(0)
        if url in visited or url in done_urls: continue
        if depth > 2: continue
        
        await asyncio.sleep(DELAY)
        result = await fetch(url)
        if not result['ok']: continue
        
        visited.add(url)
        pages_processed += 1
        parsed = parse(result['html'], result['url'])
        
        # Index this page if content-rich
        if parsed['cn'] >= 150 and result['url'] not in done_urls:
            dt = detect_type(url, parsed['title'], parsed['text'])
            chunks = chunk_document(text=parsed['text'], doc_type=dt, school_name=school_name,
                                    city=city, year=2025, source_url=result['url'],
                                    source_name=domain, source_type='official_university',
                                    data_source='official', confidence='high')
            total += index_chunks(chunks)['i']
        
        # Enqueue same-domain article links
        for link in parsed['links']:
            link_url = link['url']
            if link_url in visited or link_url in done_urls: continue
            # Only follow same-site article links
            if domain not in urlparse(link_url).netloc: continue
            if not any(p in link_url for p in ['.htm','/art/','/info/','/content/','/col/']): continue
            
            ldt = link_doc_type(link)
            if ldt:
                queue.append((link_url, depth+1))
    
    return total


async def main():
    conn = get_db()
    
    # Get schools with source_map entries for undergraduate_admission_site
    sources = conn.execute("""
        SELECT DISTINCT sm.school_name, sm.source_url, sm.source_name, s.city, s.ranking
        FROM school_source_map sm
        JOIN schools s ON sm.school_name = s.name
        WHERE sm.source_type = 'undergraduate_admission_site' AND sm.verify_status = 'verified'
        ORDER BY s.ranking
    """).fetchall()
    
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"  Deep crawl: {len(sources)} schools from source_map")
    print(f"  Following links up to 2 levels deep")
    print(f"{'='*60}\n")
    
    results = []
    total = 0
    for i, (name, url, domain, city, ranking) in enumerate(sources):
        n = await deep_crawl(url, name, city, domain)
        total += n
        results.append({'name':name, 'ranking':ranking, 'chunks':n})
        if (i+1) % 10 == 0:
            print(f"  [{i+1}/{len(sources)}] {total} chunks total | {name}: +{n}")
    
    print(f"\n{'='*60}")
    print(f"  Done: {total} new chunks across {len(sources)} schools")
    
    # Save report
    report = {'timestamp': datetime.utcnow().isoformat(), 'schools':len(sources),
              'total_chunks':total, 'results':results}
    with open(PROJECT_ROOT/'rag_output'/'deep_crawl_report.json','w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return total

if __name__ == "__main__":
    asyncio.run(main())
