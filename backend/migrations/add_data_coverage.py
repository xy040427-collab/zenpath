"""
Migration: data_coverage_status table
Tracks which provinces/years have complete data for each data type.
"""
from sqlalchemy import text
from app.core.database import engine


async def run():
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS data_coverage_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type VARCHAR(100) NOT NULL,
                province VARCHAR(50),
                year INT,
                batch VARCHAR(100),
                subject_type VARCHAR(50),
                source_name VARCHAR(300),
                source_url TEXT,
                status VARCHAR(50) DEFAULT 'missing',
                row_count INT DEFAULT 0,
                last_checked_at TIMESTAMP,
                last_imported_at TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Populate current coverage from existing data
        await conn.execute(text("""
            INSERT OR REPLACE INTO data_coverage_status (data_type, province, year, status, row_count, notes)
            SELECT 'admission_line', province, year, 'available', COUNT(*),
                   CASE WHEN SUM(CASE WHEN major_group_name IS NOT NULL AND major_group_name!='' THEN 1 ELSE 0 END)=0
                        THEN 'missing major names' ELSE '' END
            FROM admission_lines GROUP BY province, year
        """))

        await conn.execute(text("""
            INSERT OR REPLACE INTO data_coverage_status (data_type, province, year, status, row_count, notes)
            SELECT 'score_rank', province, year, 'available', COUNT(*), ''
            FROM score_rank_table GROUP BY province, year
        """))
    print("data_coverage_status migration complete.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
