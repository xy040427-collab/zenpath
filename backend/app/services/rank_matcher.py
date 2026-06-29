"""
Rank Matcher v3 — 基于距离公式的冲稳保算法

冲: 录取位次 ≤ 用户位次 ÷ 1.20（用户前进20%可达）
稳: 用户位次 × 0.90 ≤ 录取位次 ≤ 用户位次 × 1.10（±10%）
保: 录取位次 ≥ 用户位次 × 1.20（用户领先20%+）

概率公式: probability = 50 - distance × 200, clamp[1,99]
  distance = (user_rank - school_avg_rank) / school_avg_rank
  distance < 0: 用户更优 → 概率更高
  distance > 0: 用户更差 → 概率更低
"""

import logging
import re
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════
#  School name cleaning — shared by all recommenders
# ═══════════════════════════════════════════

_CORRUPT_CHARS = {"苏", "教", "省", "育", "江", "湖"}
_CORRUPT_MULTI = ["省湖"]  # known double-corrupt pairs
_LEGIT_STARTS = {  # two-char starts that share first char with corrupt set
    "苏州", "江苏", "江西", "江南", "江汉", "湖北", "湖南", "教育", "教学",
}

def clean_school_name(raw: str) -> str:
    """Strip corrupt prefixes from school / major-group names.

    Handles single-char (苏教省育江湖) and multi-char (省湖) corrupt prefixes,
    while preserving legitimate starts like 苏州/湖北/江南/教育.
    """
    if not raw or len(raw) < 3:
        return raw

    result = raw

    # Pre-process: strip known multi-char corrupt prefixes
    for prefix in sorted(_CORRUPT_MULTI, key=len, reverse=True):
        if result.startswith(prefix):
            candidate = result[len(prefix):]
            if len(candidate) >= 4 and candidate[:2] not in _LEGIT_STARTS:
                result = candidate
                break

    # Iteratively strip single-char corrupt prefixes
    while True:
        if len(result) < 3:
            break
        if result[0] not in _CORRUPT_CHARS:
            break
        # Don't strip if first 2 chars form a legitimate start
        if len(result) >= 2 and result[:2] in _LEGIT_STARTS:
            break
        candidate = result[1:]
        if len(candidate) < 3:
            break
        # Accept only if the candidate looks like a school / group name
        if re.search(r"(大学|学院|学校)", candidate):
            result = candidate
        else:
            break

    return result


# ═══════════════════════════════════════════════
# 分数→位次 查询
# ═══════════════════════════════════════════════

async def query_rank_from_score(
    db: AsyncSession, province: str, year: int,
    score: int, subject_type: str = '全体',
) -> Optional[int]:
    for y in [year, 2025, 2024, 2023, 2022]:
        result = await db.execute(
            text("""
                SELECT rank FROM score_rank_table
                WHERE province=:p AND year=:y AND score=:s AND subject_type=:st LIMIT 1
            """), {'p': province, 'y': y, 's': score, 'st': subject_type})
        row = result.fetchone()
        if row: return row[0]
    return None


# ═══════════════════════════════════════════════
# 城市学校过滤
# ═══════════════════════════════════════════════

async def get_city_schools(
    db: AsyncSession, province: str, city_keywords: list[str], max_schools: int = 500,
) -> list[str]:
    names = set()
    for city in city_keywords:
        result = await db.execute(
            text(f"""SELECT DISTINCT university_name FROM admission_lines
                WHERE province=:p AND (university_name LIKE :c1 OR university_name LIKE :c2)
                LIMIT {max_schools}"""),
            {'p': province, 'c1': f'{city}%', 'c2': f'%{city}%'})
        for row in result.fetchall():
            names.add(clean_school_name(row[0] or ''))
    return list(names)


# ═══════════════════════════════════════════════
# 投档数据查询
# ═══════════════════════════════════════════════

async def get_admission_data(
    db: AsyncSession, province: str, years: list[int],
    school_names: list[str] | None = None,
    major_keywords: list[str] | None = None,
    max_results: int = 5000,
) -> list[dict]:
    conditions = ["province=:p", f"year IN ({','.join(str(y) for y in years)})",
                  "min_rank>0"]
    params = {'p': province}
    if school_names:
        school_conds = []
        for i, n in enumerate(school_names):
            params[f's{i}'] = n
            school_conds.append(f"university_name=:s{i}")
        conditions.append('(' + ' OR '.join(school_conds) + ')')
    if major_keywords:
        major_conds = []
        for i, kw in enumerate(major_keywords):
            params[f'm{i}'] = f'%{kw}%'
            major_conds.append(f"major_group_name LIKE :m{i}")
        conditions.append('(' + ' OR '.join(major_conds) + ')')
    where = ' AND '.join(conditions)
    result = await db.execute(text(f"""
        SELECT year, university_name, major_group_name,
               CAST(min_rank AS INTEGER), CAST(min_score AS INTEGER), CAST(plan_count AS INTEGER)
        FROM admission_lines WHERE {where}
        ORDER BY university_name, major_group_name, year DESC LIMIT {max_results}
    """), params)
    return [{'year': r[0], 'school_name': clean_school_name(r[1] or ''), 'major_name': clean_school_name(r[2] or ''),
             'min_rank': r[3], 'min_score': r[4], 'plan_count': r[5] or 0}
            for r in result.fetchall()]


# ═══════════════════════════════════════════════
# 城市 + 专业相关性
# ═══════════════════════════════════════════════

_CITIES = sorted([
    '哈尔滨','呼和浩特','乌鲁木齐','石家庄','连云港','张家口','秦皇岛',
    '北京','上海','天津','重庆',
    '南京','苏州','无锡','常州','镇江','扬州','南通','徐州','泰州','盐城','淮安','宿迁',
    '杭州','宁波','温州','嘉兴','湖州','绍兴','金华','台州','舟山','丽水','衢州',
    '合肥','芜湖','蚌埠','马鞍山','安庆',
    '广州','深圳','珠海','佛山','东莞','中山','惠州','江门','肇庆',
    '武汉','黄石','宜昌','襄阳','荆州','十堰','孝感','黄冈','咸宁','鄂州',
    '成都','绵阳','德阳','宜宾','南充','泸州',
    '西安','咸阳','宝鸡','渭南','长沙','株洲','湘潭','衡阳','岳阳',
    '郑州','开封','洛阳','新乡','安阳','南阳','信阳','焦作',
    '济南','青岛','烟台','威海','潍坊','淄博','临沂','济宁','泰安','日照','聊城','德州','菏泽','滨州','东营','枣庄',
    '大连','沈阳','鞍山','抚顺','锦州','营口',
    '厦门','福州','泉州','漳州','莆田','龙岩','三明',
    '昆明','曲靖','玉溪','贵阳','遵义','南宁','桂林','柳州','海口','三亚',
    '兰州','天水','拉萨','南昌','赣州','九江','景德镇','吉安',
    '银川','石嘴山','西宁','太原','大同','长治','临汾','长春','吉林',
], key=len, reverse=True)

def detect_city(school_name: str) -> str:
    if not school_name: return ''
    for c in _CITIES:
        if school_name.startswith(c): return c
    for c in _CITIES:
        if c in school_name: return c
    return ''

def compute_relevance(major_name: str, major_prefs: list[str]) -> int:
    """专业相关性 0-100: 真正匹配给高分，不匹配给低分"""
    if not major_name or not major_prefs: return 50
    for pref in major_prefs:
        if pref in major_name or major_name in pref:
            return 100  # 精确匹配
    # 关键词命中数
    hits = sum(1 for pref in major_prefs
               for kw in [pref[:3], pref[:2]]
               if len(kw) >= 2 and kw in major_name)
    if hits >= 2: return 80
    if hits == 1: return 60
    # 大类匹配
    categories = {
        '计算机': ['计算机','软件','人工智能','数据','网络','信息','物联网'],
        '电子通信': ['电子','通信','微电子','光电','集成电路'],
        '医学': ['临床','口腔','医学','药学','护理'],
        '金融经济': ['金融','经济','财政','保险','会计','财务'],
        '法学': ['法学','知识产权'],
        '机械': ['机械','车辆','工业设计'],
        '土木建筑': ['土木','建筑','城乡规划','风景园林'],
    }
    pref_cats = set()
    for cat, kws in categories.items():
        if any(kw in ' '.join(major_prefs) for kw in kws):
            pref_cats.add(cat)
    major_cats = set()
    for cat, kws in categories.items():
        if any(kw in major_name for kw in kws):
            major_cats.add(cat)
    if pref_cats & major_cats: return 40
    return 10  # 不相关


# ═══════════════════════════════════════════════
# 核心：距离公式冲稳保算法
# ═══════════════════════════════════════════════

def compute_risk(user_rank: int, historical_ranks: list[int]) -> dict:
    """
    冲: 学校比用户强15%+ → avg < user_rank × 0.85（需前进15%以上）
    稳: 位次接近 → user_rank × 0.85 ≤ avg ≤ user_rank × 1.20
    保: 用户领先20%+ 且不超3倍 → user_rank × 1.20 ≤ avg ≤ user_rank × 3.00
    过保: 学校层次过低 → avg > user_rank × 3.00（自动过滤）

    概率: prob = clamp(50 - distance × 200, 1, 99)
          distance = (user_rank - avg) / avg
    """
    valid = sorted([r for r in historical_ranks if r > 0])
    if not valid:
        return {'risk_level': '数据不足', 'probability': 0,
                'years_admitted': 0, 'total_years': 0,
                'reason': '暂无历史录取位次数据。'}

    n = len(valid)
    best = valid[0]
    worst = valid[-1]
    avg = sum(valid) / n

    # 距离: 负=用户更优, 正=用户更差
    distance = (user_rank - avg) / avg if avg > 0 else 0
    prob = max(1, min(99, int(50 - distance * 200)))

    # ── 新冲稳保判定 ──
    rush_cutoff = user_rank * 0.85     # 冲上限: 学校比用户强15%+
    stable_low = user_rank * 0.85      # 稳下限
    stable_high = user_rank * 1.20     # 稳上限
    safe_low = user_rank * 1.20        # 保下限: 用户领先20%+
    safe_high = user_rank * 3.00       # 保上限: 不超过用户3倍（过滤垃圾学校）

    years_admitted = sum(1 for r in valid if user_rank <= r)

    if avg > safe_high:
        # 学校层次远低于用户 → 过保，标记但不推荐
        risk = '过保'
        reason = (f'该校录取均位{int(avg)}远超你的位次{user_rank}，'
                  f'层次差距过大，不建议填报。')
    elif avg >= safe_low:
        risk = '保'
        reason = (f'近{n}年录取均位{int(avg)}，你领先{int((avg-user_rank)/avg*100)}%，'
                  f'录取概率{prob}%。')
    elif stable_low <= avg <= stable_high:
        risk = '稳'
        direction = '领先' if user_rank < avg else '落后'
        gap_pct = abs(int((user_rank - avg) / avg * 100))
        reason = (f'近{n}年录取均位{int(avg)}，你{direction}{gap_pct}%，'
                  f'录取概率{prob}%。')
    elif avg < rush_cutoff:
        risk = '冲'
        need = int((user_rank / avg - 1) * 100)
        reason = (f'近{n}年录取均位{int(avg)}，你需前进{need}%({int(user_rank - avg)}位)，'
                  f'录取概率{prob}%，可冲刺。')
    else:
        # 介于 rush_cutoff 和 stable_low 之间（按理不会到这里，兜底）
        risk = '冲'
        need = int((user_rank / avg - 1) * 100)
        reason = (f'近{n}年录取均位{int(avg)}，差距{need}%，录取概率{prob}%。')

    return {
        'risk_level': risk, 'probability': prob,
        'years_admitted': years_admitted, 'total_years': n,
        'best_rank': best, 'worst_rank': worst, 'avg_rank': int(avg),
        'reason': reason,
    }


# ═══════════════════════════════════════════════
# 推荐计算主函数
# ═══════════════════════════════════════════════

async def compute_recommendations(
    db: AsyncSession, province: str, user_rank: int,
    major_preferences: list[str] | None = None,
    city_preferences: list[str] | None = None,
    years: list[int] | None = None,
) -> list[dict]:
    if years is None:
        years = [2025, 2024, 2023]

    # 专业关键词
    major_keywords = None
    if major_preferences:
        kws = set()
        for m in major_preferences:
            for chunk in [m[:3], m[:2]]:
                if len(chunk) >= 2: kws.add(chunk)
        for short in ['计算机','软件','电子','通信','自动化','电气','土木',
                      '金融','会计','法学','临床','数学','物理','化学',
                      '机械','建筑','数据','人工智能','网络','信息安全']:
            if any(short in m for m in major_preferences): kws.add(short)
        major_keywords = list(kws)

    # 城市学校
    school_names = None
    if city_preferences:
        school_names = await get_city_schools(db, province, city_preferences)

    # ── 内部函数：从原始数据计算推荐 ──
    from collections import defaultdict
    
    def _build_recs(raw_data: list[dict]) -> list[dict]:
        grouped = defaultdict(list)
        for item in raw_data:
            key = f"{item['school_name']}|{item['major_name']}"
            grouped[key].append(item)
        results = []
        for key, points in grouped.items():
            school_name, major_name = key.split('|', 1)
            ranks = [d['min_rank'] for d in points if d['min_rank'] > 0]
            if not ranks: continue
            risk = compute_risk(user_rank, ranks)
            if risk['risk_level'] in ('数据不足', '过保'): continue
            relevance = compute_relevance(major_name, major_preferences or [])
            city = detect_city(school_name)
            is_sf = '中外合作' in major_name
            latest = points[0]
            by_year = sorted([(p['year'], p['min_rank']) for p in points], key=lambda x: x[0])
            trend = 'stable'
            if len(by_year) >= 2:
                trend = 'harder' if by_year[-1][1] < by_year[0][1] else 'easier'
            results.append({
                'school_name': school_name, 'major_name': major_name,
                'city': city, 'risk_level': risk['risk_level'],
                'probability': risk['probability'], 'years_admitted': risk['years_admitted'],
                'total_years': risk['total_years'], 'major_relevance': relevance,
                'is_sino_foreign': is_sf, 'admission_trend': trend,
                'rank_analysis': {'user_rank': user_rank, 'best_year_rank': risk['best_rank'],
                    'worst_year_rank': risk['worst_rank'], 'avg_rank': risk['avg_rank'],
                    'historical_ranks': sorted(ranks), 'rank_margin': risk['worst_rank'] - user_rank},
                'algorithm_reason': risk['reason'],
                'latest_min_rank': latest['min_rank'], 'latest_min_score': latest['min_score'],
                'latest_year': latest['year'], 'plan_count': latest.get('plan_count', 0),
                'data_years': len(ranks),
            })
        return results

    # ── 查投档数据（带专业过滤 + 智能回退） ──
    # 回退场景1：major_group_name 为空 → 返回0行
    # 回退场景2：major_group_name 是编码（"同济大学(01)"）→ 匹配到的全是低层次学校，全被标"过保"
    data = await get_admission_data(
        db=db, province=province, years=years,
        school_names=school_names, major_keywords=major_keywords)
    recs = _build_recs(data) if data else []

    if not recs and major_keywords:
        logger.info(f"{province}: major filter yielded 0 valid recs, retrying without")
        data = await get_admission_data(
            db=db, province=province, years=years,
            school_names=school_names, major_keywords=None)
        recs = _build_recs(data) if data else []

    # ── 查询学校 slug（用于校徽） ──
    if recs:
        unique_schools = set(r['school_name'] for r in recs)
        # Also collect parent-school names for branch campus fallback
        parent_names = set()
        for name in unique_schools:
            # Strip campus suffixes: 中国人民大学苏州校区 → 中国人民大学
            parent = re.sub(r'[（(][^）)]*[）)]', '', name)   # remove parenthetical like （苏州）
            parent = re.sub(r'[^-]校区$', '', parent)         # remove trailing 校区
            parent = parent.strip()
            if parent != name:
                parent_names.add(parent)
        all_names = unique_schools | parent_names

        slug_map = {}
        if all_names:
            school_result = await db.execute(
                text(f"SELECT name, COALESCE(logo_slug, slug) as display_slug FROM schools WHERE name IN ({','.join(':n'+str(i) for i in range(len(all_names)))})"),
                {f'n{i}': name for i, name in enumerate(all_names)}
            )
            for row in school_result.fetchall():
                slug_map[row[0]] = row[1] or ''

        for r in recs:
            slug = slug_map.get(r['school_name'], '')
            if not slug:
                # Fallback: try parent school name
                parent = re.sub(r'[（(][^）)]*[）)]', '', r['school_name'])
                parent = re.sub(r'[^-]校区$', '', parent).strip()
                if parent != r['school_name']:
                    slug = slug_map.get(parent, '')
            r['school_slug'] = slug

    # 排序：保→稳→冲，同等级按相关性+概率
    risk_order = {'保': 0, '稳': 1, '冲': 2}
    recs.sort(key=lambda x: (
        risk_order.get(x['risk_level'], 9),
        -x['major_relevance'],
        -x['probability'],
    ))
    return recs
