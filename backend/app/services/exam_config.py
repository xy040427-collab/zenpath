"""
省份考试类型配置
不同省份的高考模式不同，影响选科解析和位次查询
"""

# 各省份考试模式
PROVINCE_EXAM_CONFIG = {
    # 3+3 模式：语数外+物化生政史地任选3
    '北京': {'mode': '3+3', 'total_score': 750, 'subject_pool': ['物理', '化学', '生物', '历史', '政治', '地理']},
    '天津': {'mode': '3+3', 'total_score': 750, 'subject_pool': ['物理', '化学', '生物', '历史', '政治', '地理']},
    '上海': {'mode': '3+3', 'total_score': 660, 'subject_pool': ['物理', '化学', '生物', '历史', '政治', '地理']},
    '浙江': {'mode': '3+3', 'total_score': 750, 'subject_pool': ['物理', '化学', '生物', '历史', '政治', '地理', '技术']},
    '山东': {'mode': '3+3', 'total_score': 750, 'subject_pool': ['物理', '化学', '生物', '历史', '政治', '地理']},
    '海南': {'mode': '3+3', 'total_score': 900, 'subject_pool': ['物理', '化学', '生物', '历史', '政治', '地理']},

    # 3+1+2 模式：语数外+物理/历史二选一+政地化生任选2
    '河北': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '辽宁': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '江苏': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '福建': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '湖北': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '湖南': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '广东': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '重庆': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '吉林': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '黑龙江': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '安徽': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '江西': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '广西': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '贵州': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},
    '甘肃': {'mode': '3+1+2', 'total_score': 750, 'primary_subjects': ['物理', '历史']},

    # 传统文理分科
    '山西': {'mode': 'traditional', 'total_score': 750, 'streams': ['理科', '文科']},
    '内蒙古': {'mode': 'traditional', 'total_score': 750, 'streams': ['理科', '文科']},
    '河南': {'mode': 'traditional', 'total_score': 750, 'streams': ['理科', '文科']},
    '四川': {'mode': 'traditional', 'total_score': 750, 'streams': ['理科', '文科']},
    '云南': {'mode': 'traditional', 'total_score': 750, 'streams': ['理科', '文科']},
    '西藏': {'mode': 'traditional', 'total_score': 750, 'streams': ['理科', '文科']},
    '陕西': {'mode': 'traditional', 'total_score': 750, 'streams': ['理科', '文科']},
    '青海': {'mode': 'traditional', 'total_score': 750, 'streams': ['理科', '文科']},
    '宁夏': {'mode': 'traditional', 'total_score': 750, 'streams': ['理科', '文科']},
    '新疆': {'mode': 'traditional', 'total_score': 750, 'streams': ['理科', '文科']},
}


def get_exam_config(province: str) -> dict:
    """获取省份考试配置"""
    return PROVINCE_EXAM_CONFIG.get(province, {'mode': '3+3', 'total_score': 750})


def get_subject_type_for_rank_lookup(province: str, subjects: list[str]) -> str:
    """
    根据省份考试模式和选科，确定查询一分一段表应使用的subject_type
    """
    config = get_exam_config(province)
    mode = config.get('mode', '3+3')
    
    if mode == '3+3':
        # 山东模式：全体排名即可（subject_type='全体'）
        return '全体'
    elif mode == '3+1+2':
        # 区分物理类/历史类
        if '物理' in subjects:
            return '物理'
        elif '历史' in subjects:
            return '历史'
        return '物理'  # 默认物理类
    elif mode == 'traditional':
        # 区分理科/文科
        if '物理' in subjects or '化学' in subjects or '生物' in subjects:
            return '理科'
        return '文科'
    
    return '全体'


def get_subject_type_for_admission(province: str, subjects: list[str]) -> str:
    """
    确定查询投档线时应使用的subject_type
    """
    config = get_exam_config(province)
    mode = config.get('mode', '3+3')
    
    if mode == '3+1+2':
        if '物理' in subjects:
            return 'physics'
        elif '历史' in subjects:
            return 'history'
        return 'physics'
    
    return 'physics'  # 默认
