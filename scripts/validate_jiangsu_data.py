#!/usr/bin/env python3
"""validate_jiangsu_data.py — 江苏高考数据校验脚本 (v2)"""
import sqlite3
import sys

DB_PATH = "data/jiangsu/real_data/jiangsu_gaokao_zenpath_v2.sqlite"

def validate(db_path: str) -> bool:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    all_ok = True

    def check(condition, label):
        nonlocal all_ok
        status = "✅" if condition else "❌"
        if not condition:
            all_ok = False
        print(f"  {status} {label}")

    # 1. Row counts per year/subject_type for score_segments
    print("\n📊 一分一段表 (score_segments) 行数：")
    for year in [2022, 2023, 2024, 2025]:
        for st in ["物理等科目类", "历史等科目类"]:
            cur.execute(
                "SELECT COUNT(*) FROM score_segments WHERE year=? AND subject_type=?",
                (year, st),
            )
            cnt = cur.fetchone()[0]
            print(f"  {year} {st}: {cnt}")

    total_ss = cur.execute("SELECT COUNT(*) FROM score_segments").fetchone()[0]
    check(total_ss == 1621, f"score_segments 总行数 = {total_ss} (预期 1621)")

    # 2. 2023 物理特殊检查
    cur.execute(
        "SELECT COUNT(*) FROM score_segments WHERE year=2023 AND subject_type='物理等科目类'"
    )
    cnt_2023_phy = cur.fetchone()[0]
    check(cnt_2023_phy == 240, f"2023 物理等科目类行数 = {cnt_2023_phy} (预期 240)")

    cur.execute(
        "SELECT MIN(score), MAX(score) FROM score_segments WHERE year=2023 AND subject_type='物理等科目类'"
    )
    min_s, max_s = cur.fetchone()
    check(min_s == 448, f"2023 物理最低分 = {min_s} (预期 448)")
    check(max_s == 687, f"2023 物理最高分 = {max_s} (预期 687)")

    # 3. Row counts per year/subject_type for admission_lines
    print("\n📊 投档线 (admission_lines) 行数：")
    for year in [2022, 2023, 2024, 2025]:
        for st in ["物理等科目类", "历史等科目类"]:
            cur.execute(
                "SELECT COUNT(*) FROM admission_lines WHERE year=? AND subject_type=?",
                (year, st),
            )
            cnt = cur.fetchone()[0]
            print(f"  {year} {st}: {cnt}")

    total_al = cur.execute("SELECT COUNT(*) FROM admission_lines").fetchone()[0]
    check(total_al == 15553, f"admission_lines 总行数 = {total_al} (预期 15553)")

    # 4. 空 source_url 检查
    cur.execute("SELECT COUNT(*) FROM score_segments WHERE source_url IS NULL OR source_url = ''")
    null_ss = cur.fetchone()[0]
    check(null_ss == 0, f"score_segments 空 source_url: {null_ss} 条")

    cur.execute("SELECT COUNT(*) FROM admission_lines WHERE source_url IS NULL OR source_url = ''")
    null_al = cur.fetchone()[0]
    check(null_al == 0, f"admission_lines 空 source_url: {null_al} 条")

    # 5. subject_type 混乱检查
    cur.execute(
        "SELECT DISTINCT subject_type FROM score_segments"
    )
    types = [r[0] for r in cur.fetchall()]
    check(
        set(types) == {"物理等科目类", "历史等科目类"},
        f"score_segments subject_type: {types}",
    )

    cur.execute(
        "SELECT DISTINCT subject_type FROM admission_lines"
    )
    types_al = [r[0] for r in cur.fetchall()]
    check(
        set(types_al) == {"物理等科目类", "历史等科目类"},
        f"admission_lines subject_type: {types_al}",
    )

    # 6. 分数范围检查（每个年份+科类）
    print("\n📊 分数范围检查：")
    for year in [2022, 2023, 2024, 2025]:
        for st in ["物理等科目类", "历史等科目类"]:
            cur.execute(
                "SELECT MIN(score), MAX(score) FROM score_segments WHERE year=? AND subject_type=?",
                (year, st),
            )
            mn, mx = cur.fetchone()
            print(f"  {year} {st}: {mn}–{mx}")

    # 7. cumulative_rank 单调性检查 (每个 year+subject_type 组合)
    print("\n📊 累计位次单调性检查：")
    for year in [2022, 2023, 2024, 2025]:
        for st in ["物理等科目类", "历史等科目类"]:
            cur.execute(
                "SELECT score, cumulative_rank FROM score_segments WHERE year=? AND subject_type=? ORDER BY score DESC",
                (year, st),
            )
            rows = cur.fetchall()
            wrong = 0
            for i in range(1, len(rows)):
                if rows[i][1] <= rows[i-1][1]:
                    wrong += 1
            status = "✅" if wrong == 0 else f"❌ {wrong} 处异常"
            print(f"  {year} {st}: {status}")

    conn.close()
    return all_ok

if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    ok = validate(DB_PATH)
    print(f"\n{'='*40}")
    print(f"{'✅ 全部校验通过' if ok else '❌ 存在校验失败，请先修数据再继续'}")
    sys.exit(0 if ok else 1)
