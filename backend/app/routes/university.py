from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["University & Major"])

# ──────────────────────────────────────────────
# Mock data: universities
# ──────────────────────────────────────────────
MOCK_UNIVERSITIES = [
    {
        "id": "univ-001",
        "name": "清华大学",
        "name_en": "Tsinghua University",
        "province": "北京市",
        "city": "北京市",
        "type": "综合",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.tsinghua.edu.cn",
        "description": "中国顶尖综合性研究型大学，被誉为红色工程师的摇篮。",
        "ranking_national": 1,
        "founded_year": 1911,
    },
    {
        "id": "univ-002",
        "name": "北京大学",
        "name_en": "Peking University",
        "province": "北京市",
        "city": "北京市",
        "type": "综合",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.pku.edu.cn",
        "description": "中国近代第一所国立综合性大学，文理医工并重。",
        "ranking_national": 2,
        "founded_year": 1898,
    },
    {
        "id": "univ-003",
        "name": "浙江大学",
        "name_en": "Zhejiang University",
        "province": "浙江省",
        "city": "杭州市",
        "type": "综合",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.zju.edu.cn",
        "description": "教育部直属综合性研究型大学，学科门类齐全。",
        "ranking_national": 3,
        "founded_year": 1897,
    },
    {
        "id": "univ-004",
        "name": "上海交通大学",
        "name_en": "Shanghai Jiao Tong University",
        "province": "上海市",
        "city": "上海市",
        "type": "综合",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.sjtu.edu.cn",
        "description": "教育部直属全国重点大学，工科实力雄厚。",
        "ranking_national": 4,
        "founded_year": 1896,
    },
    {
        "id": "univ-005",
        "name": "复旦大学",
        "name_en": "Fudan University",
        "province": "上海市",
        "city": "上海市",
        "type": "综合",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.fudan.edu.cn",
        "description": "教育部直属综合性研究型大学，人文社科与医学实力突出。",
        "ranking_national": 5,
        "founded_year": 1905,
    },
    {
        "id": "univ-006",
        "name": "华中科技大学",
        "name_en": "Huazhong University of Science and Technology",
        "province": "湖北省",
        "city": "武汉市",
        "type": "综合",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.hust.edu.cn",
        "description": "教育部直属重点综合性大学，机械、光电、医学等学科优势突出。",
        "ranking_national": 7,
        "founded_year": 1952,
    },
    {
        "id": "univ-007",
        "name": "武汉大学",
        "name_en": "Wuhan University",
        "province": "湖北省",
        "city": "武汉市",
        "type": "综合",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.whu.edu.cn",
        "description": "教育部直属综合性研究型大学，樱花闻名全国。",
        "ranking_national": 8,
        "founded_year": 1893,
    },
    {
        "id": "univ-008",
        "name": "中山大学",
        "name_en": "Sun Yat-sen University",
        "province": "广东省",
        "city": "广州市",
        "type": "综合",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.sysu.edu.cn",
        "description": "教育部直属综合性大学，华南第一学府。",
        "ranking_national": 10,
        "founded_year": 1924,
    },
    {
        "id": "univ-009",
        "name": "华南理工大学",
        "name_en": "South China University of Technology",
        "province": "广东省",
        "city": "广州市",
        "type": "理工",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.scut.edu.cn",
        "description": "教育部直属全国重点大学，以工见长，理工结合。",
        "ranking_national": 24,
        "founded_year": 1952,
    },
    {
        "id": "univ-010",
        "name": "深圳大学",
        "name_en": "Shenzhen University",
        "province": "广东省",
        "city": "深圳市",
        "type": "综合",
        "level": "双非",
        "is_double_first_class": False,
        "logo_url": None,
        "website": "https://www.szu.edu.cn",
        "description": "广东省高水平大学重点建设高校，地处深圳特区。",
        "ranking_national": 70,
        "founded_year": 1983,
    },
    {
        "id": "univ-011",
        "name": "哈尔滨工业大学（深圳）",
        "name_en": "Harbin Institute of Technology (Shenzhen)",
        "province": "广东省",
        "city": "深圳市",
        "type": "理工",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.hitsz.edu.cn",
        "description": "C9联盟成员，哈工大深圳校区，工科实力顶尖。",
        "ranking_national": 13,
        "founded_year": 2002,
    },
    {
        "id": "univ-012",
        "name": "广东工业大学",
        "name_en": "Guangdong University of Technology",
        "province": "广东省",
        "city": "广州市",
        "type": "理工",
        "level": "双非",
        "is_double_first_class": False,
        "logo_url": None,
        "website": "https://www.gdut.edu.cn",
        "description": "广东省高水平大学重点建设高校，工科实力突出。",
        "ranking_national": 100,
        "founded_year": 1958,
    },
    {
        "id": "univ-013",
        "name": "暨南大学",
        "name_en": "Jinan University",
        "province": "广东省",
        "city": "广州市",
        "type": "综合",
        "level": "211",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.jnu.edu.cn",
        "description": "中国第一所由国家创办的华侨高等学府。",
        "ranking_national": 50,
        "founded_year": 1906,
    },
    {
        "id": "univ-014",
        "name": "华南师范大学",
        "name_en": "South China Normal University",
        "province": "广东省",
        "city": "广州市",
        "type": "师范",
        "level": "211",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.scnu.edu.cn",
        "description": "广东省高水平大学建设高校，教师教育特色鲜明。",
        "ranking_national": 60,
        "founded_year": 1933,
    },
    {
        "id": "univ-015",
        "name": "南方医科大学",
        "name_en": "Southern Medical University",
        "province": "广东省",
        "city": "广州市",
        "type": "医药",
        "level": "双非",
        "is_double_first_class": False,
        "logo_url": None,
        "website": "https://www.smu.edu.cn",
        "description": "广东省高水平大学重点建设高校，医学实力突出。",
        "ranking_national": 85,
        "founded_year": 1951,
    },
    {
        "id": "univ-016",
        "name": "西安电子科技大学",
        "name_en": "Xidian University",
        "province": "陕西省",
        "city": "西安市",
        "type": "理工",
        "level": "211",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.xidian.edu.cn",
        "description": "教育部直属全国重点大学，电子信息领域黄埔军校。",
        "ranking_national": 38,
        "founded_year": 1931,
    },
    {
        "id": "univ-017",
        "name": "四川大学",
        "name_en": "Sichuan University",
        "province": "四川省",
        "city": "成都市",
        "type": "综合",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.scu.edu.cn",
        "description": "教育部直属全国重点大学，西南地区最高学府。",
        "ranking_national": 12,
        "founded_year": 1896,
    },
    {
        "id": "univ-018",
        "name": "电子科技大学",
        "name_en": "University of Electronic Science and Technology of China",
        "province": "四川省",
        "city": "成都市",
        "type": "理工",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.uestc.edu.cn",
        "description": "教育部直属全国重点大学，电子信息领域顶尖。",
        "ranking_national": 29,
        "founded_year": 1956,
    },
    {
        "id": "univ-019",
        "name": "南京大学",
        "name_en": "Nanjing University",
        "province": "江苏省",
        "city": "南京市",
        "type": "综合",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.nju.edu.cn",
        "description": "C9联盟成员，历史悠久，学风严谨。",
        "ranking_national": 6,
        "founded_year": 1902,
    },
    {
        "id": "univ-020",
        "name": "山东大学",
        "name_en": "Shandong University",
        "province": "山东省",
        "city": "济南市",
        "type": "综合",
        "level": "985",
        "is_double_first_class": True,
        "logo_url": None,
        "website": "https://www.sdu.edu.cn",
        "description": "教育部直属全国重点大学，文史见长。",
        "ranking_national": 15,
        "founded_year": 1901,
    },
]

# ──────────────────────────────────────────────
# Mock data: majors
# ──────────────────────────────────────────────
MOCK_MAJORS = [
    {
        "id": "maj-001",
        "name": "计算机科学与技术",
        "name_en": "Computer Science and Technology",
        "category": "工学",
        "subcategory": "计算机类",
        "degree": "工学学士",
        "study_years": 4,
        "description": "培养具备计算机科学与技术基本理论和基本知识，能在科研、教育、企业等从事计算机应用开发的高级专门人才。",
    },
    {
        "id": "maj-002",
        "name": "软件工程",
        "name_en": "Software Engineering",
        "category": "工学",
        "subcategory": "计算机类",
        "degree": "工学学士",
        "study_years": 4,
        "description": "培养掌握软件工程基本理论和方法，能从事软件开发、项目管理等工作的高级人才。",
    },
    {
        "id": "maj-003",
        "name": "人工智能",
        "name_en": "Artificial Intelligence",
        "category": "工学",
        "subcategory": "计算机类",
        "degree": "工学学士",
        "study_years": 4,
        "description": "培养掌握人工智能基础理论和应用技术，能从事智能系统研发的复合型人才。",
    },
    {
        "id": "maj-004",
        "name": "临床医学",
        "name_en": "Clinical Medicine",
        "category": "医学",
        "subcategory": "临床医学类",
        "degree": "医学学士",
        "study_years": 5,
        "description": "培养具备基础医学和临床医学基本理论和医疗技能，能从事医疗、科研、教学的高级医学人才。",
    },
    {
        "id": "maj-005",
        "name": "口腔医学",
        "name_en": "Stomatology",
        "category": "医学",
        "subcategory": "口腔医学类",
        "degree": "医学学士",
        "study_years": 5,
        "description": "培养具备口腔医学基本理论和临床技能，能从事口腔医疗、预防、科研的高级人才。",
    },
    {
        "id": "maj-006",
        "name": "金融学",
        "name_en": "Finance",
        "category": "经济学",
        "subcategory": "金融学类",
        "degree": "经济学学士",
        "study_years": 4,
        "description": "培养具备金融学理论基础和实务能力，能在银行、证券、保险等金融机构工作的高级人才。",
    },
    {
        "id": "maj-007",
        "name": "法学",
        "name_en": "Law",
        "category": "法学",
        "subcategory": "法学类",
        "degree": "法学学士",
        "study_years": 4,
        "description": "培养系统掌握法学理论和法律实务，能在立法、司法、行政机关从事法律工作的高级人才。",
    },
    {
        "id": "maj-008",
        "name": "汉语言文学",
        "name_en": "Chinese Language and Literature",
        "category": "文学",
        "subcategory": "中国语言文学类",
        "degree": "文学学士",
        "study_years": 4,
        "description": "培养具备汉语及中国文学基本理论和知识，能在文化、教育、媒体等领域工作的高级人才。",
    },
    {
        "id": "maj-009",
        "name": "电子信息工程",
        "name_en": "Electronic Information Engineering",
        "category": "工学",
        "subcategory": "电子信息类",
        "degree": "工学学士",
        "study_years": 4,
        "description": "培养掌握电子技术和信息系统基本理论，能从事电子设备和信息系统研发的高级人才。",
    },
    {
        "id": "maj-010",
        "name": "通信工程",
        "name_en": "Communication Engineering",
        "category": "工学",
        "subcategory": "电子信息类",
        "degree": "工学学士",
        "study_years": 4,
        "description": "培养掌握通信理论和系统技术，能从事通信网络设计、研发、管理的高级人才。",
    },
    {
        "id": "maj-011",
        "name": "自动化",
        "name_en": "Automation",
        "category": "工学",
        "subcategory": "自动化类",
        "degree": "工学学士",
        "study_years": 4,
        "description": "培养掌握自动控制理论和技术，能从事控制系统研发、运行管理的高级人才。",
    },
    {
        "id": "maj-012",
        "name": "数学与应用数学",
        "name_en": "Mathematics and Applied Mathematics",
        "category": "理学",
        "subcategory": "数学类",
        "degree": "理学学士",
        "study_years": 4,
        "description": "培养掌握数学基本理论和方法，能在科技、教育、经济等领域从事研究、应用的高级人才。",
    },
    {
        "id": "maj-013",
        "name": "物理学",
        "name_en": "Physics",
        "category": "理学",
        "subcategory": "物理学类",
        "degree": "理学学士",
        "study_years": 4,
        "description": "培养掌握物理学基本理论和实验技能，能在科研机构、高校从事物理研究和教学的高级人才。",
    },
    {
        "id": "maj-014",
        "name": "机械设计制造及其自动化",
        "name_en": "Mechanical Design, Manufacturing and Automation",
        "category": "工学",
        "subcategory": "机械类",
        "degree": "工学学士",
        "study_years": 4,
        "description": "培养掌握机械设计制造和自动控制理论，能从事机械产品研发、制造的高级人才。",
    },
    {
        "id": "maj-015",
        "name": "土木工程",
        "name_en": "Civil Engineering",
        "category": "工学",
        "subcategory": "土木类",
        "degree": "工学学士",
        "study_years": 4,
        "description": "培养掌握土木工程基本理论和技能，能从事建筑设计、施工、管理的高级人才。",
    },
    {
        "id": "maj-016",
        "name": "工商管理",
        "name_en": "Business Administration",
        "category": "管理学",
        "subcategory": "工商管理类",
        "degree": "管理学学士",
        "study_years": 4,
        "description": "培养掌握管理学基本理论和实务技能，能从事企业经营管理工作的复合型人才。",
    },
    {
        "id": "maj-017",
        "name": "会计学",
        "name_en": "Accounting",
        "category": "管理学",
        "subcategory": "工商管理类",
        "degree": "管理学学士",
        "study_years": 4,
        "description": "培养掌握会计学基本理论和实务操作技能，能从事会计、审计、财务管理工作的高级人才。",
    },
    {
        "id": "maj-018",
        "name": "电气工程及其自动化",
        "name_en": "Electrical Engineering and Automation",
        "category": "工学",
        "subcategory": "电气类",
        "degree": "工学学士",
        "study_years": 4,
        "description": "培养掌握电气工程基本理论和自动化技术，能从事电力系统、电气设备研发的高级人才。",
    },
    {
        "id": "maj-019",
        "name": "英语",
        "name_en": "English",
        "category": "文学",
        "subcategory": "外国语言文学类",
        "degree": "文学学士",
        "study_years": 4,
        "description": "培养具备英语语言文学基本理论和跨文化交际能力，能从事翻译、教学、国际交流的高级人才。",
    },
    {
        "id": "maj-020",
        "name": "生物医学工程",
        "name_en": "Biomedical Engineering",
        "category": "工学",
        "subcategory": "生物医学工程类",
        "degree": "工学学士",
        "study_years": 4,
        "description": "培养掌握工程学和医学交叉学科知识，能从事医疗仪器研发、生物信息处理的高级人才。",
    },
    {
        "id": "maj-021",
        "name": "药学",
        "name_en": "Pharmacy",
        "category": "医学",
        "subcategory": "药学类",
        "degree": "理学学士",
        "study_years": 4,
        "description": "培养具备药学基本理论和实验技能，能从事药物研发、生产、检验、管理的高级人才。",
    },
    {
        "id": "maj-022",
        "name": "新闻学",
        "name_en": "Journalism",
        "category": "文学",
        "subcategory": "新闻传播学类",
        "degree": "文学学士",
        "study_years": 4,
        "description": "培养掌握新闻学基本理论和采编技能，能从事新闻采访、编辑、传播工作的高级人才。",
    },
    {
        "id": "maj-023",
        "name": "建筑学",
        "name_en": "Architecture",
        "category": "工学",
        "subcategory": "建筑类",
        "degree": "工学学士",
        "study_years": 5,
        "description": "培养掌握建筑设计基本理论和方法，能从事建筑设计、城市设计的高级人才。",
    },
    {
        "id": "maj-024",
        "name": "数据科学与大数据技术",
        "name_en": "Data Science and Big Data Technology",
        "category": "工学",
        "subcategory": "计算机类",
        "degree": "理学学士",
        "study_years": 4,
        "description": "培养掌握数据科学基础理论和大数据处理技术，能从事数据分析、挖掘、应用的复合型人才。",
    },
    {
        "id": "maj-025",
        "name": "心理学",
        "name_en": "Psychology",
        "category": "理学",
        "subcategory": "心理学类",
        "degree": "理学学士",
        "study_years": 4,
        "description": "培养掌握心理学基本理论和研究方法，能从事心理咨询、教育、科研的高级人才。",
    },
]


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────


@router.get("/universities")
async def search_universities(
    keyword: Optional[str] = Query(None, description="搜索关键词（院校名称）"),
    province: Optional[str] = Query(None, description="省份筛选"),
    city: Optional[str] = Query(None, description="城市筛选"),
    type: Optional[str] = Query(None, alias="univ_type", description="院校类型（综合/理工/师范/医药等）"),
    level: Optional[str] = Query(None, description="院校层次（985/211/双非）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):
    """搜索大学列表，支持分页和按省/市/类型/层次筛选。"""
    items = MOCK_UNIVERSITIES

    # Filter
    if keyword:
        items = [u for u in items if keyword.lower() in u["name"].lower() or keyword.lower() in u.get("name_en", "").lower()]
    if province:
        items = [u for u in items if u["province"] == province]
    if city:
        items = [u for u in items if u["city"] == city]
    if type:
        items = [u for u in items if u["type"] == type]
    if level:
        items = [u for u in items if u["level"] == level]

    total = len(items)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    paged = items[start:end]

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "items": paged,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/universities/{university_id}")
async def get_university_detail(university_id: str):
    """获取大学详情。"""
    for u in MOCK_UNIVERSITIES:
        if u["id"] == university_id:
            return {
                "success": True,
                "code": "OK",
                "message": "success",
                "data": u,
            }
    raise HTTPException(status_code=404, detail="University not found")


@router.get("/majors")
async def search_majors(
    keyword: Optional[str] = Query(None, description="搜索关键词（专业名称）"),
    category: Optional[str] = Query(None, description="学科门类（工学/理学/医学/文学/法学/经济学/管理学等）"),
    subcategory: Optional[str] = Query(None, description="专业类（计算机类/临床医学类/金融学类等）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
):
    """搜索专业列表，支持分页和按学科门类/专业类筛选。"""
    items = MOCK_MAJORS

    # Filter
    if keyword:
        items = [m for m in items if keyword.lower() in m["name"].lower() or keyword.lower() in m.get("name_en", "").lower()]
    if category:
        items = [m for m in items if m["category"] == category]
    if subcategory:
        items = [m for m in items if m["subcategory"] == subcategory]

    total = len(items)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    paged = items[start:end]

    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "items": paged,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/majors/{major_id}")
async def get_major_detail(major_id: str):
    """获取专业详情。"""
    for m in MOCK_MAJORS:
        if m["id"] == major_id:
            return {
                "success": True,
                "code": "OK",
                "message": "success",
                "data": m,
            }
    raise HTTPException(status_code=404, detail="Major not found")
