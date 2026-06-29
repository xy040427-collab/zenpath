"""
一步到位：取已知招生网域名 → 抓首页 → 提取正文 → 入库
"""

import asyncio, hashlib, json, re, sqlite3, sys, time
from datetime import datetime
from pathlib import Path

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
TIMEOUT = 20; DELAY = 2


def get_db():
    conn = sqlite3.connect(str(PROJECT_ROOT / "backend" / "gaokao.db"))
    conn.row_factory = sqlite3.Row; return conn


def index_chunks(chunks):
    conn = get_db(); stats = {'inserted': 0, 'skipped': 0}
    now = datetime.utcnow().isoformat()
    hashes = set(r[0] for r in conn.execute(
        "SELECT DISTINCT content_hash FROM rag_chunks WHERE source_type='official_university'").fetchall() if r[0])
    try:
        for c in chunks:
            content = c.get('content', '')
            if len(content.strip()) < 80: stats['skipped'] += 1; continue
            ch = c.get('content_hash') or hashlib.md5(content.encode()).hexdigest()[:12]
            if ch in hashes: stats['skipped'] += 1; continue
            cid = c.get('chunk_id', f"{c.get('school_name','')}_{c.get('doc_type','')}_{ch}")
            if conn.execute("SELECT 1 FROM rag_chunks WHERE chunk_id=?", (cid,)).fetchone():
                stats['skipped'] += 1; continue
            conn.execute("""INSERT INTO rag_chunks(chunk_id,doc_type,school_name,city,province,year,title,section,content,source_url,source_name,source_type,data_source,confidence,content_hash,crawled_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                cid, c.get('doc_type'), c.get('school_name'), c.get('city'), c.get('province'),
                c.get('year', 2025), c.get('title', ''), c.get('section', ''), content,
                c.get('source_url'), c.get('source_name'), c.get('source_type', 'official_university'),
                c.get('data_source', 'official'), c.get('confidence', 'high'), ch, now, now, now))
            hashes.add(ch); stats['inserted'] += 1
        conn.commit()
    except Exception as e:
        print(f"  Index error: {e}"); conn.rollback()
    finally: conn.close()
    return stats


async def fetch(url):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={'User-Agent': UA}) as c:
            r = await c.get(url); r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            title = soup.title.get_text().strip() if soup.title else ''
            for t in soup.find_all(['script', 'style', 'nav', 'footer', 'header']): t.decompose()
            text = soup.get_text(separator='\n')
            for pat in [r'版权所有[^\n]*', r'Copyright[^\n]*', r'ICP[备证].*?\n',
                        r'地址[：:][^\n]*', r'电话[：:][^\n]*', r'邮箱[：:][^\n]*']:
                text = re.sub(pat, '', text)
            text = re.sub(r'\n{3,}', '\n\n', text)
            return {'ok': True, 'url': str(r.url), 'title': title, 'text': text.strip(),
                    'chars': len(re.findall(r'[\u4e00-\u9fff]', text))}
    except Exception as e:
        return {'ok': False, 'url': url, 'error': str(e)[:80]}


def detect_type(url, title, text):
    c = (url + ' ' + title + ' ' + text[:300]).lower()
    # Only exact employment report phrases — do NOT match bare '就业'
    if any(k in c for k in ['就业质量报告','毕业生就业质量报告','就业质量年度报告',
                              '就业质量报告.pdf']): return 'employment_report'
    if any(k in c for k in ['专业介绍', '培养目标', '核心课程']): return 'major_profile'
    if any(k in c for k in ['学科', '一流专业']): return 'discipline_evaluation'
    if any(k in c for k in ['简介', '概况']): return 'school_profile'
    if '招生' in c: return 'admission_policy'
    return 'school_profile'


async def crawl_one(name, domain, city=''):
    """Fetch domain homepage, chunk, and index."""
    url = f'https://{domain}' if not domain.startswith('http') else domain
    print(f"  {name}: {url} ...", end=' ')
    result = await fetch(url)
    if not result['ok']:
        print(f"❌ {result.get('error','')}")
        return None
    text = result['text']
    chars = result['chars']
    if chars < 200:
        print(f"⚠️ only {chars} Chinese chars (skipped)")
        return None
    dt = detect_type(url, result['title'], text)
    chunks = chunk_document(text=text, doc_type=dt, school_name=name, city=city,
                            year=2025, source_url=result['url'],
                            source_name=domain, source_type='official_university',
                            data_source='official', confidence='high')
    stats = index_chunks(chunks)
    print(f"✅ {chars} chars → {stats['inserted']} chunks [{dt}]")
    return {'name': name, 'domain': domain, 'chunks': stats['inserted'], 'chars': chars, 'type': dt}


async def main():
    # Load known admission domains
    with open(PROJECT_ROOT / 'rag_output' / 'admission_domains.json') as f:
        data = json.load(f)
    
    # Get city info
    conn = get_db()
    schools_db = {r['name']: dict(r) for r in conn.execute("SELECT name, city FROM schools").fetchall()}
    conn.close()
    
    known = [(k, v['known_admission']) for k, v in data.items() if v['known_admission']]
    print(f"\n抓取 {len(known)} 所高校招生网首页\n")
    
    results = []
    for name, domain in known:
        sch = schools_db.get(name, {})
        city = sch.get('city', '')
        r = await crawl_one(name, domain, city)
        if r: results.append(r)
        await asyncio.sleep(DELAY)
    
    total = sum(r['chunks'] for r in results)
    print(f"\n{'='*50}")
    print(f"完成: {len(results)}/{len(known)} 校成功, 入库 {total} chunks")
    
    # Also re-fetch 中国农业大学's specific pages
    print(f"\n加抓中国农业大学招生章程等具体页面...")
    cau_pages = [
        ("中国农业大学", "https://jwzs.cau.edu.cn/art/2026/5/28/art_42837_1115831.html", "2026年本科招生章程"),
        ("中国农业大学", "https://www.cau.edu.cn/xxgk/xxjj/index.htm", "学校简介"),
        ("中国农业大学", "https://www.cau.edu.cn/xxgk/dxzc/index.htm", "大学章程"),
        ("中国农业大学", "https://www.cau.edu.cn/zsjy/jy/index.htm", "就业信息"),
    ]
    for name, url, label in cau_pages:
        print(f"  {label}: {url} ...", end=' ')
        result = await fetch(url)
        if not result['ok'] or result['chars'] < 200:
            print(f"❌")
            continue
        dt = detect_type(url, result['title'], result['text'])
        chunks = chunk_document(text=result['text'], doc_type=dt, school_name=name,
                                year=2025, source_url=result['url'],
                                source_name='cau.edu.cn', source_type='official_university',
                                data_source='official', confidence='high')
        stats = index_chunks(chunks)
        print(f"✅ {result['chars']} chars → {stats['inserted']} chunks [{dt}]")
        total += stats['inserted']
        await asyncio.sleep(DELAY)
    
    print(f"\n总计入库: {total} chunks")
    return results

if __name__ == "__main__":
    asyncio.run(main())
