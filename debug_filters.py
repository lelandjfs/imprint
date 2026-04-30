#!/usr/bin/env python3
"""Debug thesis filtering to see what's happening."""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent / "api"))

from services.thesis_analysis import analyze_all_theses
from services.market_clients import PolymarketClient

async def main():
    print("=== THESIS FILTERS ===")
    filters = await analyze_all_theses()

    print(f"\nCategories: {filters['categories']}")
    print(f"\nKeywords ({len(filters['keywords'])}):")
    for kw in sorted(list(filters['keywords'])[:15]):
        print(f"  - {kw}")

    print(f"\nEntities ({len(filters['entities'])}):")
    for entity in sorted(list(filters['entities'])[:15]):
        print(f"  - {entity}")

    # Fetch some markets and check why they don't match
    print("\n=== SAMPLE MARKETS (first 10) ===")
    client = PolymarketClient()
    markets = await client.get_markets(active=True, limit=10)

    for m in markets[:10]:
        title = m.get('question', m.get('title', 'Unknown'))
        category = m.get('category', 'None')
        print(f"\n- {title[:80]}")
        print(f"  Category: {category}")

if __name__ == "__main__":
    asyncio.run(main())
