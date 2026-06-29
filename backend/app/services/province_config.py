"""
省份配置中心 — 全国31省高考模式、选科、批次、分数、改革年份

每省一个 ProvinceConfig，驱动前端表单联动 + 后端查询适配。
"""

from dataclasses import dataclass, field
from typing import Literal

ExamMode = Literal["3+3", "3+1+2", "传统文理"]
AdmissionUnit = Literal["院校专业组", "专业+院校", "院校"]


@dataclass
class ProvinceConfig:
    """单个省份的高考配置"""

    # 标识
    code: str           # 数据库/API 用简称，如 '山东'
    name: str           # 展示名，如 '山东省'

    # 考试模式
    exam_mode: ExamMode                          # 3+3 / 3+1+2 / 传统文理
    admission_unit: AdmissionUnit                # 投档单位
    score_max: int = 750                         # 满分
    score_min: int = 0

    # 选科选项（前端按钮列表）
    subject_options: list[str] = field(default_factory=list)       # 如 ['物理类','历史类']
    subject_options_secondary: list[str] = field(default_factory=list)  # 3+1+2 再选科
    subject_type_default: str = "综合"                              # 默认科类

    # 批次
    batches: list[str] = field(default_factory=lambda: ["本科普通批"])

    # 改革年份：{年份: 'old'|'new'}，用于切换投档规则
    reform_year: dict[int, str] = field(default_factory=dict)

    # 一分段 subject_type 映射：原始xlsx中的category → 数据库 subject_type
    segment_subject_map: dict[str, str] = field(default_factory=dict)

    # 投档线 subject_type 映射
    admission_subject_map: dict[str, str] = field(default_factory=dict)

    # 提示文案
    hint_score: str = "满分 750"
    hint_subject: str = "请选择报考科类"
    hint_batch: str = ""


# ═══════════════════════════════════════════════
# 3+3 省份
# ═══════════════════════════════════════════════

SD = ProvinceConfig(
    code="山东", name="山东省",
    exam_mode="3+3", admission_unit="专业+院校",
    subject_options=["综合", "选考物理", "选考化学", "选考生物", "选考历史", "选考政治", "选考地理"],
    subject_type_default="综合",
    segment_subject_map={
        "全体": "综合", "选考物理": "physics", "选考化学": "chemistry",
        "选考生物": "biology", "选考思想政治": "politics",
        "选考历史": "history", "选考地理": "geography",
    },
    admission_subject_map={"综合": "综合", "物理": "physics", "化学": "chemistry",
                           "生物": "biology", "政治": "politics", "历史": "history", "地理": "geography"},
    hint_score="满分 750", hint_subject="3+3 省份，选考科目可多选",
)

BJ = ProvinceConfig(
    code="北京", name="北京市",
    exam_mode="3+3", admission_unit="院校专业组",
    subject_options=["综合"],  # 北京投档线不按选科拆分
    subject_type_default="综合",
    segment_subject_map={"综合": "综合"},
    admission_subject_map={"综合": "综合"},
    hint_score="满分 750",
)

TJ = ProvinceConfig(
    code="天津", name="天津市",
    exam_mode="3+3", admission_unit="院校专业组",
    subject_options=["综合"],
    subject_type_default="综合",
    segment_subject_map={"综合": "综合"},
    admission_subject_map={"综合": "综合"},
    hint_score="满分 750",
)

SH = ProvinceConfig(
    code="上海", name="上海市",
    exam_mode="3+3", admission_unit="院校专业组",
    score_max=660, score_min=0,
    subject_options=["综合改革"],
    subject_type_default="综合改革",
    segment_subject_map={"综合改革": "综合改革"},
    admission_subject_map={"综合改革": "综合改革"},
    hint_score="满分 660",
)

ZJ = ProvinceConfig(
    code="浙江", name="浙江省",
    exam_mode="3+3", admission_unit="专业+院校",
    subject_options=["综合"],
    subject_type_default="综合",
    segment_subject_map={"综合": "综合"},
    admission_subject_map={"综合": "综合"},
    hint_score="满分 750",
)

HN_ = ProvinceConfig(
    code="海南", name="海南省",
    exam_mode="3+3", admission_unit="院校专业组",
    score_max=900, score_min=0,
    subject_options=["综合改革"],
    subject_type_default="综合改革",
    segment_subject_map={"综合改革": "综合改革"},
    admission_subject_map={"综合改革": "综合改革"},
    hint_score="满分 900",
)


# ═══════════════════════════════════════════════
# 3+1+2 省份（始终新高考）
# ═══════════════════════════════════════════════

HEB = ProvinceConfig(
    code="河北", name="河北省",
    exam_mode="3+1+2", admission_unit="专业+院校",
    subject_options=["物理类", "历史类"],
    subject_options_secondary=["化学", "生物", "政治", "地理"],
    subject_type_default="物理类",
    segment_subject_map={"物理类": "physics", "历史类": "history"},
    admission_subject_map={"物理类": "physics", "历史类": "history"},
    hint_subject="3+1+2 省份，首选物理或历史",
)

LN = ProvinceConfig(
    code="辽宁", name="辽宁省",
    exam_mode="3+1+2", admission_unit="专业+院校",
    subject_options=["物理类", "历史类"],
    subject_options_secondary=["化学", "生物", "政治", "地理"],
    subject_type_default="物理类",
    segment_subject_map={"物理类": "physics", "历史类": "history"},
    admission_subject_map={"物理类": "physics", "历史类": "history"},
    hint_subject="3+1+2 省份，首选物理或历史",
)

JS = ProvinceConfig(
    code="江苏", name="江苏省",
    exam_mode="3+1+2", admission_unit="院校专业组",
    subject_options=["物理类", "历史类"],
    subject_options_secondary=["化学", "生物", "政治", "地理"],
    subject_type_default="物理类",
    segment_subject_map={"物理类": "physics", "历史类": "history"},
    admission_subject_map={"物理类": "physics", "历史类": "history"},
    hint_subject="3+1+2 省份，院校专业组投档",
)

FJ = ProvinceConfig(
    code="福建", name="福建省",
    exam_mode="3+1+2", admission_unit="院校专业组",
    subject_options=["物理类", "历史类"],
    subject_options_secondary=["化学", "生物", "政治", "地理"],
    subject_type_default="物理类",
    segment_subject_map={"物理类": "physics", "历史类": "history"},
    admission_subject_map={"物理类": "physics", "历史类": "history"},
)

HUB = ProvinceConfig(
    code="湖北", name="湖北省",
    exam_mode="3+1+2", admission_unit="院校专业组",
    subject_options=["物理类", "历史类"],
    subject_options_secondary=["化学", "生物", "政治", "地理"],
    subject_type_default="物理类",
    segment_subject_map={"物理类": "physics", "历史类": "history"},
    admission_subject_map={"物理类": "physics", "历史类": "history"},
)

HUN = ProvinceConfig(
    code="湖南", name="湖南省",
    exam_mode="3+1+2", admission_unit="院校专业组",
    subject_options=["物理类", "历史类"],
    subject_options_secondary=["化学", "生物", "政治", "地理"],
    subject_type_default="物理类",
    segment_subject_map={"物理类": "physics", "历史类": "history"},
    admission_subject_map={"物理类": "physics", "历史类": "history"},
)

GD = ProvinceConfig(
    code="广东", name="广东省",
    exam_mode="3+1+2", admission_unit="院校专业组",
    subject_options=["物理类", "历史类"],
    subject_options_secondary=["化学", "生物", "政治", "地理"],
    subject_type_default="物理类",
    segment_subject_map={"物理类": "physics", "历史类": "history"},
    admission_subject_map={"物理类": "physics", "历史类": "history"},
    hint_subject="3+1+2 省份，数据较完整",
)

CQ = ProvinceConfig(
    code="重庆", name="重庆市",
    exam_mode="3+1+2", admission_unit="专业+院校",
    subject_options=["物理类", "历史类"],
    subject_options_secondary=["化学", "生物", "政治", "地理"],
    subject_type_default="物理类",
    segment_subject_map={"物理类": "physics", "历史类": "history"},
    admission_subject_map={"物理类": "physics", "历史类": "history"},
)


# ═══════════════════════════════════════════════
# 3+1+2 省份（2024 首届新高考）
# ═══════════════════════════════════════════════

def _3plus1plus2_2024(code, name, admission_unit="院校专业组"):
    return ProvinceConfig(
        code=code, name=name,
        exam_mode="3+1+2", admission_unit=admission_unit,
        subject_options=["物理类", "历史类"],
        subject_options_secondary=["化学", "生物", "政治", "地理"],
        subject_type_default="物理类",
        segment_subject_map={
            "物理类": "physics", "历史类": "history",
            "理科": "physics", "文科": "history",  # 老高考遗留
        },
        admission_subject_map={
            "物理类": "physics", "历史类": "history",
            "理科": "physics", "文科": "history",
        },
        reform_year={2022: "old", 2023: "old", 2024: "new", 2025: "new"},
        hint_subject="2024 起新高考，2023 前为传统文理",
    )

HLJ = _3plus1plus2_2024("黑龙江", "黑龙江省")
JL  = _3plus1plus2_2024("吉林", "吉林省")
AH  = _3plus1plus2_2024("安徽", "安徽省")
JX  = _3plus1plus2_2024("江西", "江西省")
GX  = _3plus1plus2_2024("广西", "广西壮族自治区")
GZ  = _3plus1plus2_2024("贵州", "贵州省", admission_unit="专业+院校")
GS  = _3plus1plus2_2024("甘肃", "甘肃省")


# ═══════════════════════════════════════════════
# 3+1+2 省份（2025 首届新高考）
# ═══════════════════════════════════════════════

def _3plus1plus2_2025(code, name):
    return ProvinceConfig(
        code=code, name=name,
        exam_mode="3+1+2", admission_unit="院校专业组",
        subject_options=["物理类", "历史类"],
        subject_options_secondary=["化学", "生物", "政治", "地理"],
        subject_type_default="物理类",
        segment_subject_map={
            "物理类": "physics", "历史类": "history",
            "理科": "physics", "文科": "history",
        },
        admission_subject_map={
            "物理类": "physics", "历史类": "history",
            "理科": "physics", "文科": "history",
        },
        reform_year={2022: "old", 2023: "old", 2024: "old", 2025: "new"},
        hint_subject="2025 起新高考，2024 前为传统文理",
    )

SX_ = _3plus1plus2_2025("山西", "山西省")
HEN = _3plus1plus2_2025("河南", "河南省")
SNX = _3plus1plus2_2025("陕西", "陕西省")
NMG = _3plus1plus2_2025("内蒙古", "内蒙古自治区")
SC  = _3plus1plus2_2025("四川", "四川省")
YN  = _3plus1plus2_2025("云南", "云南省")
NX  = _3plus1plus2_2025("宁夏", "宁夏回族自治区")
QH  = _3plus1plus2_2025("青海", "青海省")


# ═══════════════════════════════════════════════
# 传统文理 / 特殊
# ═══════════════════════════════════════════════

XJ = ProvinceConfig(
    code="新疆", name="新疆维吾尔自治区",
    exam_mode="传统文理", admission_unit="院校",
    subject_options=["理工", "文史"],
    subject_type_default="理工",
    segment_subject_map={"理工": "science", "文史": "arts"},
    admission_subject_map={"理工": "science", "文史": "arts"},
    reform_year={},  # 2026 仍传统，2027 起 3+1+2
    hint_subject="传统文理分科",
)

XZ = ProvinceConfig(
    code="西藏", name="西藏自治区",
    exam_mode="传统文理", admission_unit="院校",
    subject_options=["文史", "理工"],
    subject_type_default="理工",
    segment_subject_map={"文史": "arts", "理工": "science"},
    admission_subject_map={"文史": "arts", "理工": "science"},
    hint_subject="传统文理分科，含民族课程体系",
)


# ═══════════════════════════════════════════════
# 全局索引
# ═══════════════════════════════════════════════

ALL_PROVINCE_CONFIGS: dict[str, ProvinceConfig] = {
    "山东": SD, "北京": BJ, "天津": TJ, "上海": SH, "浙江": ZJ, "海南": HN_,
    "河北": HEB, "辽宁": LN, "江苏": JS, "福建": FJ, "湖北": HUB, "湖南": HUN,
    "广东": GD, "重庆": CQ,
    "黑龙江": HLJ, "吉林": JL, "安徽": AH, "江西": JX, "广西": GX,
    "贵州": GZ, "甘肃": GS,
    "山西": SX_, "河南": HEN, "陕西": SNX, "内蒙古": NMG, "四川": SC,
    "云南": YN, "宁夏": NX, "青海": QH,
    "新疆": XJ, "西藏": XZ,
}


def get_province_config(province_name: str) -> ProvinceConfig | None:
    """根据省份名称（如 '山东' 或 '山东省'）获取配置"""
    # 去掉「省」「市」「自治区」后缀
    short = province_name.rstrip("省市自治区").replace("壮族", "").replace("回族", "").replace("维吾尔", "")
    for key, cfg in ALL_PROVINCE_CONFIGS.items():
        if key == short or key == province_name or cfg.name == province_name:
            return cfg
    # 模糊匹配
    for key, cfg in ALL_PROVINCE_CONFIGS.items():
        if key in province_name or province_name in key:
            return cfg
    return None


def get_exam_mode(province_name: str) -> str:
    cfg = get_province_config(province_name)
    return cfg.exam_mode if cfg else "未知"


def get_subject_options(province_name: str) -> list[str]:
    cfg = get_province_config(province_name)
    return cfg.subject_options if cfg else ["综合"]


def get_score_max(province_name: str) -> int:
    cfg = get_province_config(province_name)
    return cfg.score_max if cfg else 750


def get_year_rule(province_name: str, year: int) -> str:
    """获取某省某年的高考规则版本 ('old'|'new'|'unknown')"""
    cfg = get_province_config(province_name)
    if cfg and year in cfg.reform_year:
        return cfg.reform_year[year]
    return "unknown"


def map_subject_type(province_name: str, raw_category: str, map_type: str = "segment") -> str:
    """将原始xlsx中的category映射为数据库subject_type"""
    cfg = get_province_config(province_name)
    if not cfg:
        return raw_category
    mapping = cfg.segment_subject_map if map_type == "segment" else cfg.admission_subject_map
    return mapping.get(raw_category, raw_category)
