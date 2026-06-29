"""
Query Parser — 用户自然语言 → 结构化JSON
Step 8: 用户Query解析
"""

import re
import json
import logging

logger = logging.getLogger(__name__)

# 省份名称映射
PROVINCE_KEYWORDS = {
    '北京': '北京', '天津': '天津', '上海': '上海', '重庆': '重庆',
    '河北': '河北', '山西': '山西', '内蒙古': '内蒙古', '辽宁': '辽宁',
    '吉林': '吉林', '黑龙江': '黑龙江', '江苏': '江苏', '浙江': '浙江',
    '安徽': '安徽', '福建': '福建', '江西': '江西', '山东': '山东',
    '河南': '河南', '湖北': '湖北', '湖南': '湖南', '广东': '广东',
    '广西': '广西', '海南': '海南', '四川': '四川', '贵州': '贵州',
    '云南': '云南', '西藏': '西藏', '陕西': '陕西', '甘肃': '甘肃',
    '青海': '青海', '宁夏': '宁夏', '新疆': '新疆',
}

# 选科关键词 → 标准名称
SUBJECT_MAP = {
    '物理': '物理', '物': '物理',
    '化学': '化学', '化': '化学',
    '生物': '生物', '生': '生物',
    '历史': '历史', '史': '历史',
    '政治': '政治', '思政': '政治', '思想政治': '政治',
    '地理': '地理', '地': '地理',
    '物化生': '物理+化学+生物',
    '物化地': '物理+化学+地理',
    '物化政': '物理+化学+政治',
    '物生地': '物理+生物+地理',
    '物生政': '物理+生物+政治',
    '物地政': '物理+地理+政治',
    '历化生': '历史+化学+生物',
    '历化地': '历史+化学+地理',
    '历化政': '历史+化学+政治',
    '历生地': '历史+生物+地理',
    '历生政': '历史+生物+政治',
    '历地政': '历史+地理+政治',
}

# 专业关键词 → 标准专业名
MAJOR_EXPANSION = {
    '计算机': ['计算机科学与技术', '软件工程', '人工智能', '数据科学与大数据技术', '网络工程', '信息安全', '物联网工程'],
    '软件': ['软件工程', '计算机科学与技术'],
    '人工智能': ['人工智能', '计算机科学与技术', '数据科学与大数据技术', '智能科学与技术'],
    '数据': ['数据科学与大数据技术', '统计学', '计算机科学与技术'],
    '电子': ['电子信息工程', '通信工程', '微电子科学与工程', '光电信息科学与工程', '集成电路设计与集成系统'],
    '通信': ['通信工程', '电子信息工程', '信息工程'],
    '自动化': ['自动化', '电气工程及其自动化', '机器人工程'],
    '电气': ['电气工程及其自动化', '自动化'],
    '机械': ['机械工程', '机械设计制造及其自动化', '车辆工程'],
    '土木': ['土木工程', '建筑环境与能源应用工程', '给排水科学与工程'],
    '建筑': ['建筑学', '城乡规划', '风景园林'],
    '金融': ['金融学', '金融工程', '投资学', '保险学'],
    '会计': ['会计学', '财务管理', '审计学'],
    '法学': ['法学', '知识产权'],
    '医学': ['临床医学', '口腔医学', '医学影像学', '预防医学', '药学'],
    '临床': ['临床医学', '口腔医学'],
    '数学': ['数学与应用数学', '信息与计算科学', '统计学'],
    '物理': ['物理学', '应用物理学'],
    '化学': ['化学', '应用化学', '化学工程与工艺'],
    '英语': ['英语', '翻译'],
    '师范': ['数学与应用数学（师范）', '汉语言文学（师范）', '英语（师范）', '物理学（师范）', '化学（师范）'],
}

# 风险偏好
RISK_MAP = {
    '冲': '冲', '冲刺': '冲', '想冲': '冲', '冲一冲': '冲',
    '稳': '稳', '稳妥': '稳', '稳一点': '稳', '稳当': '稳',
    '保守': '保守', '保底': '保守', '不想滑档': '保守', '安全': '保守',
    '均衡': '均衡', '平衡': '均衡', '随便': '均衡', '都可以': '均衡',
}

# 城市别名/区域扩展
CITY_EXPANSION = {
    '江浙沪': ['上海', '南京', '苏州', '无锡', '杭州', '宁波', '嘉兴', '常州', '镇江', '扬州', '南通', '温州'],
    '长三角': ['上海', '南京', '杭州', '苏州', '宁波', '无锡', '合肥', '常州', '南通', '嘉兴'],
    '北上广': ['北京', '上海', '广州'],
    '北上广深': ['北京', '上海', '广州', '深圳'],
    '珠三角': ['广州', '深圳', '珠海', '佛山', '东莞', '中山'],
    '京津冀': ['北京', '天津', '石家庄', '保定', '唐山'],
    '成渝': ['成都', '重庆'],
    '武汉都市圈': ['武汉', '黄石', '鄂州'],
    '南京都市圈': ['南京', '镇江', '扬州', '马鞍山', '芜湖'],
}


def extract_score_rank(text: str) -> dict:
    """从文本中提取分数和位次"""
    result = {}
    
    # 优先提取位次：xxxx位、位次xxx
    rank_patterns = [
        r'(\d{3,6})\s*位',
        r'位次\s*[约:：]?\s*(\d{3,6})',
        r'排名\s*[约:：]?\s*(\d{3,6})',
        r'第\s*(\d{3,6})\s*名',
    ]
    for pattern in rank_patterns:
        m = re.search(pattern, text)
        if m:
            result['rank'] = int(m.group(1))
            break
    
    # 提取分数：xxx分
    score_patterns = [
        r'(\d{2,3})\s*分',
        r'分数[约为]?(\d{2,3})',
        r'考[了了]?(\d{2,3})\s*分',
        r'(\d{2,3})分[钟散]?(?!钟)',  # 避免"分钟"
    ]
    for pattern in score_patterns:
        m = re.search(pattern, text)
        if m:
            score = int(m.group(1))
            if 100 <= score <= 750:
                result['score'] = score
                break
    
    return result


def extract_province(text: str) -> str | None:
    """提取省份"""
    for name in PROVINCE_KEYWORDS:
        if name in text:
            return PROVINCE_KEYWORDS[name]
    return None


def extract_subjects(text: str) -> list[str]:
    """提取选科"""
    found = []
    # 先检查组合关键词
    for combo_key, combo_val in SUBJECT_MAP.items():
        if combo_key in text and '+' in combo_val:
            found.extend(combo_val.split('+'))
            return found
    
    # 单个科目
    for subj in ['物理', '化学', '生物', '历史', '政治', '地理', '思政', '思想政治']:
        if subj in text and subj not in found:
            standard = SUBJECT_MAP.get(subj, subj)
            if standard not in found:
                found.append(standard)
    
    return found


# 科目关键词（从 SUBJECT_MAP 中提取，避免与专业偏好混淆）
_SUBJECT_KEYWORDS = {'物理', '化学', '生物', '历史', '政治', '地理', '思政', '思想政治',
                     '物化生', '物化地', '物化政', '物生地', '物生政', '物地政',
                     '历化生', '历化地', '历化政', '历生地', '历生政', '历地政'}


def extract_majors(text: str, subjects: list[str] | None = None) -> list[str]:
    """提取并扩展专业偏好（排除科目关键词，避免物理/化学等被误判）"""
    found = set()
    exclude = _SUBJECT_KEYWORDS | (set(subjects) if subjects else set())
    for keyword, expansions in MAJOR_EXPANSION.items():
        if keyword in text and keyword not in exclude:
            for exp in expansions:
                found.add(exp)
    return list(found)


def extract_cities(text: str, province: str | None = None) -> list[str]:
    """提取城市偏好（支持区域扩展），自动排除省份名以免过滤到全量数据"""
    found = set()
    
    # 直接城市名
    for city in ['北京', '上海', '广州', '深圳', '杭州', '南京', '苏州', '成都', '武汉',
                 '天津', '重庆', '西安', '青岛', '济南', '厦门', '大连', '宁波', '长沙',
                 '郑州', '合肥', '沈阳', '哈尔滨', '昆明', '贵阳', '兰州', '福州', '南昌',
                 '无锡', '常州', '徐州', '南通', '烟台', '潍坊', '威海', '淄博', '临沂',
                 '温州', '嘉兴', '绍兴', '金华', '厦门', '珠海', '佛山', '东莞', '惠州',
                 '中山', '江门', '肇庆', '海口', '三亚', '南宁', '桂林', '贵阳']:
        if city in text:
            found.add(city)
    
    # 区域扩展
    for region, cities in CITY_EXPANSION.items():
        if region in text:
            for c in cities:
                found.add(c)
    
    # 排除省份自身（避免"上海考生"→city=["上海"]过滤掉同济复旦等618所非上海命名大学）
    if province:
        # 去掉后缀：上海市→上海, 北京市→北京
        province_short = province.rstrip('省市自治区').replace('壮族','').replace('回族','').replace('维吾尔','')
        found.discard(province)
        found.discard(province_short)
    
    return list(found)


def extract_risk(text: str) -> str:
    """提取风险偏好"""
    # 先判断否定
    has_negation = any(w in text for w in ['不想', '不要', '别'])
    
    for keyword, risk in RISK_MAP.items():
        if keyword in text:
            if has_negation and keyword in ['冲', '冲刺']:
                return '保守'
            return risk
    
    return '均衡'  # 默认


def extract_student_type(text: str) -> str:
    """提取考生类别"""
    if any(w in text for w in ['历史类', '文史', '历史生', '文科']):
        return '历史类'
    elif any(w in text for w in ['物理类', '理工', '物理生', '理科']):
        return '物理类'
    return '普通类'


def parse_query(text: str) -> dict:
    """
    主入口：解析用户自然语言输入为结构化JSON
    
    先用规则兜底提取，后续可用大模型增强。
    """
    if not text or not text.strip():
        return {}
    
    result = {}
    
    result['province'] = extract_province(text)
    
    score_rank = extract_score_rank(text)
    if 'score' in score_rank:
        result['score'] = score_rank['score']
    if 'rank' in score_rank:
        result['rank'] = score_rank['rank']
    
    result['subjects'] = extract_subjects(text)
    result['major_preferences'] = extract_majors(text, result['subjects'])
    result['city_preferences'] = extract_cities(text, result.get('province'))
    result['risk_preference'] = extract_risk(text)
    result['student_type'] = extract_student_type(text)
    
    return result
