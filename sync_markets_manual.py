#!/usr/bin/env python3
"""
Manual script to sync markets from Kalshi and Polymarket.

Usage:
    python3 sync_markets_manual.py

This will fetch ~100 active markets from each platform and store them in the database.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add api directory to Python path
api_dir = Path(__file__).parent / "api"
sys.path.insert(0, str(api_dir))

from services.market_sync import sync_markets, sync_price_history


async def main():
    print("=" * 60)
    print("MARKETS SYNC - Manual Run")
    print("=" * 60)
    print()

    # Step 1: Sync market metadata
    print("Step 1: Analyzing your theses...")
    print("This will extract categories, keywords, and entities from your theses")
    print("to find the most relevant prediction markets.")
    print()
    print("Step 2: Syncing market metadata from Kalshi and Polymarket...")
    print("Using thesis-driven filters for maximum relevance.")
    print()

    try:
        stats = await sync_markets()

        print("✓ Market sync complete!")
        print()
        print("Results:")
        print(f"  Kalshi:")
        print(f"    - Fetched: {stats['kalshi']['fetched']}")
        print(f"    - Inserted: {stats['kalshi']['inserted']}")
        print(f"    - Updated: {stats['kalshi']['updated']}")
        print(f"    - Errors: {stats['kalshi']['errors']}")
        print()
        print(f"  Polymarket:")
        print(f"    - Fetched: {stats['polymarket']['fetched']}")
        print(f"    - Inserted: {stats['polymarket']['inserted']}")
        print(f"    - Updated: {stats['polymarket']['updated']}")
        print(f"    - Errors: {stats['polymarket']['errors']}")
        print()

    except Exception as e:
        print(f"✗ Error during market sync: {e}")
        return

    # Price history is fetched on-demand when viewing markets
    # No need to pre-sync and store everything

    print("=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print()
    print("You can now view the markets in the web app:")
    print("  http://localhost:3001")
    print()
    print("Navigate to the 'Markets' tab to see the synced markets.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
