"""
Post-Check — 结果校验 + 安全过滤
Step 17: Post-check
Step 21: Security (部分)
"""

import logging
import re

logger = logging.getLogger(__name__)

# 禁止词列表
FORBIDDEN_PHRASES = [
    '一定能上', '保证录取', '100%稳', '绝对安全',
    '不会滑档', '稳赚', '必录', '包录取', '绝对能上',
    '稳上', '保证能上', '肯定能上',
]

# 警告词（需要提醒但不拦截）
WARNING_PHRASES = [
    '稳妥推荐', '强烈推荐', '最优选择',
]


def check_explanation_safety(explanation: str) -> list[str]:
    """
    检查解释文本是否安全
    返回警告列表
    """
    warnings = []
    
    for phrase in FORBIDDEN_PHRASES:
        if phrase in explanation:
            warnings.append(f"包含禁止词「{phrase}」")
    
    return warnings


def check_recommendation_validity(
    recommendation: dict,
    user_rank: int,
    user_subjects: list[str] = None,
) -> list[str]:
    """
    检查推荐结果的有效性
    """
    warnings = []
    
    rank_analysis = recommendation.get('rank_analysis', {})
    
    # 位次检查
    if rank_analysis:
        avg_rank = rank_analysis.get('avg_min_rank', 0)
        user_rank_val = rank_analysis.get('user_rank', 0)
        if avg_rank > 0 and user_rank_val > 0:
            # 检查冲稳保是否说反
            risk_level = recommendation.get('risk_level', '')
            if user_rank_val < avg_rank and risk_level == '高风险':
                warnings.append(f"用户位次({user_rank_val})优于平均位次({avg_rank})，但被标记为高风险，请检查")
            elif user_rank_val > avg_rank * 1.1 and risk_level == '保':
                warnings.append(f"用户位次({user_rank_val})落后于平均位次({avg_rank})，但被标记为保底，请检查")
    
    return warnings


def sanitize_explanation(explanation: str) -> str:
    """清洗解释文本，替换禁止词"""
    for phrase in FORBIDDEN_PHRASES:
        explanation = explanation.replace(phrase, '【已过滤】')
    return explanation


async def post_check_verify(
    profile: dict,
    recommendation: dict,
    explanation: str,
) -> dict:
    """
    完整后检查流程
    返回检查结果：
    - passed: bool
    - warnings: list[str]
    - sanitized_explanation: str
    """
    warnings = []
    
    # 1. 检查解释安全性
    safety_warnings = check_explanation_safety(explanation)
    warnings.extend(safety_warnings)
    
    # 2. 检查推荐有效性
    validity_warnings = check_recommendation_validity(
        recommendation,
        profile.get('rank', 0),
        profile.get('subjects'),
    )
    warnings.extend(validity_warnings)
    
    # 3. 清洗
    clean_explanation = sanitize_explanation(explanation)
    
    return {
        'passed': len(warnings) == 0,
        'warnings': warnings,
        'sanitized_explanation': clean_explanation,
    }
