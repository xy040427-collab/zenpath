#!/usr/bin/env python3
"""Generate complete 863-school data file from Urongda school map."""

import json

# Province code mapping (from school code prefix at positions 2-3)
PROVINCE_MAP = {
    '11': '北京', '12': '天津', '13': '河北', '14': '山西', '15': '内蒙古',
    '21': '辽宁', '22': '吉林', '23': '黑龙江',
    '31': '上海', '32': '江苏', '33': '浙江', '34': '安徽', '35': '福建',
    '36': '江西', '37': '山东',
    '41': '河南', '42': '湖北', '43': '湖南', '44': '广东', '45': '广西', '46': '海南',
    '50': '重庆', '51': '四川', '52': '贵州', '53': '云南', '54': '西藏',
    '61': '陕西', '62': '甘肃', '63': '青海', '64': '宁夏', '65': '新疆'
}

# Province capital cities
CAPITAL_MAP = {
    '北京': '北京', '天津': '天津', '河北': '石家庄', '山西': '太原', '内蒙古': '呼和浩特',
    '辽宁': '沈阳', '吉林': '长春', '黑龙江': '哈尔滨',
    '上海': '上海', '江苏': '南京', '浙江': '杭州', '安徽': '合肥', '福建': '福州',
    '江西': '南昌', '山东': '济南',
    '河南': '郑州', '湖北': '武汉', '湖南': '长沙', '广东': '广州', '广西': '南宁', '海南': '海口',
    '重庆': '重庆', '四川': '成都', '贵州': '贵阳', '云南': '昆明', '西藏': '拉萨',
    '陕西': '西安', '甘肃': '兰州', '青海': '西宁', '宁夏': '银川', '新疆': '乌鲁木齐'
}

def get_type_from_name(name):
    """Determine school type from name keywords."""
    keywords = {
        '师范': '师范',
        '理工': '理工',
        '工业': '理工',
        '工程': '理工',
        '科技': '理工',
        '邮电': '理工',
        '交通': '理工',
        '电力': '理工',
        '石油': '理工',
        '化工': '理工',
        '航空': '理工',
        '航天': '理工',
        '海事': '理工',
        '海洋': '理工',
        '电子': '理工',
        '信息': '理工',
        '建筑': '理工',
        '冶金': '理工',
        '矿业': '理工',
        '地质': '理工',
        '水利': '理工',
        '纺织': '理工',
        '农林': '农林',
        '农业': '农林',
        '林业': '农林',
        '医学': '医药',
        '医药': '医药',
        '医': '医药',
        '药': '医药',
        '中医': '医药',
        '艺术': '艺术',
        '美术': '艺术',
        '音乐': '艺术',
        '戏剧': '艺术',
        '电影': '艺术',
        '舞蹈': '艺术',
        '传媒': '综合',
        '财经': '财经',
        '经济': '财经',
        '金融': '财经',
        '外国语': '综合',
        '外语': '综合',
        '体育': '体育',
        '政法': '政法',
        '警察': '政法',
        '公安': '政法',
        '民族': '综合',
        '综合': '综合',
        '学院': '综合',
        '大学': '综合',
        '职业': '理工',
        '技术': '理工',
    }
    for kw, typ in keywords.items():
        if kw in name:
            return typ
    return '综合'

def get_tags(name, school_type, province):
    """Generate appropriate tags."""
    tags = ['普通高校']
    
    # Special known universities get specific tags
    special_tags = {
        '北京大学': ['双一流', 'C9联盟', '文理强校'],
        '清华大学': ['双一流', 'C9联盟', '工科强校'],
        '中国人民大学': ['双一流', '人文社科强校'],
        '北京航空航天大学': ['双一流', '国防七子', '工科强校'],
        '北京理工大学': ['双一流', '国防七子'],
        '北京师范大学': ['双一流', '师范强校'],
        '中国农业大学': ['双一流', '农学强校'],
        '中央民族大学': ['双一流', '民族强校'],
        '中国科学院大学': ['双一流', '科研强校'],
        '北京交通大学': ['双一流', '交通强校'],
        '北京科技大学': ['双一流', '工科强校'],
        '北京邮电大学': ['双一流', '两电一邮'],
        '北京化工大学': ['双一流', '工科强校'],
        '北京外国语大学': ['双一流', '外语强校'],
        '北京中医药大学': ['双一流', '中医强校'],
        '北京体育大学': ['双一流', '体育强校'],
        '中国传媒大学': ['双一流', '传媒强校'],
        '中国政法大学': ['双一流', '法学强校'],
        '中国石油大学': ['双一流', '石油强校'],
        '华北电力大学': ['双一流', '电力强校'],
        '中央音乐学院': ['双一流', '音乐强校'],
        '中央美术学院': ['双一流', '美术强校'],
        '中央戏剧学院': ['双一流', '戏剧强校'],
        '首都师范大学': ['双一流', '师范强校'],
        '南开大学': ['双一流', '文理强校'],
        '天津大学': ['双一流', '工科强校'],
        '天津工业大学': ['双一流', '纺织强校'],
        '复旦大学': ['双一流', 'C9联盟'],
        '上海交通大学': ['双一流', 'C9联盟', '工科强校'],
        '同济大学': ['双一流', '建筑老八校'],
        '华东师范大学': ['双一流', '师范强校'],
        '华东理工大学': ['双一流', '工科强校'],
        '上海外国语大学': ['双一流', '外语强校'],
        '上海财经大学': ['双一流', '财经强校'],
        '上海中医药大学': ['双一流', '中医强校'],
        '上海海洋大学': ['双一流', '海洋强校'],
        '上海音乐学院': ['双一流', '音乐强校'],
        '上海科技大学': ['双一流', '科研强校'],
        '东华大学': ['双一流', '纺织强校'],
        '重庆大学': ['双一流', '建筑老八校'],
        '大连理工大学': ['双一流', '工科强校'],
        '东北大学': ['双一流', '工科强校'],
        '吉林大学': ['双一流', '学科齐全'],
        '东北师范大学': ['双一流', '师范强校'],
        '延边大学': ['双一流', '边疆强校'],
        '哈尔滨工业大学': ['双一流', 'C9联盟', '国防七子'],
        '哈尔滨工程大学': ['双一流', '国防七子'],
        '东南大学': ['双一流', '建筑老八校'],
        '南京理工大学': ['双一流', '国防七子'],
        '南京师范大学': ['双一流', '师范强校'],
        '南京信息工程大学': ['双一流', '气象强校'],
        '南京邮电大学': ['双一流', '两电一邮'],
        '南京中医药大学': ['双一流', '中医强校'],
        '苏州大学': ['双一流', '最美校园'],
        '江南大学': ['双一流', '食品强校'],
        '河海大学': ['双一流', '水利强校'],
        '浙江大学': ['双一流', 'C9联盟', '学科齐全'],
        '中国美术学院': ['双一流', '美术强校'],
        '宁波大学': ['双一流', '地方强校'],
        '中国科学技术大学': ['双一流', 'C9联盟', '理科强校'],
        '厦门大学': ['双一流', '最美校园'],
        '福州大学': ['双一流', '工科强校'],
        '山东大学': ['双一流', '文理强校'],
        '中国海洋大学': ['双一流', '海洋强校'],
        '郑州大学': ['双一流', '中原第一'],
        '武汉大学': ['双一流', '最美校园'],
        '华中科技大学': ['双一流', '工科强校'],
        '华中农业大学': ['双一流', '农学强校'],
        '中南大学': ['双一流', '工科强校'],
        '湖南大学': ['双一流', '建筑老八校'],
        '湖南师范大学': ['双一流', '师范强校'],
        '中山大学': ['双一流', '华南第一'],
        '华南理工大学': ['双一流', '建筑老八校'],
        '华南师范大学': ['双一流', '师范强校'],
        '暨南大学': ['双一流', '侨校强校'],
        '广州中医药大学': ['双一流', '中医强校'],
        '南方科技大学': ['双一流', '科研强校'],
        '广西大学': ['双一流', '华南强校'],
        '四川大学': ['双一流', '西南第一'],
        '电子科技大学': ['双一流', '两电一邮'],
        '西南交通大学': ['双一流', '交通强校'],
        '西南财经大学': ['双一流', '财经强校'],
        '四川农业大学': ['双一流', '农学强校'],
        '成都理工大学': ['双一流', '地质强校'],
        '贵州大学': ['双一流', '地方强校'],
        '云南大学': ['双一流', '生态强校'],
        '西藏大学': ['双一流', '高原强校'],
        '西安交通大学': ['双一流', 'C9联盟'],
        '西北工业大学': ['双一流', '国防七子'],
        '西安电子科技大学': ['双一流', '两电一邮'],
        '西北大学': ['双一流', '文理强校'],
        '长安大学': ['双一流', '交通强校'],
        '陕西师范大学': ['双一流', '师范强校'],
        '兰州大学': ['双一流', '文理强校'],
        '青海大学': ['双一流', '高原强校'],
        '新疆大学': ['双一流', '边疆强校'],
    }
    
    # Check if the school matches any special tag entry (by prefix matching)
    for key, val in special_tags.items():
        if name.startswith(key):
            return val
    
    # Generate tags based on type
    type_tags = {
        '师范': ['普通高校'],
        '理工': ['普通高校'],
        '农林': ['普通高校'],
        '医药': ['普通高校'],
        '艺术': ['普通高校'],
        '财经': ['普通高校'],
        '体育': ['普通高校'],
        '政法': ['普通高校'],
        '综合': ['普通高校'],
    }
    return type_tags.get(school_type, ['普通高校'])


def generate_description(name, school_type, province):
    """Generate a description for the school."""
    type_desc = {
        '师范': '省属重点师范院校，教师教育特色鲜明。',
        '理工': '省属理工类院校，工程技术学科实力突出。',
        '农林': '农林类院校，农业与生命科学特色鲜明。',
        '医药': '医药类院校，医学与药学学科特色鲜明。',
        '艺术': '艺术类院校，艺术与设计学科特色鲜明。',
        '财经': '财经类院校，经济与管理学科特色鲜明。',
        '体育': '体育类院校，体育学科特色鲜明。',
        '政法': '政法类院校，法学学科特色鲜明。',
        '综合': '省属综合性院校，多学科协调发展。',
    }
    base_desc = type_desc.get(school_type, '省属高等院校，多学科协调发展。')
    return f"{name}是{province}{base_desc}"


# Load data files
with open('/home/xiaoyu/projects/gaokao-volunteer/public/university-logos/data/urongda_school_map.json', 'r', encoding='utf-8') as f:
    urongda_map = json.load(f)

with open('/home/xiaoyu/projects/gaokao-volunteer/gaokao_data/all_universities_data.json', 'r', encoding='utf-8') as f:
    existing_schools = json.load(f)

# Build a lookup by slug for existing schools
existing_by_slug = {}
for school in existing_schools:
    existing_by_slug[school['slug']] = school

print(f"Urongda schools: {len(urongda_map)}")
print(f"Existing schools: {len(existing_schools)}")

# Also build a lookup by name to handle name variations
existing_by_name = {}
for school in existing_schools:
    existing_by_name[school['name']] = school

# Process all schools
schools = []
next_id = 112  # Start from 112 since existing IDs go up to 111
matched_count = 0
new_count = 0

# Sort schools by code for deterministic output
sorted_codes = sorted(urongda_map.keys())

for code in sorted_codes:
    entry = urongda_map[code]
    slug = entry['slug']
    name = entry['name']
    
    # Try to match by slug first
    if slug in existing_by_slug:
        school = existing_by_slug[slug]
        schools.append(school)
        matched_count += 1
        continue
    
    # Try to match by name
    if name in existing_by_name:
        school = existing_by_name[name]
        schools.append(school)
        matched_count += 1
        continue
    
    # Generate new school entry
    province_code = code[2:4]
    province = PROVINCE_MAP.get(province_code, '未知')
    city = CAPITAL_MAP.get(province, province)
    school_type = get_type_from_name(name)
    tags = get_tags(name, school_type, province)
    description = generate_description(name, school_type, province)
    
    # Generate website
    if 'edu.cn' in slug or slug.endswith('edu'):
        website = f"https://www.{slug}.edu.cn"
    else:
        # Try common patterns
        if slug.startswith('china-') or slug.startswith('university-of-'):
            website = f"https://www.{slug.replace('-', '')}.edu.cn"
        else:
            domain = slug.replace('-', '').replace('_', '')
            website = f"https://www.{domain}.edu.cn"
    
    school = {
        'id': str(next_id),
        'slug': slug,
        'name': name,
        'province': province,
        'city': city,
        'type': school_type,
        'level': '普通',
        'isPublic': True,
        'tags': tags,
        'description': description,
        'website': website
    }
    schools.append(school)
    next_id += 1
    new_count += 1

print(f"Matched schools: {matched_count}")
print(f"New schools: {new_count}")
print(f"Total schools: {len(schools)}")

# Collect unique provinces sorted
provinces_set = set()
for school in schools:
    provinces_set.add(school['province'])

# Sort provinces
province_order = [
    '北京', '天津', '河北', '山西', '内蒙古',
    '辽宁', '吉林', '黑龙江',
    '上海', '江苏', '浙江', '安徽', '福建', '江西', '山东',
    '河南', '湖北', '湖南', '广东', '广西', '海南',
    '重庆', '四川', '贵州', '云南', '西藏',
    '陕西', '甘肃', '青海', '宁夏', '新疆'
]
provinces_sorted = [p for p in province_order if p in provinces_set]
print(f"Provinces: {provinces_sorted}")

# Generate TypeScript file
def format_school(s):
    tags_str = ', '.join(f'"{t}"' for t in s['tags'])
    return (
        f"  {{ id: '{s['id']}', slug: '{s['slug']}', name: '{s['name']}', "
        f"province: '{s['province']}', city: '{s['city']}', type: '{s['type']}', "
        f"level: '{s['level']}', isPublic: {str(s['isPublic']).lower()}, "
        f"tags: [{tags_str}], "
        f"description: '{s['description']}', website: '{s['website']}' }}"
    )

lines = []
lines.append("// Auto-generated schools data from Urongda school map")
lines.append("// Contains all 863 schools from the Urongda dataset")
lines.append("")
lines.append("export interface SchoolItem {")
lines.append("  id: string;")
lines.append("  slug: string;")
lines.append("  name: string;")
lines.append("  province: string;")
lines.append("  city: string;")
lines.append("  type: string;")
lines.append("  level: string;")
lines.append("  isPublic: boolean;")
lines.append("  tags: string[];")
lines.append("  description: string;")
lines.append("  website: string;")
lines.append("}")
lines.append("")
lines.append(f"export const SCHOOLS: SchoolItem[] = [")
for i, s in enumerate(schools):
    comma = ',' if i < len(schools) - 1 else ''
    lines.append(f"  {json.dumps(s, ensure_ascii=False)}{comma}")
lines.append("];")
lines.append("")
lines.append(f"export const PROVINCES = {json.dumps(['全部'] + provinces_sorted, ensure_ascii=False)};")

output = '\n'.join(lines)

with open('/home/xiaoyu/projects/gaokao-volunteer/dyad-output/src/data/schools_data.ts', 'w', encoding='utf-8') as f:
    f.write(output)

print(f"\nFile written: /home/xiaoyu/projects/gaokao-volunteer/dyad-output/src/data/schools_data.ts")
print(f"File size: {len(output)} bytes")
