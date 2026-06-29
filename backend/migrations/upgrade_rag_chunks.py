"""
Migration: upgrade rag_chunks table with missing RAG metadata columns.
"""
from sqlalchemy import text
from app.core.database import engine


async def run():
    async with engine.begin() as conn:
        columns_to_add = [
            ("source_name", "VARCHAR(300)"),
            ("source_type", "VARCHAR(100) DEFAULT 'official'"),
            ("confidence", "VARCHAR(50) DEFAULT 'medium'"),
            ("permission_level", "VARCHAR(50) DEFAULT 'free'"),
            ("content_hash", "VARCHAR(100)"),
            ("crawled_at", "TIMESTAMP"),
            ("updated_at", "TIMESTAMP"),
        ]

        existing = await conn.execute(text("PRAGMA table_info(rag_chunks)"))
        existing_cols = {r[1] for r in existing.fetchall()}

        for col_name, col_type in columns_to_add:
            if col_name not in existing_cols:
                sql = f"ALTER TABLE rag_chunks ADD COLUMN {col_name} {col_type}"
                await conn.execute(text(sql))
                print(f"  Added: {col_name} {col_type}")

        # Clean: mark all existing mock rows
        await conn.execute(text("""
            UPDATE rag_chunks SET
                data_source = 'mock',
                confidence = 'mock',
                source_type = 'mock'
            WHERE data_source IS NULL OR data_source = 'mock'
        """))

    print("rag_chunks upgrade complete.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
