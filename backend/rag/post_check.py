"""
Post-check validator — validates AI-generated explanations for rule violations.

Must catch:
- Absolute promises (保证录取, 一定能上, 100%稳, etc.)
- Fabricated scores/ranks/plans
- Modified risk levels
- Non-existent source citations
- Mock/manual data presented as official
- Province policy confusion
"""
import re

FORBIDDEN_PATTERNS = [
    (r'保证录取', '出现了绝对化承诺"保证录取"'),
    (r'一定能上', '出现了绝对化承诺"一定能上"'),
    (r'100%稳', '出现了绝对化承诺"100%稳"'),
    (r'绝对安全', '出现了绝对化承诺"绝对安全"'),
    (r'不会滑档', '出现了绝对化承诺"不会滑档"'),
    (r'必录', '出现了绝对化承诺"必录"'),
    (r'稳赚', '出现了绝对化承诺"稳赚"'),
    (r'稳如', '出现了绝对化表述'),
]


def validate_ai_explanation(
    text: str,
    recommendation: dict,
    evidences: list[dict],
) -> dict:
    """Validate AI-generated explanation. Returns {valid: bool, issues: [...]}."""
    issues = []

    # Check forbidden patterns
    for pattern, msg in FORBIDDEN_PATTERNS:
        if re.search(pattern, text):
            issues.append({'severity': 'error', 'message': msg})

    # Check for fabricated scores (numbers not in recommendation)
    actual_min_score = recommendation.get('latest_min_score')
    actual_min_rank = recommendation.get('latest_min_rank')
    actual_risk = recommendation.get('risk_level')

    # Check fabricated scores
    score_pattern = re.compile(r'(\d{3})\s*分')
    for match in score_pattern.finditer(text):
        fake_score = int(match.group(1))
        if actual_min_score and 300 < fake_score < 900:
            if abs(fake_score - actual_min_score) > 2:
                issues.append({
                    'severity': 'warning',
                    'message': f'解释中出现了分数{fake_score}分，与推荐结果中的{actual_min_score}分不一致'
                })

    # Check fabricated ranks
    rank_pattern = re.compile(r'位次\s*(\d{4,6})|排名\s*(\d{4,6})')
    for match in rank_pattern.finditer(text):
        fake_rank = int(match.group(1) or match.group(2))
        if actual_min_rank and abs(fake_rank - actual_min_rank) > 100:
            issues.append({
                'severity': 'warning',
                'message': f'解释中出现了位次{fake_rank}，与推荐结果中的{actual_min_rank}不一致'
            })

    # Check risk level consistency
    risk_labels = {
        '保': ['保底', '保', '把握极大'],
        '稳': ['稳妥', '稳', '匹配'],
        '冲': ['冲刺', '冲', '挑战'],
    }
    if actual_risk in risk_labels:
        expected_terms = risk_labels[actual_risk]
        if not any(term in text for term in expected_terms):
            issues.append({
                'severity': 'warning',
                'message': f'解释中未体现{actual_risk}的风险等级特征'
            })

    # Check mock data presented as official
    for ev in evidences:
        if ev.get('data_source') == 'mock' and ev.get('source_name') in text:
            issues.append({
                'severity': 'error',
                'message': f'引用了mock数据源 {ev["source_name"]}，不应出现在AI解释中'
            })

    return {
        'valid': not any(i['severity'] == 'error' for i in issues),
        'issues': issues,
        'has_warnings': len(issues) > 0,
    }
