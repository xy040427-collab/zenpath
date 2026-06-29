#!/usr/bin/env python3
"""
Import schools from TypeScript data into the SQLite database.

Usage:
    cd backend/
    python3 seed_data/import_schools.py

Reads:
  - dyad-output/src/data/schools_data.ts     → SCHOOLS array
  - dyad-output/src/data/urongda_logo_map.ts → logo slug mapping
"""

import asyncio
import json
import logging
import os
import sys

# Add backend/ to sys.path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("import_schools")

# ── Paths ──────────────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
SCHOOLS_FILE = os.path.join(PROJECT_ROOT, "dyad-output", "src", "data", "schools_data.ts")
LOGO_MAP_FILE = os.path.join(PROJECT_ROOT, "dyad-output", "src", "data", "urongda_logo_map.ts")


def extract_bracketed_json(text: str, marker: str) -> str:
    """Extract the JSON array/object that follows *marker* in *text*.

    Uses bracket-depth counting so it handles nested arrays/objects
    and ignores trailing content (e.g. a second export).
    """
    idx = text.index(marker) + len(marker)
    # Skip whitespace before the opening bracket
    while idx < len(text) and text[idx] in (" ", "\n", "\t", "\r"):
        idx += 1
    opening = text[idx]
    assert opening in ("[", "{"), f"Expected '[' or '{{' after marker, got {repr(opening)}"
    closing = "]" if opening == "[" else "}"
    depth = 0
    for i in range(idx, len(text)):
        if text[i] == opening:
            depth += 1
        elif text[i] == closing:
            depth -= 1
            if depth == 0:
                return text[idx : i + 1]
    raise ValueError(f"Could not find matching '{closing}' for marker {marker!r}")


def parse_schools_file() -> list[dict]:
    """Read and parse the SCHOOLS array from school_data.ts."""
    with open(SCHOOLS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    json_str = extract_bracketed_json(content, "SCHOOLS: SchoolItem[] =")
    return json.loads(json_str)


def parse_logo_map() -> dict[str, str]:
    """Read and parse URONDA_LOGO_MAP from urongda_logo_map.ts."""
    import ast
    with open(LOGO_MAP_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    json_str = extract_bracketed_json(content, "URONDA_LOGO_MAP: Record<string, string> =")
    # The file uses single quotes (valid Python syntax), so use ast.literal_eval
    return ast.literal_eval(json_str)


async def import_schools():
    """Main import routine."""
    from app.core.database import async_session_factory, Base, engine
    from app.models.models import School, gen_id
    from sqlalchemy import delete

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Reading schools data…")
    raw_schools = parse_schools_file()
    logger.info(f"  → {len(raw_schools)} schools in TypeScript data")

    logo_map = parse_logo_map()
    logger.info(f"  → {len(logo_map)} entries in logo map")

    async with async_session_factory() as session:
        # Delete existing records for idempotency
        logger.info("Deleting existing School records…")
        await session.execute(delete(School))
        await session.commit()
        logger.info("  ✓ All existing records deleted.")

        # Insert new records
        count = 0
        errors = 0
        for i, item in enumerate(raw_schools):
            try:
                name = item["name"]
                # Prefer logo from urongda_logo_map; fall back to slug in data
                logo_slug = logo_map.get(name, item.get("slug", ""))

                school = School(
                    id=item.get("id", gen_id()),
                    slug=item["slug"],
                    name=name,
                    province=item["province"],
                    city=item.get("city", ""),
                    type=item.get("type", "综合"),
                    level=item.get("level", "普通"),
                    ranking=int(item.get("ranking", 9999)),
                    is_public=item.get("isPublic", True),
                    tags=item.get("tags", []),
                    description=item.get("description", ""),
                    website=item.get("website", ""),
                    logo_slug=logo_slug,
                )
                session.add(school)
                count += 1

                # Progress every 100
                if count % 100 == 0:
                    logger.info(f"  ➜ {count} schools added so far…")
                    await session.flush()

            except Exception as e:
                errors += 1
                logger.warning(
                    f"  ⚠ Failed to import school #{i} "
                    f"({item.get('name', 'unknown')}): {e}"
                )

        await session.commit()
        logger.info(
            f"\n✅ Import complete: {count} schools added, "
            f"{errors} errors, {count - errors} total success."
        )


if __name__ == "__main__":
    asyncio.run(import_schools())
