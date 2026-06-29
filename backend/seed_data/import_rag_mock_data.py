"""
Mock RAG 数据生成 + 导入
为导入了的山东高校生成：学校介绍、专业介绍、城市资料等 RAG chunk
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
import uuid
from sqlalchemy import text, select, distinct
from app.core.database import async_session_factory
from app.models.models import RagChunk, AdmissionLine

# 生成 RAG 知识库：学校介绍
SCHOOL_DESCRIPTIONS = {
    "山东大学": {
        "city": "济南",
        "type": "综合",
        "level": "985",
        "description": "山东大学是中华人民共和国教育部直属的全国重点大学，位列国家\"双一流\"、\"985工程\"、\"211工程\"。学校主体位于山东省济南市，在青岛、威海设有校区。山大是一所历史悠久、学科齐全、学术实力雄厚的综合性大学。",
    },
    "中国海洋大学": {
        "city": "青岛",
        "type": "综合",
        "level": "985",
        "description": "中国海洋大学坐落于山东省青岛市，是教育部直属重点综合性大学，国家\"985工程\"和\"211工程\"重点建设高校，国家\"双一流\"建设高校。学校以海洋和水产学科为特色，涵盖理学、工学、农学、医学、文学、经济学、管理学、法学、教育学、艺术学等学科门类。",
    },
    "中国石油大学（华东）": {
        "city": "青岛",
        "type": "理工",
        "level": "211",
        "description": "中国石油大学（华东）是教育部直属全国重点大学，国家\"211工程\"重点建设高校，国家\"双一流\"建设高校。学校位于山东省青岛市，是一所以工为主、石油石化特色鲜明、多学科协调发展的大学。",
    },
    "哈尔滨工业大学（威海）": {
        "city": "威海",
        "type": "理工",
        "level": "985",
        "description": "哈尔滨工业大学（威海）是哈尔滨工业大学的重要组成部分，位于山东省威海市。哈工大是国家\"985工程\"重点建设高校，享有\"工程师的摇篮\"之美誉。威海校区与校本部同一品牌、同一规格，在电子信息、计算机、机械、材料等工科领域实力突出。",
    },
    "山东师范大学": {
        "city": "济南",
        "type": "师范",
        "level": "普通",
        "description": "山东师范大学位于山东省济南市，是一所学科门类齐全的综合性师范大学，山东省属重点高校。学校在教师教育、人文社科、基础理学等领域具有传统优势，同时在计算机、电子信息等应用型学科也有良好发展。",
    },
    "青岛大学": {
        "city": "青岛",
        "type": "综合",
        "level": "普通",
        "description": "青岛大学位于山东省青岛市，是山东省属重点综合大学。学校由原青岛大学、山东纺织工学院、青岛医学院和青岛师范专科学校合并组建，临床医学、工程学、化学、材料科学等学科实力突出。",
    },
    "山东科技大学": {
        "city": "青岛",
        "type": "理工",
        "level": "普通",
        "description": "山东科技大学是一所工科优势突出、行业特色鲜明的山东省属重点大学。学校主校区位于青岛，在泰安和济南设有校区。在矿业工程、安全工程、测绘科学与技术、计算机科学等领域具有显著优势。",
    },
    "济南大学": {
        "city": "济南",
        "type": "综合",
        "level": "普通",
        "description": "济南大学是山东省政府和教育部共建的综合性大学，山东省属重点高校。学校位于济南市，在材料科学、化学、工程学、计算机科学等领域有较强的教学和科研实力。",
    },
    "曲阜师范大学": {
        "city": "曲阜",
        "type": "师范",
        "level": "普通",
        "description": "曲阜师范大学位于孔子故里曲阜，是一所以教师教育为特色的省属重点大学。学校被誉为\"考研神校\"，考研率长期位居全国前列。在数学、教育学、历史学、中国语言文学等学科有深厚积淀。",
    },
    "烟台大学": {
        "city": "烟台",
        "type": "综合",
        "level": "普通",
        "description": "烟台大学位于山东省烟台市，是山东省属综合性大学。学校由北京大学、清华大学共同援建，在法学、药学、数学、电子科学与技术等学科有较好基础。",
    },
    "山东财经大学": {
        "city": "济南",
        "type": "财经",
        "level": "普通",
        "description": "山东财经大学位于济南市，是山东省属重点财经大学。学校由原山东经济学院和山东财政学院合并组建，在经济学、管理学、统计学等领域具有显著优势，是山东省最好的财经类高校。",
    },
    "山东农业大学": {
        "city": "泰安",
        "type": "农林",
        "level": "普通",
        "description": "山东农业大学位于泰山脚下的泰安市，是山东省属重点农业院校。学校在作物学、园艺学、植物保护、农业资源与环境等学科有博士点和国家重点学科，农学实力全国前列。",
    },
    "青岛科技大学": {
        "city": "青岛",
        "type": "理工",
        "level": "普通",
        "description": "青岛科技大学位于青岛市，以材料科学与工程、化学工程与技术为特色，被称为\"中国橡胶工业的黄埔军校\"。在化学、材料科学、工程学等领域进入全球ESI排名前1%。",
    },
    "山东建筑大学": {
        "city": "济南",
        "type": "理工",
        "level": "普通",
        "description": "山东建筑大学位于济南市，是以土木建筑为特色的山东省属工科院校。在建筑学、土木工程、城乡规划等建筑类学科有较强实力，为建筑行业培养了大量人才。",
    },
    "齐鲁工业大学": {
        "city": "济南",
        "type": "理工",
        "level": "普通",
        "description": "齐鲁工业大学（山东省科学院）位于济南市，是山东省属重点工科院校。学校在轻工技术与工程、计算机科学与技术、材料科学与工程等领域有较强的科研实力。",
    },
    "鲁东大学": {
        "city": "烟台",
        "type": "综合",
        "level": "普通",
        "description": "鲁东大学位于烟台市，是一所综合性大学。学校在汉语言文学、历史学、数学、教育学等传统学科有较好基础，同时大力发展计算机、电子等应用学科。",
    },
    "临沂大学": {
        "city": "临沂",
        "type": "综合",
        "level": "普通",
        "description": "临沂大学位于山东省临沂市，是沂蒙革命老区的一所综合性大学。学校在数学、化学、工程学等领域有一定实力，师范教育具有传统优势。",
    },
    "山东理工大学": {
        "city": "淄博",
        "type": "理工",
        "level": "普通",
        "description": "山东理工大学位于淄博市，是山东省属重点理工科院校。学校在农业工程、机械工程、电气工程、计算机科学等领域有较好表现，车辆工程是其特色专业。",
    },
}

# 专业介绍数据
MAJOR_INTRODUCTIONS = {
    "计算机科学与技术": {
        "category": "工学",
        "description": "计算机科学与技术是研究计算机系统结构、软件理论与应用技术的学科。核心课程包括数据结构与算法、操作系统、计算机网络、数据库原理、编译原理等。就业方向覆盖软件开发、算法工程、系统架构、人工智能等方向。该专业是当前就业率最高、薪资水平最好的专业之一。",
        "suitable_for": "对编程感兴趣、逻辑思维强、数学基础好的学生。需要较强的自学能力和持续学习意愿。",
    },
    "软件工程": {
        "category": "工学",
        "description": "软件工程专注于大型软件系统的开发方法论、工程管理、质量保证和质量控制。核心课程包括软件需求分析、软件设计、软件测试、项目管理等。就业方向包括软件开发工程师、测试工程师、项目经理、DevOps工程师等。",
        "suitable_for": "喜欢团队协作、项目管理，对软件开发流程感兴趣的学生。",
    },
    "人工智能": {
        "category": "工学",
        "description": "人工智能是研究如何使计算机模拟人类智能行为的交叉学科。核心课程包括机器学习、深度学习、自然语言处理、计算机视觉、强化学习等。就业方向覆盖AI算法工程师、数据科学家、NLP工程师、计算机视觉工程师等。",
        "suitable_for": "数学基础极好、对算法研究有热情、想从事前沿技术开发的学生。建议考研深造。",
    },
    "数据科学与大数据技术": {
        "category": "工学",
        "description": "数据科学与大数据技术培养具备数据采集、存储、处理、分析和可视化的能力。核心课程包括统计学、机器学习、数据挖掘、分布式计算、数据可视化等。就业方向包括数据分析师、大数据工程师、数据科学家等。",
        "suitable_for": "对数据敏感、喜欢分析问题、既有编程能力又有统计思维的学生。",
    },
    "电子信息工程": {
        "category": "工学",
        "description": "电子信息工程是研究电子信号处理、通信系统、嵌入式系统的学科。核心课程包括电路分析、信号与系统、数字信号处理、通信原理、嵌入式系统等。就业方向包括硬件工程师、嵌入式工程师、通信工程师等。",
        "suitable_for": "动手能力强、对电子电路和硬件感兴趣、既懂软件也懂硬件的学生。",
    },
    "自动化": {
        "category": "工学",
        "description": "自动化是研究系统控制、智能控制、机器人技术的学科。核心课程包括自动控制原理、传感器技术、电机拖动、过程控制、智能控制等。就业方向包括自动化工程师、控制工程师、机器人工程师、PLC工程师等。",
        "suitable_for": "喜欢系统思维、对智能制造和工业4.0感兴趣、动手能力强的学生。",
    },
    "通信工程": {
        "category": "工学",
        "description": "通信工程是研究信息传输、交换和处理技术的学科。核心课程包括通信原理、移动通信、光纤通信、数据通信与网络等。就业方向包括通信工程师、网络工程师、5G/6G研发工程师等。",
        "suitable_for": "对通信技术感兴趣、数学物理基础好的学生。",
    },
    "电气工程及其自动化": {
        "category": "工学",
        "description": "电气工程及其自动化是研究电力系统、电机控制、电气自动化的学科。核心课程包括电路理论、电机学、电力系统分析、电力电子技术、继电保护等。就业方向包括国家电网、电力设计院、电气工程师等。",
        "suitable_for": "对电力和能源行业感兴趣、动手能力强、希望稳定就业的学生。",
    },
    "机械工程": {
        "category": "工学",
        "description": "机械工程是研究机械设计、制造、自动化的传统工科。核心课程包括机械制图、理论力学、材料力学、机械设计、机械制造基础等。就业方向包括机械工程师、结构设计工程师、工艺工程师等。",
        "suitable_for": "动手能力强、喜欢设计和制造、对实体产品有热情的学生。",
    },
    "数学与应用数学": {
        "category": "理学",
        "description": "数学与应用数学培养扎实的数学理论基础和应用能力。核心课程包括数学分析、高等代数、概率论与数理统计、运筹学、数值计算等。就业方向包括金融量化分析、数据科学、教育科研、IT算法工程师等。",
        "suitable_for": "对纯数学和应用数学都有兴趣、逻辑思维极强、可转金融或IT方向的学生。",
    },
    "临床医学": {
        "category": "医学",
        "description": "临床医学是培养从事临床医疗工作的高级医学人才。学制通常为5年，核心课程包括人体解剖学、生理学、病理学、药理学、内科学、外科学等。就业方向为各级医院的临床医生，需要完成住院医师规范化培训。",
        "suitable_for": "对医学有热情、有耐心和责任心、能承受高强度学习工作压力的学生。学制长、投入大。",
    },
    "法学": {
        "category": "法学",
        "description": "法学是研究法律规范、法律关系和法律制度的学科。核心课程包括法理学、宪法学、民法学、刑法学、行政法学、诉讼法学等。就业方向包括律师、法官/检察官、企业法务、公务员等。",
        "suitable_for": "逻辑思维强、善于表达和辩论、对公平正义有追求、文字表达能力好的学生。",
    },
    "会计学": {
        "category": "管理学",
        "description": "会计学是研究企业财务信息记录、分析和报告的学科。核心课程包括基础会计、中级财务会计、成本会计、审计学、财务管理等。就业方向包括企业会计、审计师、财务分析师、税务师等。",
        "suitable_for": "细心、认真、对数字敏感、希望从事稳定职业的学生。考证（CPA/ACCA）对就业极为重要。",
    },
    "金融学": {
        "category": "经济学",
        "description": "金融学研究资金融通、投资决策和风险管理。核心课程包括微观经济学、宏观经济学、金融学原理、投资学、公司金融、国际金融等。就业方向包括银行、证券公司、基金公司、保险公司、金融科技公司等。",
        "suitable_for": "对经济和金融市场感兴趣、数学基础好、抗压能力强的学生。名校背景对金融行业非常重要。",
    },
}

# 城市资料
CITY_DATA = {
    "济南": {
        "定位": "山东省省会，历史文化名城",
        "产业": "信息技术、高端装备、生物医药、文化旅游",
        "高校": "山东大学、山东师范大学、济南大学、山东财经大学、齐鲁工业大学",
        "就业": "信息技术产业快速发展，济南高新区集聚了大量科技企业。浪潮集团、中孚信息、众阳软件等IT企业总部设在济南。",
    },
    "青岛": {
        "定位": "计划单列市，沿海开放城市",
        "产业": "智能家电、轨道交通装备、海洋经济、现代金融",
        "高校": "中国海洋大学、中国石油大学（华东）、青岛大学、山东科技大学、青岛科技大学",
        "就业": "海尔、海信、中车四方等知名企业总部所在地。海洋经济和对外贸易发达，对工科、外语、贸易类人才需求大。",
    },
    "烟台": {
        "定位": "环渤海地区重要港口城市",
        "产业": "电子信息、食品加工、有色及贵金属加工、高端化工",
        "高校": "烟台大学、鲁东大学、山东工商学院",
        "就业": "烟台是山东省经济总量前三的城市，万华化学、杰瑞股份、中集来福士等知名企业坐落于此。",
    },
    "威海": {
        "定位": "宜居海滨城市，中韩经济合作前沿",
        "产业": "医疗器械、打印设备、海洋食品、旅游",
        "高校": "哈尔滨工业大学（威海）、山东大学（威海）、北京交通大学（威海）",
        "就业": "威海是\"中国医疗器械之都\"，威高集团为行业龙头。城市环境优美，适合宜居发展。",
    },
}

# 招生章程示例
ADMISSION_RULES = """
录取规则：
1. 学校根据各省（自治区、直辖市）生源情况确定投档比例，按照平行志愿投档的批次，调档比例原则上不超过105%。
2. 按照\"分数优先、遵循志愿\"的原则进行专业分配，不设专业级差。
3. 当考生所有专业志愿都无法满足时，若服从专业调剂，则根据考生成绩调剂到其他专业录取；若不服从调剂，作退档处理。
4. 各专业不限外语语种，但入校后公共外语课程仅开设英语。
5. 身体健康状况要求按照教育部《普通高等学校招生体检工作指导意见》执行。
"""


async def generate_and_import():
    print("=== 生成 RAG chunk 数据 ===")
    async with async_session_factory() as session:
        # 获取山东有投档数据的学校列表
        result = await session.execute(
            text("SELECT DISTINCT university_name FROM admission_lines WHERE province='山东' ORDER BY university_name")
        )
        schools = [r[0] for r in result.fetchall()]
        print(f"山东投档数据中共有 {len(schools)} 所高校")
        
        # 清空旧数据
        await session.execute(text("DELETE FROM rag_chunks"))
        await session.commit()
        
        chunks = []
        chunk_id = 0
        
        # 1. 学校介绍
        for school_name, info in SCHOOL_DESCRIPTIONS.items():
            chunk_id += 1
            chunks.append(RagChunk(
                chunk_id=f"school_intro_{chunk_id}",
                doc_type="学校介绍",
                school_name=school_name,
                province="山东",
                city=info["city"],
                year=2025,
                title=f"{school_name}介绍",
                section="学校简介",
                content=f"{school_name}是位于山东省{info['city']}的一所{info['type']}类高校，{info['level']}层次。{info['description']}",
                source_url="mock",
                data_source="mock",
            ))
        
        # 2. 专业介绍
        for major_name, info in MAJOR_INTRODUCTIONS.items():
            for school_name, school_info in SCHOOL_DESCRIPTIONS.items():
                # 每个学校选择3-4个主流专业（按学校类型匹配）
                is_tech_school = school_info['type'] in ('理工', '综合')
                is_med_school = '医药' in school_info['type']
                is_econ_school = '财经' in school_info['type']
                
                cs_majors = ["计算机科学与技术", "软件工程", "人工智能", "数据科学与大数据技术", "电子信息工程"]
                engineering_majors = ["自动化", "通信工程", "电气工程及其自动化", "机械工程"]
                
                if major_name in cs_majors and is_tech_school:
                    chunk_id += 1
                    chunks.append(RagChunk(
                        chunk_id=f"major_intro_{chunk_id}",
                        doc_type="专业介绍",
                        school_name=school_name,
                        major_name=major_name,
                        province="山东",
                        city=school_info["city"],
                        year=2025,
                        title=f"{school_name}{major_name}专业介绍",
                        section="专业简介",
                        content=f"{school_name}的{major_name}专业属于{MAJOR_INTRODUCTIONS[major_name]['category']}学科门类。{MAJOR_INTRODUCTIONS[major_name]['description']}",
                        source_url="mock",
                        data_source="mock",
                    ))
                elif major_name in engineering_majors and is_tech_school:
                    chunk_id += 1
                    chunks.append(RagChunk(
                        chunk_id=f"major_intro_{chunk_id}",
                        doc_type="专业介绍",
                        school_name=school_name,
                        major_name=major_name,
                        province="山东",
                        city=school_info["city"],
                        year=2025,
                        title=f"{school_name}{major_name}专业介绍",
                        section="专业简介",
                        content=f"{school_name}的{major_name}专业属于{MAJOR_INTRODUCTIONS[major_name]['category']}学科门类。{MAJOR_INTRODUCTIONS[major_name]['description']}",
                        source_url="mock",
                        data_source="mock",
                    ))
                elif major_name in ("临床医学",) and is_med_school:
                    continue  # skip - no med schools in our mock set
        
        # 3. 招生章程（每个学校一份）
        for school_name, info in SCHOOL_DESCRIPTIONS.items():
            chunk_id += 1
            chunks.append(RagChunk(
                chunk_id=f"rules_{chunk_id}",
                doc_type="招生章程",
                school_name=school_name,
                province="山东",
                city=info["city"],
                year=2025,
                title=f"{school_name}2025年招生章程",
                section="录取规则",
                content=f"{school_name}2025年招生录取规则：{ADMISSION_RULES}",
                source_url="mock",
                data_source="mock",
            ))
            
            # 专业调剂说明
            chunk_id += 1
            chunks.append(RagChunk(
                chunk_id=f"adjust_{chunk_id}",
                doc_type="招生章程",
                school_name=school_name,
                province="山东",
                city=info["city"],
                year=2025,
                title=f"{school_name}专业调剂说明",
                section="专业调剂",
                content=f"{school_name}在专业调剂方面实行\"分数优先、遵循志愿\"原则。考生所填报的专业志愿都无法满足时，若服从专业调剂，将根据考生成绩调剂到其他未录满的专业。若不服从调剂，则作退档处理。建议考生勾选服从专业调剂以降低退档风险。",
                source_url="mock",
                data_source="mock",
            ))
        
        # 4. 城市资料
        for city, info in CITY_DATA.items():
            chunk_id += 1
            chunks.append(RagChunk(
                chunk_id=f"city_{chunk_id}",
                doc_type="城市资料",
                city=city,
                province="山东",
                year=2025,
                title=f"{city}城市发展概况",
                section="城市定位",
                content=f"{city}是{info['定位']}。{info['产业']}。{info['就业']}",
                source_url="mock",
                data_source="mock",
            ))
        
        # 批量插入
        print(f"准备插入 {len(chunks)} 个 RAG chunk...")
        session.add_all(chunks)
        await session.commit()
        
        # 验证
        result = await session.execute(text("SELECT COUNT(*) FROM rag_chunks"))
        count = result.scalar()
        print(f"✅ RAG chunk 导入完成: {count} 个")


if __name__ == "__main__":
    asyncio.run(generate_and_import())
