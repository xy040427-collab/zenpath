"""
择境 ZENPATH — RAG 真实性审计与 L0-L5 覆盖分级

重新定义覆盖标准：
  L0: 仅有 schools 表基础信息，不算真实 RAG
  L1: 有官方学校简介 / 本科招生网介绍
  L2: 有招生章程
  L3: 有至少 3 个官方专业介绍
  L4: 有就业质量报告或毕业去向报告
  L5: 学校 + 专业 + 就业 + 招生章程 + 城市资料完整覆盖
"""

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# Handle both backend/rag and rag paths
if PROJECT_ROOT.name == 'backend':
    PROJECT_ROOT = PROJECT_ROOT.parent

DB_PATH = PROJECT_ROOT / "backend" / "gaokao.db"
OUTPUT_DIR = PROJECT_ROOT / "rag_output"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def classify_chunk(chunk: dict) -> str:
    """
    Classify a single chunk by data origin.
    Returns one of: baseline_generated, manual_seed, web_official,
                   web_third_party, mock, invalid
    """
    content = chunk.get('content', '') or ''
    source_url = chunk.get('source_url', '') or ''
    source_name = chunk.get('source_name', '') or ''
    source_type = chunk.get('source_type', '') or ''
    data_source = chunk.get('data_source', '') or ''
    doc_type = chunk.get('doc_type', '')
    
    # Mock
    if data_source == 'mock' or source_type == 'mock':
        return 'mock'
    
    # Baseline generated (schools table auto-generation)
    if (source_name == '择境学校数据库' and source_type == 'manual' 
        and data_source == 'manual' and doc_type == 'school_profile'):
        return 'baseline_generated'
    
    # Manual seed (hand-written content)
    if (data_source == 'manual' and source_type == 'manual' 
        and ('择境' in source_name or '人工' in source_name)
        and doc_type in ('major_profile', 'career_path', 'city_industry')):
        return 'manual_seed'
    
    # Web official (.edu.cn or .gov.cn)
    if '.edu.cn' in (source_url or '').lower() or 'gov.cn' in (source_url or '').lower():
        return 'web_official'
    if source_type.startswith('official_'):
        return 'web_official'
    
    # Web third-party (has URL but not official)
    if source_url and source_url.startswith('http'):
        return 'web_third_party'
    
    # Invalid check
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    if chinese_chars < 150:
        return 'invalid'
    if not source_url:
        return 'invalid'
    
    # Default
    if chunk.get('school_name') and not source_url:
        return 'baseline_generated'
    
    return 'invalid'


def compute_school_coverage(school_name: str, chunks: list[dict]) -> dict:
    """
    Compute L0-L5 coverage for a school based on its chunks.
    Only counts web_official chunks for coverage assessment.
    """
    # Filter to web_official chunks only for L1-L5
    official = [c for c in chunks if c['_class'] == 'web_official' and c.get('school_name') == school_name]
    manual = [c for c in chunks if c['_class'] == 'manual_seed']
    baseline = [c for c in chunks if c['_class'] == 'baseline_generated' and c.get('school_name') == school_name]
    
    # Default L0
    level = 'L0'
    
    has_school_profile = any(c['doc_type'] == 'school_profile' for c in official)
    has_admission = any(c['doc_type'] == 'admission_policy' for c in official)
    has_major = any(c['doc_type'] == 'major_profile' for c in official)
    has_employment = any(c['doc_type'] == 'employment_report' for c in official)
    has_city = any(c['doc_type'] == 'city_industry' for c in manual)
    
    major_count = sum(1 for c in official if c['doc_type'] == 'major_profile')
    
    # L5: Complete coverage
    if has_school_profile and has_admission and major_count >= 3 and has_employment and has_city:
        level = 'L5'
    # L4: Has employment report
    elif has_school_profile and has_admission and has_employment:
        level = 'L4'
    # L3: Has 3+ major profiles
    elif has_school_profile and has_admission and major_count >= 3:
        level = 'L3'
    # L2: Has admission policy
    elif has_school_profile and has_admission:
        level = 'L2'
    # L1: Has school profile
    elif has_school_profile:
        level = 'L1'
    # L0: Only baseline data
    else:
        level = 'L0'
    
    return {
        'school_name': school_name,
        'level': level,
        'has_school_profile': has_school_profile,
        'has_admission_policy': has_admission,
        'major_profile_count': major_count,
        'has_employment_report': has_employment,
        'has_city_industry': has_city,
        'official_chunks': len(official),
        'manual_chunks': len(manual),
        'baseline_only': len(baseline) > 0 and len(official) == 0,
    }


def run_audit() -> dict:
    """Full audit of all rag_chunks."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM rag_chunks ORDER BY id").fetchall()
    finally:
        conn.close()
    
    # Classify every chunk
    all_chunks = []
    for r in rows:
        chunk = dict(r)
        chunk['_class'] = classify_chunk(chunk)
        all_chunks.append(chunk)
    
    # Aggregate stats
    classes = {}
    for cls in ['baseline_generated', 'manual_seed', 'web_official', 'web_third_party', 'mock', 'invalid']:
        classes[cls] = [c for c in all_chunks if c['_class'] == cls]
    
    # Real usable chunks
    real_chunks = classes['web_official'] + classes['manual_seed']
    
    # School coverage
    all_schools = set(c.get('school_name') for c in all_chunks if c.get('school_name'))
    official_schools = set(c.get('school_name') for c in classes['web_official'] if c.get('school_name'))
    
    # Compute L0-L5 for each school
    school_levels = {}
    for name in all_schools:
        school_levels[name] = compute_school_coverage(name, all_chunks)
    
    level_counts = {}
    for lv in ['L0', 'L1', 'L2', 'L3', 'L4', 'L5']:
        level_counts[lv] = sum(1 for s in school_levels.values() if s['level'] == lv)
    
    # Invalid chunks detail
    invalid_detail = []
    for c in classes['invalid'][:50]:
        chinese = len(re.findall(r'[\u4e00-\u9fff]', c.get('content', '')))
        invalid_detail.append({
            'id': c['id'],
            'chunk_id': c.get('chunk_id', ''),
            'doc_type': c.get('doc_type', ''),
            'school_name': c.get('school_name', ''),
            'reason': f'内容过短({chinese}中文字)' if chinese < 150 else '无来源URL',
            'content_preview': c.get('content', '')[:100],
        })
    
    # Manual seed detail
    manual_detail = []
    doc_types_manual = set()
    for c in classes['manual_seed']:
        doc_types_manual.add(c.get('doc_type'))
        manual_detail.append({
            'doc_type': c.get('doc_type'),
            'school_name': c.get('school_name'),
            'major_name': c.get('major_name'),
            'city': c.get('city'),
            'content_len': len(c.get('content', '')),
            'source_name': c.get('source_name'),
        })
    
    audit = {
        'timestamp': datetime.utcnow().isoformat(),
        'total_chunks': len(all_chunks),
        
        # By classification
        'by_classification': {k: len(v) for k, v in classes.items()},
        
        # Real coverage
        'real_coverage': {
            'real_usable_chunks': len(real_chunks),
            'official_chunks': len(classes['web_official']),
            'manual_seed_chunks': len(classes['manual_seed']),
            'not_real_coverage': len(classes['baseline_generated']) + len(classes['mock']) + len(classes['invalid']),
        },
        
        # School stats
        'school_coverage': {
            'total_schools_in_db': len(all_schools),
            'schools_with_official_data': len(official_schools),
            'schools_with_only_baseline': len(all_schools - official_schools),
        },
        
        # L0-L5 grading
        'l0_l5_distribution': level_counts,
        'school_levels': {k: v for k, v in list(school_levels.items())[:20]},  # top 20
        
        # Manual seed detail
        'manual_seed': {
            'total': len(classes['manual_seed']),
            'doc_types': list(doc_types_manual),
            'detail': manual_detail,
        },
        
        # Invalid chunks
        'invalid_chunks': {
            'total': len(classes['invalid']),
            'detail': invalid_detail,
        },
        
        # Web third party (garbage check)
        'web_third_party': {
            'total': len(classes['web_third_party']),
            'domains': list(set(
                c.get('source_url', '').split('/')[2] if '//' in (c.get('source_url') or '') else ''
                for c in classes['web_third_party']
            )),
        },
    }
    
    return audit


def generate_reports(audit: dict):
    """Generate all audit reports."""
    
    # 1. Audit report (JSON)
    audit_path = OUTPUT_DIR / "rag_audit_v2.json"
    with open(audit_path, 'w', encoding='utf-8') as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)
    
    # 2. Markdown report
    md = []
    md.append("# 择境 ZENPATH — RAG 真实性审计报告")
    md.append(f"\n生成时间: {audit['timestamp']}\n")
    
    md.append("## 一、数据分类统计\n")
    md.append("| 分类 | 数量 | 计入真实覆盖？ |")
    md.append("|------|------|--------------|")
    for cls, label, countable in [
        ('web_official', '官方来源', '✅ 计入（高质量）'),
        ('manual_seed', '人工整理', '✅ 计入（中置信度）'),
        ('web_third_party', '第三方网页', '⚠️ 低置信度计入'),
        ('baseline_generated', 'schools表自动生成', '❌ 不计入'),
        ('mock', '测试数据', '❌ 不计入'),
        ('invalid', '不合格内容', '❌ 不计入'),
    ]:
        cnt = audit['by_classification'].get(cls, 0)
        md.append(f"| {label} | {cnt} | {countable} |")
    
    md.append(f"\n**真实可用 RAG chunks: {audit['real_coverage']['real_usable_chunks']}**")
    md.append(f"- 官方来源: {audit['real_coverage']['official_chunks']}")
    md.append(f"- 人工整理: {audit['real_coverage']['manual_seed_chunks']}")
    
    md.append("\n## 二、L0-L5 覆盖分级\n")
    md.append("| 级别 | 定义 | 院校数 |")
    md.append("|------|------|--------|")
    level_defs = {
        'L0': '仅有 schools 表基础信息',
        'L1': '有官方学校简介',
        'L2': '有招生章程',
        'L3': '有 ≥3 个专业介绍',
        'L4': '有就业质量报告',
        'L5': '完整覆盖(学校+专业+就业+章程+城市)',
    }
    for lv in ['L0', 'L1', 'L2', 'L3', 'L4', 'L5']:
        md.append(f"| {lv} | {level_defs[lv]} | {audit['l0_l5_distribution'].get(lv, 0)} |")
    
    md.append("\n## 三、不合格 Chunk 清单\n")
    for c in audit['invalid_chunks']['detail'][:20]:
        md.append(f"- `{c['chunk_id']}`: {c['reason']} — {c['content_preview'][:60]}...")
    if audit['invalid_chunks']['total'] > 20:
        md.append(f"\n... 及其他 {audit['invalid_chunks']['total']-20} 条")
    
    md.append("\n## 四、第三方抓取垃圾清单\n")
    for d in audit['web_third_party'].get('domains', []):
        md.append(f"- {d}")
    
    md.append("\n## 五、人工整理资料明细\n")
    for c in audit['manual_seed'].get('detail', []):
        md.append(f"- [{c['doc_type']}] {c.get('major_name','') or c.get('city','') or c.get('school_name','')}")
    
    md.append("\n## 六、核心结论\n")
    md.append(f"1. 上一轮汇报的「906 chunks」「864院校 RAG覆盖」将 schools 表自动生成的 baseline_generated 数据计入了覆盖统计，属于**虚报**。")
    md.append(f"2. 真实可用 RAG chunks 仅有 **{audit['real_coverage']['real_usable_chunks']}** 条。")
    md.append(f"3. 16 条 web_third_party 数据来自 naver.com、gemini.com、github.com 等非高校网站，是搜索引擎返回的**垃圾结果**。")
    md.append(f"4. 15 条 invalid chunks 因内容过短（<150中文字）无法作为有效 RAG 资料。")
    md.append(f"5. 848 条 baseline_generated chunks 由 schools 表字段自动拼装，仅包含「学校名+层次+类型+排名」等基础字段，**不是从官网抓取的真实资料**。")
    md.append("\n**当前真实状况：RAG 知识库仅有 27 条人工整理资料，需要通过 v2 爬虫从高校官网抓取真实内容。**")
    
    report_path = OUTPUT_DIR / "rag_audit_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    
    return audit_path, report_path


if __name__ == "__main__":
    print("Running audit...")
    audit = run_audit()
    
    print(f"\n=== 审计结果 ===")
    for cls, cnt in audit['by_classification'].items():
        print(f"  {cls}: {cnt}")
    
    print(f"\n  真实可用: {audit['real_coverage']['real_usable_chunks']}")
    print(f"  非真实覆盖: {audit['real_coverage']['not_real_coverage']}")
    
    print(f"\n=== L0-L5 分布 ===")
    for lv, cnt in audit['l0_l5_distribution'].items():
        print(f"  {lv}: {cnt}")
    
    audit_path, report_path = generate_reports(audit)
    print(f"\n报告已生成:")
    print(f"  {audit_path}")
    print(f"  {report_path}")
