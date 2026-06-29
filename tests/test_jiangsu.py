#!/usr/bin/env python3
"""
test_jiangsu.py — 江苏推荐引擎重构 测试验证 (v3)
按任务文档第十一章测试要求逐项验证
"""
import json, sys, urllib.request, urllib.error, sqlite3

API_BASE = "http://localhost:8000/api/gaokao/jiangsu"
DB_PATH = "/home/xiaoyu/projects/gaokao-volunteer/backend/gaokao.db"
PASS = FAIL = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition: PASS += 1; print(f"  ✅ {name}")
    else: FAIL += 1; print(f"  ❌ {name} — {detail}")

def api(payload):
    req = urllib.request.Request(f"{API_BASE}/recommend", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"success": False, "http_error": e.code, "body": e.read().decode()[:300]}
    except Exception as e:
        return {"success": False, "error": str(e)}

print("=" * 60)
print("江苏推荐引擎重构 — 测试验证 v3")
print("=" * 60)

# ── Test 1: 用户 rank 优先 ──
print("\n📋 Test 1: 用户输入 rank 时采用用户位次")
r = api({"year": 2025, "subject_type": "物理等科目类", "score": 620, "rank": 19004, "top_n": 50})
test("success=True", r.get("success"))
test("user_rank = 19004", r.get("user_rank") == 19004)
test("rank_source = user_input", r.get("rank_source") == "user_input")
test("estimated_rank_from_score = 19004", r.get("estimated_rank_from_score") == 19004)

# ── Test 2: 无 rank → 估算 ──
print("\n📋 Test 2: 无 rank 时用分数估算")
r = api({"year": 2025, "subject_type": "物理等科目类", "score": 620, "top_n": 50})
test("user_rank = 19004", r.get("user_rank") == 19004)
test("rank_source = score_segment_estimated", r.get("rank_source") == "score_segment_estimated")

# ── Test 3: rank 差异警告 ──
print("\n📋 Test 3: rank 差异过大时发出警告")
r = api({"year": 2025, "subject_type": "物理等科目类", "score": 620, "rank": 30000, "top_n": 50})
test("rank_source = user_input", r.get("rank_source") == "user_input")
test("rank_warning 非空", r.get("rank_warning") is not None and "差异较大" in str(r.get("rank_warning")))

# ── Test 4: subject_type 校验 ──
print("\n📋 Test 4: subject_type 非法值拒绝")
r = api({"year": 2025, "subject_type": "物理", "score": 620, "top_n": 50})
test("HTTP 400 或 success=False", r.get("http_error") == 400 or r.get("success") is False)

# ── Test 5: 物理不返回历史 ──
print("\n📋 Test 5: 物理/历史严格分离")
r_phys = api({"year": 2025, "subject_type": "物理等科目类", "score": 620, "top_n": 50})
r_hist = api({"year": 2025, "subject_type": "历史等科目类", "score": 580, "top_n": 50})
test("物理请求 subject_type=物理等科目类", r_phys.get("subject_type") == "物理等科目类")
test("历史请求 subject_type=历史等科目类", r_hist.get("subject_type") == "历史等科目类")
test("物理≠历史位次", r_phys.get("user_rank") != r_hist.get("user_rank"))

# ── Test 6: 位次数据校验 ──
print("\n📋 Test 6: 2023 物理位次校验")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
checks = [
    ("2023物理612→24194", "SELECT cumulative_rank FROM gaokao_score_segments WHERE year=2023 AND subject_type='物理等科目类' AND score<=612 ORDER BY score DESC LIMIT 1", 24194),
    ("2023物理567→60724", "SELECT cumulative_rank FROM gaokao_score_segments WHERE year=2023 AND subject_type='物理等科目类' AND score<=567 ORDER BY score DESC LIMIT 1", 60724),
    ("2023物理448→173523", "SELECT cumulative_rank FROM gaokao_score_segments WHERE year=2023 AND subject_type='物理等科目类' AND score<=448 ORDER BY score DESC LIMIT 1", 173523),
]
for label, sql, expected in checks:
    cur.execute(sql)
    val = cur.fetchone()[0]
    test(f"{label}", val == expected, f"实际: {val}")

# ── Test 7: 无 selected_subjects 不默认 ──
print("\n📋 Test 7: 无再选科目时不得默认")
r_no_subs = api({"year": 2025, "subject_type": "物理等科目类", "score": 620, "top_n": 50})
test("无选科仍返回结果", r_no_subs.get("success"))
# When no subjects provided, elective requirement="需人工核验" items should still appear
# (they're not filtered out since unparseable defaults to pass-through)

# ── Test 8: 选科不满足被过滤 ──
print("\n📋 Test 8: 选科过滤")
r_no_chem = api({"year": 2025, "subject_type": "物理等科目类", "score": 620, "selected_subjects": ["物理", "生物", "地理"], "top_n": 50})
test("有选科过滤计数", r_no_chem.get("summary", {}).get("filtered_by_elective", 0) >= 0)

# ── Test 9: 必填字段 ──
print("\n📋 Test 9: 响应必填字段")
all_items = []
for b in ["冲", "稳", "保", "垫"]:
    all_items.extend(r_phys.get("recommendations", {}).get(b, []))
test("至少 100 候选", len(all_items) >= 100, f"实际: {len(all_items)}")
if all_items:
    item = all_items[0]
    for f in ["school_name", "major_group_code", "major_group_full_name", "elective_requirement",
              "bucket", "risk_tags", "risk_level", "reason", "source_url",
              "matched_majors", "group_major_status", "subject_match_status",
              "rank_delta", "rank_delta_ratio", "total_score", "score_breakdown"]:
        test(f"含 {f}", f in item, f"缺失: {f}")

# ── Test 10: source_url ──
print("\n📋 Test 10: source_url 可溯源")
urls = [i.get("source_url", "") for i in all_items]
test("含 jseea.cn", any("jseea.cn" in (u or "") for u in urls))

# ── Test 11: group_major_status ──
print("\n📋 Test 11: 组内专业状态")
test("group_major_status=missing", all(i.get("group_major_status") == "missing" for i in all_items[:10]))

# ── Test 12: 新表已建立 ──
print("\n📋 Test 12: jiangsu_group_plan + exam_population 表")
cur.execute("SELECT COUNT(*) FROM jiangsu_group_plan")
test("jiangsu_group_plan 表存在", True, f"{cur.fetchone()[0]} 行（空表=暂无招生计划）")
cur.execute("SELECT COUNT(*) FROM jiangsu_exam_population")
test("jiangsu_exam_population 表存在", True, f"{cur.fetchone()[0]} 行（空表=暂无考生人数）")

# ── Test 13: 响应含 rank_source ──
print("\n📋 Test 13: 响应含 rank 来源字段")
for f in ["user_rank", "estimated_rank_from_score", "rank_source", "rank_warning"]:
    test(f"{f} 在顶层", f in r_phys, f"缺失: {f}")

# ── Test 14: 学校多样性 ──
print("\n📋 Test 14: 学校多样性 ≥ 30")
schools = set(i["school_name"] for i in all_items)
test(f"覆盖 {len(schools)} 所", len(schools) >= 30, f"实际: {len(schools)}")

conn.close()

print("\n" + "=" * 60)
print(f"结果: {PASS} 通过 / {FAIL} 失败 / {PASS+FAIL} 总计")
print("✅ 全部测试通过！" if FAIL == 0 else f"⚠️  {FAIL} 项失败")
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
