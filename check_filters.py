#!/usr/bin/env python3
"""Check what filters were extracted from theses."""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "api"))

from services.thesis_analysis import analyze_all_theses

async def main():
    print("=== ANALYZING THESES TO EXTRACT FILTERS ===\n")

    filters = await analyze_all_theses()

    print(f"Categories ({len(filters['categories'])}):")
    for cat in sorted(filters['categories']):
        print(f"  - {cat}")

    print(f"\nKeywords ({len(filters['keywords'])}):")
    for kw in sorted(list(filters['keywords'])[:20]):  # Show first 20
        print(f"  - {kw}")
    if len(filters['keywords']) > 20:
        print(f"  ... and {len(filters['keywords']) - 20} more")

    print(f"\nEntities ({len(filters['entities'])}):")
    for entity in sorted(list(filters['entities'])[:20]):  # Show first 20
        print(f"  - {entity}")
    if len(filters['entities']) > 20:
        print(f"  ... and {len(filters['entities']) - 20} more")

if __name__ == "__main__":
    asyncio.run(main())
