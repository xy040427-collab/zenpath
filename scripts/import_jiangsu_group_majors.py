#!/usr/bin/env python3
"""
Import Jiangsu group majors and plan summary data into gaokao.db.
Source: 江苏省专业组内专业与计划数_择境版_整理包/jiangsu_group_plan_zenpath.sqlite
"""

import sqlite3, os, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / 'backend' / 'gaokao.db'
SOURCE_DB = PROJECT_ROOT / 'data' / 'jiangsu' / 'group_plan' / 'jiangsu_group_plan_zenpath.sqlite'

sys.path.insert(0, str(PROJECT_ROOT / 'backend'))
from app.services.rank_matcher import clean_school_name


def import_data():
    if not SOURCE_DB.exists():
        print(f'ERROR: Source DB not found at {SOURCE_DB}')
        sys.exit(1)

    src = sqlite3.connect(str(SOURCE_DB))
    dst = sqlite3.connect(str(DB_PATH))

    # ═══════════════════════════════════════════════
    # 1. Create jiangsu_group_majors table
    # ═══════════════════════════════════════════════
    dst.execute('DROP TABLE IF EXISTS jiangsu_group_majors')
    dst.execute('''
        CREATE TABLE jiangsu_group_majors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            province TEXT DEFAULT '江苏',
            batch TEXT,
            subject_type TEXT NOT NULL,
            school_code TEXT,
            school_name TEXT NOT NULL,
            school_name_clean TEXT NOT NULL,
            major_group_code TEXT,
            major_group_no TEXT,
            major_group_title TEXT NOT NULL,
            major_group_name TEXT,
            elective_requirement TEXT,
            group_plan_count INTEGER,
            major_code TEXT,
            major_name TEXT NOT NULL,
            major_name_clean TEXT,
            major_plan_count INTEGER,
            duration TEXT,
            tuition TEXT,
            is_sino_foreign INTEGER DEFAULT 0,
            is_joint_training INTEGER DEFAULT 0,
            is_remaining_plan INTEGER DEFAULT 0,
            notes TEXT,
            source_file TEXT
        )
    ''')

    # ═══════════════════════════════════════════════
    # 2. Create jiangsu_group_plan_summary table
    # ═══════════════════════════════════════════════
    dst.execute('DROP TABLE IF EXISTS jiangsu_group_plan_summary')
    dst.execute('''
        CREATE TABLE jiangsu_group_plan_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            province TEXT DEFAULT '江苏',
            batch TEXT,
            subject_type TEXT NOT NULL,
            school_code TEXT,
            school_name TEXT NOT NULL,
            school_name_clean TEXT NOT NULL,
            major_group_code TEXT,
            major_group_no TEXT,
            major_group_title TEXT NOT NULL,
            major_group_name TEXT,
            elective_requirement TEXT,
            group_plan_count INTEGER,
            major_count INTEGER,
            sum_major_plan_count INTEGER,
            plan_check TEXT,
            is_remaining_plan INTEGER DEFAULT 0,
            notes TEXT,
            source_file TEXT
        )
    ''')

    # ═══════════════════════════════════════════════
    # 3. Import jiangsu_group_majors
    # ═══════════════════════════════════════════════
    src_rows = src.execute('''
        SELECT year, batch, subject_type, school_code, school_name,
               major_group_code, major_group_no, major_group_title, major_group_name,
               elective_requirement, group_plan_count,
               major_code, major_name, major_name_clean, major_plan_count,
               duration, tuition,
               COALESCE(is_sino_foreign,0), COALESCE(is_joint_training,0),
               COALESCE(is_remaining_plan,0), notes, source_file
        FROM jiangsu_group_majors
    ''').fetchall()

    imported = 0
    for row in src_rows:
        (year, batch, subject_type, school_code, school_name,
         mgc, mgn, mgt, mgname, elective, gp_count,
         mc, mn, mn_clean, mp_count, dur, tuition,
         is_sf, is_jt, is_rp, notes, src_file) = row

        clean_name = clean_school_name(school_name or '')
        clean_major = mn_clean or (clean_school_name(mn) if mn else '')

        dst.execute('''
            INSERT INTO jiangsu_group_majors
            (year, batch, subject_type, school_code, school_name, school_name_clean,
             major_group_code, major_group_no, major_group_title, major_group_name,
             elective_requirement, group_plan_count,
             major_code, major_name, major_name_clean, major_plan_count,
             duration, tuition, is_sino_foreign, is_joint_training,
             is_remaining_plan, notes, source_file)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (year, batch, subject_type, school_code, school_name, clean_name,
              mgc, mgn, mgt, mgname, elective, gp_count,
              mc, mn, clean_major, mp_count,
              dur, tuition, is_sf, is_jt, is_rp, notes, src_file))
        imported += 1
        if imported % 5000 == 0:
            print(f'  Imported {imported} major rows...')

    print(f'Imported {imported} rows into jiangsu_group_majors')

    # ═══════════════════════════════════════════════
    # 4. Import jiangsu_group_plan_summary
    # ═══════════════════════════════════════════════
    src_rows = src.execute('''
        SELECT year, batch, subject_type, school_code, school_name,
               major_group_code, major_group_no, major_group_title, major_group_name,
               elective_requirement, group_plan_count,
               major_count, sum_major_plan_count, plan_check,
               notes, source_file
        FROM jiangsu_group_plan_summary
    ''').fetchall()

    imported = 0
    for row in src_rows:
        (year, batch, subject_type, school_code, school_name,
         mgc, mgn, mgt, mgname, elective, gp_count,
         mc, smpc, pcheck, notes, src_file) = row

        clean_name = clean_school_name(school_name or '')

        dst.execute('''
            INSERT INTO jiangsu_group_plan_summary
            (year, batch, subject_type, school_code, school_name, school_name_clean,
             major_group_code, major_group_no, major_group_title, major_group_name,
             elective_requirement, group_plan_count,
             major_count, sum_major_plan_count, plan_check,
             notes, source_file)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (year, batch, subject_type, school_code, school_name, clean_name,
              mgc, mgn, mgt, mgname, elective, gp_count,
              int(mc) if mc else 0, int(smpc) if smpc else 0, pcheck,
              notes, src_file))
        imported += 1

    print(f'Imported {imported} rows into jiangsu_group_plan_summary')

    # ═══════════════════════════════════════════════
    # 5. Create indices
    # ═══════════════════════════════════════════════
    dst.execute('CREATE INDEX IF NOT EXISTS idx_jgm_school_clean ON jiangsu_group_majors(school_name_clean, major_group_title)')
    dst.execute('CREATE INDEX IF NOT EXISTS idx_jgm_year_subject ON jiangsu_group_majors(year, subject_type)')
    dst.execute('CREATE INDEX IF NOT EXISTS idx_jgps_school_clean ON jiangsu_group_plan_summary(school_name_clean, major_group_title)')
    dst.execute('CREATE INDEX IF NOT EXISTS idx_jgps_year_subject ON jiangsu_group_plan_summary(year, subject_type)')

    dst.commit()

    # ═══════════════════════════════════════════════
    # 6. Verify
    # ═══════════════════════════════════════════════
    print('\n=== Verification ===')
    for table in ['jiangsu_group_majors', 'jiangsu_group_plan_summary']:
        count = dst.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        years = dst.execute(f'SELECT DISTINCT year FROM {table} ORDER BY year').fetchall()
        subjects = dst.execute(f'SELECT subject_type, COUNT(*) FROM {table} GROUP BY subject_type').fetchall()
        print(f'{table}: {count} rows, years={[y[0] for y in years]}')
        for st, c in subjects:
            print(f'  {st}: {c}')

    # Match test
    match_count = dst.execute('''
        SELECT COUNT(DISTINCT t.school_name_clean || '|' || t.major_group_full_name)
        FROM jiangsu_group_trends t
        INNER JOIN jiangsu_group_majors m
          ON t.school_name = m.school_name_clean
          AND t.major_group_full_name = m.major_group_title
        WHERE m.year=2022 AND m.subject_type = t.subject_type
    ''').fetchone()[0]
    print(f'\nMatched trend groups with majors: {match_count}')

    dst.close()
    src.close()
    print('\nDone.')


if __name__ == '__main__':
    import_data()
