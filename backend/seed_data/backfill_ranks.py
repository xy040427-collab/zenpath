"""
位次反查：对 min_rank=0 的 admission_lines，从 score_rank_table 查对应位次

用法: python seed_data/backfill_ranks.py [--province 河北]
"""

import sys, os, asyncio, argparse, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.core.database import async_session_factory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_ranks")


async def backfill_ranks(province: str | None = None):
    async with async_session_factory() as session:
        where = "WHERE min_rank = 0 OR CAST(min_rank AS INTEGER) = 0"
        if province:
            where += f" AND province = :p"
            params = {"p": province}
        else:
            params = {}

        # Count
        cnt_result = await session.execute(
            text(f"SELECT COUNT(*) FROM admission_lines {where}"), params)
        total = cnt_result.scalar()
        logger.info(f"待反查: {total} 行" + (f" ({province})" if province else ""))

        if total == 0:
            return

        # Batch process by province+year for efficiency
        provs = [province] if province else [
            r[0] for r in (await session.execute(
                text(f"SELECT DISTINCT province FROM admission_lines {where}"), params)).fetchall()
        ]

        updated = 0
        for p in provs:
            p_where = where + (f" AND province = '{p}'" if not province else "")
            # Get min/max year
            yr_result = await session.execute(
                text(f"SELECT MIN(year), MAX(year) FROM admission_lines {p_where}"), params if province else {})
            yr_min, yr_max = yr_result.fetchone()

            if yr_min is None:
                continue

            for yr in range(yr_min, yr_max + 1):
                # Get all unique scores needing rank
                scores_result = await session.execute(text(f"""
                    SELECT DISTINCT CAST(min_score AS INTEGER) FROM admission_lines
                    WHERE province = :p AND year = :y
                    AND CAST(min_rank AS INTEGER) = 0 AND CAST(min_score AS INTEGER) > 0
                """), {"p": p, "y": yr})
                scores = [r[0] for r in scores_result.fetchall()]

                if not scores:
                    continue

                # Build rank lookup from score_rank_table
                placeholders = ",".join([":s" + str(i) for i in range(len(scores))])
                rank_result = await session.execute(text(f"""
                    SELECT score, rank FROM score_rank_table
                    WHERE province = :p AND year = :y
                    AND score IN ({placeholders})
                """), {"p": p, "y": yr, **{f"s{i}": s for i, s in enumerate(scores)}})
                rank_map = {r[0]: r[1] for r in rank_result.fetchall()}

                if not rank_map:
                    continue

                # Update in batches
                for score, rank in rank_map.items():
                    result = await session.execute(text(f"""
                        UPDATE admission_lines SET min_rank = :r
                        WHERE province = :p AND year = :y
                        AND CAST(min_score AS INTEGER) = :s
                        AND CAST(min_rank AS INTEGER) = 0
                    """), {"p": p, "y": yr, "s": score, "r": rank})
                    updated += result.rowcount

                await session.commit()
                logger.info(f"  {p} {yr}: {len(rank_map)} scores mapped, {updated} rows updated so far")

        await session.commit()
        logger.info(f"✅ 位次反查完成: {updated} 行已更新")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--province", type=str)
    args = parser.parse_args()
    await backfill_ranks(args.province)


if __name__ == "__main__":
    asyncio.run(main())
