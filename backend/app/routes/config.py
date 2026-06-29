"""Configuration endpoints for supported provinces, subject types, batches, and form schema."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/config", tags=["Config"])

# ── Hardcoded MVP data (focus on 广东省 first) ──────────────────────────────

PROVINCES = [
    {
        "id": "gd",
        "name": "广东省",
        "name_en": "Guangdong",
        "gaokao_type": "3+1+2",  # New gaokao reform
        "total_score": 750,
        "subject_types": ["physics", "history"],
        "batches": ["early", "undergraduate", "vocational"],
        "year": 2026,
    },
    {
        "id": "bj",
        "name": "北京市",
        "name_en": "Beijing",
        "gaokao_type": "3+3",
        "total_score": 750,
        "subject_types": ["physics", "history", "politics", "geography", "chemistry", "biology"],
        "batches": ["early_a", "early_b", "undergraduate", "vocational"],
        "year": 2026,
    },
    {
        "id": "sh",
        "name": "上海市",
        "name_en": "Shanghai",
        "gaokao_type": "3+3",
        "total_score": 660,
        "subject_types": ["physics", "history", "politics", "geography", "chemistry", "biology"],
        "batches": ["early", "undergraduate", "vocational"],
        "year": 2026,
    },
]

SUBJECT_TYPES = [
    {
        "id": "physics",
        "name": "物理类",
        "name_en": "Physics Stream",
        "description": "首选科目为物理，适合理工类专业方向",
        "eligible_majors": "理工类、医学类、经管类等大部分专业",
    },
    {
        "id": "history",
        "name": "历史类",
        "name_en": "History Stream",
        "description": "首选科目为历史，适合文史类专业方向",
        "eligible_majors": "文史类、法学类、教育类等专业",
    },
]

BATCHES = [
    {
        "id": "early",
        "name": "提前批",
        "name_en": "Early Admission",
        "order": 1,
        "description": "军队、公安、消防、航海、小语种、公费师范生等特殊类型招生",
        "max_choices": 2,
    },
    {
        "id": "undergraduate",
        "name": "本科批",
        "name_en": "Undergraduate Batch",
        "order": 2,
        "description": "普通本科院校及专业招生",
        "max_choices": 45,
    },
    {
        "id": "vocational",
        "name": "专科批",
        "name_en": "Vocational Batch",
        "order": 3,
        "description": "高职（专科）院校及专业招生",
        "max_choices": 45,
    },
]

# Dynamic form schema — defines which fields appear and their validation rules
FORM_SCHEMA = {
    "version": "1.0.0",
    "sections": [
        {
            "id": "personal_info",
            "title": "个人信息",
            "fields": [
                {
                    "key": "name",
                    "label": "考生姓名",
                    "type": "text",
                    "required": True,
                    "placeholder": "请输入姓名",
                    "validation": {"min_length": 1, "max_length": 20},
                },
                {
                    "key": "gender",
                    "label": "性别",
                    "type": "select",
                    "required": True,
                    "options": [
                        {"value": "male", "label": "男"},
                        {"value": "female", "label": "女"},
                    ],
                },
                {
                    "key": "id_number",
                    "label": "身份证号",
                    "type": "text",
                    "required": True,
                    "placeholder": "请输入18位身份证号",
                    "validation": {"pattern": "^\\d{17}[\\dXx]$", "length": 18},
                },
                {
                    "key": "phone",
                    "label": "手机号码",
                    "type": "text",
                    "required": True,
                    "placeholder": "请输入手机号",
                    "validation": {"pattern": "^1[3-9]\\d{9}$", "length": 11},
                },
            ],
        },
        {
            "id": "exam_info",
            "title": "考试信息",
            "fields": [
                {
                    "key": "province",
                    "label": "省份",
                    "type": "select",
                    "required": True,
                    "options": [
                        {"value": "gd", "label": "广东省"},
                        {"value": "bj", "label": "北京市"},
                        {"value": "sh", "label": "上海市"},
                    ],
                },
                {
                    "key": "subject_type",
                    "label": "首选科目",
                    "type": "select",
                    "required": True,
                    "options": [
                        {"value": "physics", "label": "物理类"},
                        {"value": "history", "label": "历史类"},
                    ],
                },
                {
                    "key": "score",
                    "label": "高考总分",
                    "type": "number",
                    "required": True,
                    "placeholder": "请输入高考分数",
                    "validation": {"min": 0, "max": 750},
                },
                {
                    "key": "rank",
                    "label": "全省位次",
                    "type": "number",
                    "required": True,
                    "placeholder": "请输入全省排名",
                    "validation": {"min": 1},
                },
                {
                    "key": "year",
                    "label": "高考年份",
                    "type": "select",
                    "required": True,
                    "options": [
                        {"value": "2026", "label": "2026年"},
                        {"value": "2025", "label": "2025年"},
                        {"value": "2024", "label": "2024年"},
                    ],
                },
            ],
        },
        {
            "id": "preferences",
            "title": "志愿偏好",
            "fields": [
                {
                    "key": "preferred_provinces",
                    "label": "意向省份",
                    "type": "multi_select",
                    "required": False,
                    "description": "可多选，不选则不限省份",
                    "options": [
                        {"value": "gd", "label": "广东省"},
                        {"value": "bj", "label": "北京市"},
                        {"value": "sh", "label": "上海市"},
                        {"value": "zj", "label": "浙江省"},
                        {"value": "js", "label": "江苏省"},
                    ],
                },
                {
                    "key": "preferred_major_categories",
                    "label": "意向专业类别",
                    "type": "multi_select",
                    "required": False,
                    "description": "可多选，不选则不限专业",
                    "options": [
                        {"value": "engineering", "label": "工学"},
                        {"value": "science", "label": "理学"},
                        {"value": "medicine", "label": "医学"},
                        {"value": "liberal_arts", "label": "文史哲"},
                        {"value": "law", "label": "法学"},
                        {"value": "economics", "label": "经济学"},
                        {"value": "management", "label": "管理学"},
                        {"value": "education", "label": "教育学"},
                        {"value": "agriculture", "label": "农学"},
                        {"value": "art", "label": "艺术学"},
                    ],
                },
                {
                    "key": "priority",
                    "label": "填报策略",
                    "type": "select",
                    "required": True,
                    "options": [
                        {"value": "balanced", "label": "稳妥为主（冲稳保结合）"},
                        {"value": "aggressive", "label": "冲刺为主（勇于尝试更高层次院校）"},
                        {"value": "conservative", "label": "保守为主（确保录取）"},
                    ],
                },
            ],
        },
    ],
}


@router.get("/provinces")
async def get_provinces():
    """Return list of supported provinces with details."""
    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": PROVINCES,
    }


@router.get("/subject-types")
async def get_subject_types():
    """Return supported subject (stream) types."""
    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": SUBJECT_TYPES,
    }


@router.get("/batches")
async def get_batches():
    """Return batch / admission-round configurations."""
    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": BATCHES,
    }


@router.get("/form-schema")
async def get_form_schema():
    """Return dynamic form schema used to render the volunteer application form."""
    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": FORM_SCHEMA,
    }
