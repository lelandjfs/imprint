#!/usr/bin/env python3
"""
Manual script to compute thesis-market alignments using Claude.

Usage:
    python3 compute_alignments_manual.py

This will analyze all your theses against all active markets and store alignment scores.
Note: This uses Claude API and may take a few minutes for many thesis-market pairs.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add api directory to Python path
api_dir = Path(__file__).parent / "api"
sys.path.insert(0, str(api_dir))

from services.thesis_alignment import compute_all_alignments


async def main():
    print("=" * 70)
    print("THESIS-MARKET ALIGNMENT COMPUTATION")
    print("=" * 70)
    print()
    print("This will use Claude to analyze how prediction markets relate to your")
    print("investment theses.")
    print()
    print("Note: This uses the Anthropic API and may take a few minutes.")
    print()

    try:
        stats = await compute_all_alignments(min_score=0.3)

        print("✓ Alignment computation complete!")
        print()
        print("Results:")
        print(f"  - Theses analyzed: {stats['theses']}")
        print(f"  - Markets analyzed: {stats['markets']}")
        print(f"  - Total comparisons: {stats['alignments_computed']}")
        print(f"  - Alignments stored (score ≥ 0.3): {stats['alignments_stored']}")
        print(f"  - Errors: {stats['errors']}")
        print()

        if stats['alignments_stored'] > 0:
            print("=" * 70)
            print("SUCCESS - Markets are now aligned to your theses!")
            print("=" * 70)
            print()
            print("You can now view aligned markets in the web app:")
            print("  http://localhost:3001")
            print()
            print("Navigate to the 'Markets' tab:")
            print("  - Explore: See markets relevant to ALL your theses")
            print("  - Thesis Alignment: Deep dive into markets for ONE thesis")
            print()
        else:
            print("No alignments found. This could mean:")
            print("  - No theses exist (create some in the Thesis tab)")
            print("  - No markets matched your theses (try broader theses)")
            print("  - Alignment scores were all below 0.3")
            print()

    except Exception as e:
        print(f"✗ Error during alignment computation: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    asyncio.run(main())
