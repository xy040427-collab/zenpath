"""
Preference Matcher v2 — 专业扩展 + 风险策略 + 结果过滤

专业相关性评分已移至 rank_matcher.py 的 compute_major_relevance()
本模块负责：专业偏好扩展、结果按策略分配
"""

import logging

logger = logging.getLogger(__name__)

# ── 专业相似度映射（用于扩展用户偏好） ──

MAJOR_SIMILARITY_MAP = {
    '计算机科学与技术': ['软件工程', '人工智能', '数据科学与大数据技术',
                         '网络工程', '信息安全', '物联网工程', '数字媒体技术', '智能科学与技术'],
    '软件工程': ['计算机科学与技术', '人工智能', '数据科学与大数据技术'],
    '人工智能': ['计算机科学与技术', '数据科学与大数据技术', '智能科学与技术',
                '机器人工程', '自动化'],
    '数据科学与大数据技术': ['统计学', '计算机科学与技术', '人工智能', '信息与计算科学'],
    '电子信息工程': ['通信工程', '电子科学与技术', '微电子科学与工程', '光电信息科学与工程',
                    '集成电路设计与集成系统'],
    '通信工程': ['电子信息工程', '信息工程', '电子科学与技术'],
    '自动化': ['电气工程及其自动化', '机器人工程', '测控技术与仪器'],
    '电气工程及其自动化': ['自动化', '智能电网信息工程'],
    '机械工程': ['机械设计制造及其自动化', '车辆工程', '工业设计', '机械电子工程'],
    '临床医学': ['口腔医学', '医学影像学', '麻醉学', '儿科学'],
    '金融学': ['金融工程', '投资学', '保险学', '经济学', '国际经济与贸易'],
    '会计学': ['财务管理', '审计学', '资产评估'],
    '法学': ['知识产权', '政治学与行政学'],
    '数学与应用数学': ['统计学', '数据科学与大数据技术', '信息与计算科学'],
    '土木工程': ['建筑环境与能源应用工程', '给排水科学与工程', '道路桥梁与渡河工程'],
    '建筑学': ['城乡规划', '风景园林'],
}


def expand_major_preferences(major_prefs: list[str]) -> list[str]:
    """扩展专业偏好 — 添加相关专业"""
    expanded = set(major_prefs)
    for pref in major_prefs:
        if pref in MAJOR_SIMILARITY_MAP:
            for related in MAJOR_SIMILARITY_MAP[pref]:
                expanded.add(related)
    return list(expanded)


def filter_and_strategize(
    recommendations: list[dict],
    risk_preference: str = '均衡',
    max_total: int = 30,
) -> list[dict]:
    """
    按风险偏好策略过滤和分配推荐结果

    策略：
    - 冲：各等级均衡，允许"冲"占主导
    - 稳/保守：减少"冲"，增加"保"和"稳"
    - 均衡：默认分配

    每个等级内部按 major_relevance + probability 排序
    """
    if not recommendations:
        return []

    # 分组
    by_risk = {'保': [], '稳': [], '冲': []}
    for r in recommendations:
        rl = r.get('risk_level', '冲')
        if rl in by_risk:
            by_risk[rl].append(r)

    # 策略目标
    strategies = {
        '冲':   {'保': 5, '稳': 8, '冲': 12},
        '均衡': {'保': 8, '稳': 8, '冲': 8},
        '稳':   {'保': 10, '稳': 10, '冲': 4},
        '保守': {'保': 14, '稳': 6, '冲': 2},
    }

    targets = strategies.get(risk_preference, strategies['均衡'])
    result = []
    used_keys = set()

    for risk_level in ['保', '稳', '冲']:
        target = targets.get(risk_level, 0)
        items = by_risk.get(risk_level, [])
        # 组内排序：专业相关性 > 概率
        items.sort(key=lambda x: (-x.get('major_relevance', 0), -x.get('probability', 0)))
        for item in items:
            key = f"{item['school_name']}|{item['major_name']}"
            if key not in used_keys and len([r for r in result if r.get('risk_level') == risk_level]) < target:
                result.append(item)
                used_keys.add(key)

    # 如果某等级不够，用其他等级补充
    remaining = [r for r in recommendations
                 if f"{r['school_name']}|{r['major_name']}" not in used_keys]
    remaining.sort(key=lambda x: (-x.get('major_relevance', 0), -x.get('probability', 0)))

    # 填满到 max_total
    for item in remaining:
        if len(result) >= max_total:
            break
        key = f"{item['school_name']}|{item['major_name']}"
        if key not in used_keys:
            result.append(item)
            used_keys.add(key)

    return result[:max_total]
