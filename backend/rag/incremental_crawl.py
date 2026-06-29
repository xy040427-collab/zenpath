"""
择境 ZENPATH — RAG 知识库增量抓取脚本

用于日常增量更新 RAG 知识库。
支持两种模式：
  1. priority: 按优先级顺序抓取
  2. delta: 只抓取尚未有覆盖的学校/doc_type
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rag.crawler.real_crawler import crawl_school, crawl_batch
from rag.pipeline import get_db, get_rag_coverage, update_coverage, generate_coverage_report

logger = logging.getLogger(__name__)


async def delta_crawl(max_schools: int = 50):
    """
    Delta crawl: only crawl schools that are missing specific doc types.
    This is the most efficient mode for ongoing updates.
    """
    priority_file = Path(__file__).resolve().parent.parent.parent / "rag_output" / "school_rag_priority_list.json"
    with open(priority_file, 'r', encoding='utf-8') as f:
        schools = json.load(f)
    
    # Get current coverage
    coverage = get_rag_coverage()
    
    # Filter to schools with < 3 doc types covered
    delta_schools = []
    for s in schools:
        name = s['school_name']
        cov = coverage.get(name, {})
        if len(cov) < 3:  # Missing at least some doc types
            delta_schools.append(s)
    
    # Prioritize P0/P1
    delta_schools.sort(key=lambda x: (-x['priority_score'], x['ranking_position']))
    target = delta_schools[:max_schools]
    
    print(f"Delta crawl: {len(target)} schools with incomplete coverage")
    results = await crawl_batch(target, max_per_school=3)
    
    # Update coverage after crawl
    priority_list = schools
    update_coverage(priority_list)
    
    return results


async def priority_crawl(tier: str = "P0", max_schools: int = 50):
    """
    Priority crawl: crawl schools in a specific tier.
    """
    priority_file = Path(__file__).resolve().parent.parent.parent / "rag_output" / "school_rag_priority_list.json"
    with open(priority_file, 'r', encoding='utf-8') as f:
        schools = json.load(f)
    
    target = [s for s in schools if s['priority_tier'] == tier][:max_schools]
    
    print(f"Priority crawl: {len(target)} {tier} schools")
    results = await crawl_batch(target, max_per_school=3)
    
    update_coverage(schools)
    return results


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "delta"
    max_schools = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    tier = sys.argv[3] if len(sys.argv) > 3 else "P0"
    
    print(f"\n{'='*60}")
    print(f"  择境 ZENPATH — RAG 增量抓取")
    print(f"  Mode: {mode}, Max: {max_schools}")
    print(f"{'='*60}\n")
    
    if mode == "delta":
        results = asyncio.run(delta_crawl(max_schools))
    elif mode == "priority":
        results = asyncio.run(priority_crawl(tier, max_schools))
    else:
        print(f"Unknown mode: {mode}")
        return
    
    # Print summary
    total_inserted = sum(r.get('inserted', 0) for r in results)
    print(f"\n✅ Done: {total_inserted} new chunks inserted")


if __name__ == "__main__":
    main()
