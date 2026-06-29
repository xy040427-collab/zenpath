"""
择境 RAG 爬虫 v4 — 浏览器提取URL + httpx批量抓取

策略：
  1. 浏览器访问高校首页 → JS提取招生/专业/就业相关链接
  2. 保存真实URL到数据库
  3. httpx异步批量抓取这些URL
"""

import asyncio, hashlib, json, logging, re, sqlite3, sys, time
from datetime import datetime
from pathlib import Path

import httpx

_PROJECT_ROOT = Path(__file__).resolve()
while _PROJECT_ROOT.name:
    if (_PROJECT_ROOT / "backend" / "gaokao.db").exists():
        break
    _PROJECT_ROOT = _PROJECT_ROOT.parent
PROJECT_ROOT = _PROJECT_ROOT
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

logger = logging.getLogger(__name__)
UA = "Mozilla/5.0 (compatible; ZENPATH-RAG/4.0; +https://zenpath.cn)"
TIMEOUT = 20; DELAY = 2

DB_DIR = PROJECT_ROOT / "backend"
URLS_FILE = PROJECT_ROOT / "rag_output" / "discovered_urls_v4.json"

# ─── Browser URL Discovery ──────────────────────────────────────────────────

# For now, use console expressions on each school's homepage.
# The browser needs to be called externally; we store discovered URLs here.

def save_discovered_urls(school_name: str, urls: list[dict]):
    """Save discovered URLs for later batch fetching."""
    all_urls = {}
    if URLS_FILE.exists():
        with open(URLS_FILE) as f:
            all_urls = json.load(f)
    all_urls[school_name] = urls
    with open(URLS_FILE, 'w') as f:
        json.dump(all_urls, f, ensure_ascii=False, indent=2)

def load_discovered_urls() -> dict:
    if URLS_FILE.exists():
        with open(URLS_FILE) as f:
            return json.load(f)
    return {}

# ─── Batch HTTP Fetch ───────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(str(DB_DIR / "gaokao.db"))
    conn.row_factory = sqlite3.Row
    return conn

def get_existing_hashes():
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT content_hash FROM rag_chunks WHERE source_type='official_university'").fetchall()
    conn.close()
    return set(r[0] for r in rows if r[0])

def index_chunks(chunks):
    conn = get_db(); stats = {'inserted':0,'skipped':0}
    now = datetime.utcnow().isoformat()
    hashes = get_existing_hashes()
    try:
        for c in chunks:
            content = c.get('content','')
            if len(content.strip()) < 100: stats['skipped']+=1; continue
            ch = c.get('content_hash') or hashlib.md5(content.encode()).hexdigest()[:12]
            if ch in hashes: stats['skipped']+=1; continue
            cid = c.get('chunk_id', f"{c.get('school_name','')}_{c.get('doc_type','')}_{ch}")
            if conn.execute("SELECT 1 FROM rag_chunks WHERE chunk_id=?",(cid,)).fetchone(): stats['skipped']+=1; continue
            conn.execute("""INSERT INTO rag_chunks(chunk_id,doc_type,school_name,major_name,city,province,year,title,section,content,source_url,source_name,source_type,data_source,confidence,content_hash,crawled_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(
                cid,c.get('doc_type'),c.get('school_name'),c.get('major_name'),c.get('city'),c.get('province'),c.get('year',2025),c.get('title',''),c.get('section',''),content,c.get('source_url'),c.get('source_name'),c.get('source_type','official_university'),c.get('data_source','official'),c.get('confidence','high'),ch,now,now,now))
            hashes.add(ch); stats['inserted']+=1
        conn.commit()
    except Exception as e: logger.error(f"Index error: {e}"); conn.rollback()
    finally: conn.close()
    return stats

async def fetch_page(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={'User-Agent':UA}) as client:
            resp = await client.get(url); resp.raise_for_status()
            ct = resp.headers.get('content-type','')
            if 'pdf' in ct: return {'ok':False,'url':url,'reason':'pdf'}
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text,'html.parser')
                title = soup.title.get_text().strip() if soup.title else ''
                for t in soup.find_all(['script','style','nav','footer','header']): t.decompose()
                text = soup.get_text(separator='\n')
                for pat in [r'版权所有[^\n]*',r'Copyright[^\n]*',r'ICP[备证].*?\n',r'地址[：:][^\n]*',r'电话[：:][^\n]*',r'邮箱[：:][^\n]*',r'邮编[：:][^\n]*',r'分享到[^\n]*',r'设为首页.*?\n',r'加入收藏.*?\n',r'友情链接.*?\n',r'首页.*?上一页.*?\n']:
                    text = re.sub(pat,'',text)
                text = re.sub(r'\n{3,}','\n\n',text)
                chinese = len(re.findall(r'[\u4e00-\u9fff]',text))
                return {'ok':True,'url':str(resp.url),'title':title,'text':text.strip(),'chinese_chars':chinese}
            except: return {'ok':False,'url':url,'reason':'parse error'}
    except Exception as e: return {'ok':False,'url':url,'reason':str(e)[:80]}

def detect_type(url, title, text):
    c = (url+' '+title+' '+text[:300]).lower()
    # Only exact employment report phrases — do NOT match bare '就业' or '/jy/'
    if any(k in c for k in ['就业质量报告','毕业生就业质量报告','就业质量年度报告',
                              '就业质量报告.pdf']): return 'employment_report'
    if any(k in c for k in ['招生章程','录取规则','录取办法']): return 'admission_policy'
    if any(k in c for k in ['专业介绍','培养方案','培养目标','主干课程','核心课程']): return 'major_profile'
    if any(k in c for k in ['学科建设','重点学科','一流专业','学科评估','双一流']): return 'discipline_evaluation'
    if any(k in c for k in ['学校简介','学校概况','学院简介','学校介绍']): return 'school_profile'
    if '/zs' in url.lower() or 'zhaosheng' in url.lower(): return 'admission_policy'
    if '/zy' in url.lower(): return 'major_profile'
    if '/xxgk' in url.lower() or '/about' in url.lower(): return 'school_profile'
    return 'general'

async def fetch_all_discovered(batch_name: str = None):
    """
    Fetch all URLs discovered via browser and stored in URLS_FILE.
    If batch_name provided, only fetch that school's URLs.
    """
    from rag.chunker import chunk_document
    
    all_discovered = load_discovered_urls()
    if not all_discovered:
        print("No discovered URLs found. Run browser discovery first.")
        return
    
    schools = list(all_discovered.keys()) if not batch_name else [batch_name]
    
    total_fetched = 0; total_indexed = 0; results = []
    
    for school in schools:
        urls = all_discovered.get(school, [])
        if not urls: continue
        
        print(f"\n🕷️ {school}: {len(urls)} URLs")
        all_chunks = []; fetched = 0
        
        for u in urls:
            url = u.get('url',''); label = u.get('label','')
            await asyncio.sleep(DELAY)
            result = await fetch_page(url)
            if not result['ok']: continue
            if result.get('chinese_chars',0) < 200: continue
            fetched += 1
            
            dt = detect_type(url, result.get('title',''), result.get('text',''))
            if dt == 'general':
                # Infer from label
                if any(k in label for k in ['招生章程','录取']): dt = 'admission_policy'
                elif any(k in label for k in ['专业','培养']): dt = 'major_profile'
                elif any(k in label for k in ['就业','毕业']): dt = 'employment_report'
                elif any(k in label for k in ['简介','概况']): dt = 'school_profile'
                else: dt = 'school_profile'
            
            chunks = chunk_document(text=result['text'], doc_type=dt, school_name=school,
                                    city='', province=None, year=2025,
                                    source_url=result['url'], source_name=url.split('/')[2] if '//' in url else url,
                                    source_type='official_university', data_source='official', confidence='high')
            all_chunks.extend(chunks)
            print(f"  ✅ {result['url'][:70]} → {len(chunks)} [{dt}]")
        
        stats = index_chunks(all_chunks)
        total_fetched += fetched; total_indexed += stats['inserted']
        results.append({'school': school, 'fetched': fetched, 'chunks': len(all_chunks), 'indexed': stats['inserted']})
    
    print(f"\n{'='*60}")
    print(f"  完成: {len(schools)}校, 抓取{total_fetched}页, 入库{total_indexed}chunks")
    return results


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    results = asyncio.run(fetch_all_discovered())
    if results:
        report = {'timestamp': datetime.utcnow().isoformat(), 'results': results}
        path = PROJECT_ROOT / "rag_output" / "crawl_report_v4.json"
        with open(path, 'w') as f: json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"报告: {path}")

if __name__ == "__main__":
    main()
