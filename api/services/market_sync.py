"""
Market synchronization service for Kalshi and Polymarket.

Handles fetching market data from external APIs and storing in database.
"""

import asyncio
import logging
from typing import List, Optional, Set
from datetime import datetime, timedelta
from utils import get_db_connection
from services.market_clients import KalshiClient, PolymarketClient
from services.thesis_analysis import analyze_all_theses

logger = logging.getLogger(__name__)


async def sync_markets() -> dict:
    """
    Sync market metadata from Kalshi and Polymarket using thesis-driven discovery.

    Flow:
    1. Analyze theses to extract categories, keywords, and entities
    2. Fetch markets from relevant categories
    3. Filter by thesis-derived keywords and entities
    4. Store in database

    Returns:
        Dictionary with sync statistics
    """
    logger.info("Starting thesis-driven market sync...")

    kalshi_client = KalshiClient()
    polymarket_client = PolymarketClient()

    stats = {
        "kalshi": {"fetched": 0, "filtered": 0, "inserted": 0, "updated": 0, "errors": 0},
        "polymarket": {"fetched": 0, "filtered": 0, "inserted": 0, "updated": 0, "errors": 0}
    }

    # Step 1: Analyze theses to get filters
    logger.info("Analyzing theses to extract categories, keywords, and entities...")
    thesis_filters = await analyze_all_theses()

    if not thesis_filters["categories"] and not thesis_filters["keywords"] and not thesis_filters["entities"]:
        logger.warning("No theses found or theses have no content. Using fallback filters.")
        # Fallback to basic investment categories
        thesis_filters = {
            "categories": {"economics", "politics", "technology"},
            "keywords": {"market", "election", "economy"},
            "entities": set()
        }

    logger.info(f"Thesis filters - Categories: {thesis_filters['categories']}, "
                f"Keywords: {len(thesis_filters['keywords'])}, "
                f"Entities: {len(thesis_filters['entities'])}")

    # Step 2: Search for markets using thesis keywords directly
    # Much more efficient - only fetch what we need
    search_keywords = list(thesis_filters["keywords"]) + list(thesis_filters["entities"])

    logger.info(f"Searching with {len(search_keywords)} keywords/entities")

    # Use search API with keywords
    polymarket_markets = await polymarket_client.search_markets(
        keywords=search_keywords[:20],  # Top 20 most specific keywords
        active=True,
        limit_per_keyword=10
    )

    # Kalshi requires auth, skip for now
    kalshi_markets = []

    stats["kalshi"]["fetched"] = len(kalshi_markets)
    stats["polymarket"]["fetched"] = len(polymarket_markets)

    # Step 3: Light filtering (search already did heavy lifting)
    # Just verify quality - markets from search should mostly be relevant
    polymarket_markets = _filter_markets_by_thesis(polymarket_markets, thesis_filters)

    stats["kalshi"]["filtered"] = len(kalshi_markets)
    stats["polymarket"]["filtered"] = len(polymarket_markets)

    logger.info(f"After search + filter: Kalshi={len(kalshi_markets)}, Polymarket={len(polymarket_markets)}")

    # Normalize and upsert
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Process Kalshi markets
        for market in kalshi_markets:
            try:
                normalized = kalshi_client.normalize_market(market)
                upsert_result = _upsert_market(cur, normalized)
                stats["kalshi"][upsert_result] += 1
            except Exception as e:
                logger.error(f"Error processing Kalshi market {market.get('ticker')}: {e}")
                stats["kalshi"]["errors"] += 1

        # Process Polymarket markets
        for market in polymarket_markets:
            try:
                normalized = polymarket_client.normalize_market(market)
                upsert_result = _upsert_market(cur, normalized)
                stats["polymarket"][upsert_result] += 1
            except Exception as e:
                logger.error(f"Error processing Polymarket market {market.get('id')}: {e}")
                stats["polymarket"]["errors"] += 1

        conn.commit()
        logger.info(f"Market sync complete: {stats}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during market sync: {e}")
        raise
    finally:
        cur.close()
        conn.close()

    return stats


def _upsert_market(cur, market: dict) -> str:
    """
    Insert or update a market in the database.

    Args:
        cur: Database cursor
        market: Normalized market data

    Returns:
        'inserted' or 'updated'
    """
    # Check if market exists
    cur.execute(
        """
        SELECT id FROM markets
        WHERE platform = %s AND external_id = %s
        """,
        (market["platform"], market["external_id"])
    )
    existing = cur.fetchone()

    if existing:
        # Update existing market
        cur.execute(
            """
            UPDATE markets
            SET title = %s,
                description = %s,
                category = %s,
                end_date = %s,
                status = %s,
                market_url = %s,
                last_synced_at = NOW()
            WHERE platform = %s AND external_id = %s
            """,
            (
                market["title"],
                market["description"],
                market["category"],
                market["end_date"],
                market["status"],
                market["market_url"],
                market["platform"],
                market["external_id"]
            )
        )

        # Update current price
        if market.get("yes_price") is not None:
            cur.execute(
                """
                INSERT INTO market_current_prices (market_id, yes_price, no_price, volume_24h, open_interest, fetched_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (market_id) DO UPDATE
                SET yes_price = EXCLUDED.yes_price,
                    no_price = EXCLUDED.no_price,
                    volume_24h = EXCLUDED.volume_24h,
                    open_interest = EXCLUDED.open_interest,
                    fetched_at = NOW()
                """,
                (
                    existing[0],
                    market.get("yes_price"),
                    market.get("no_price"),
                    market.get("volume_24h"),
                    market.get("open_interest")
                )
            )

        return "updated"
    else:
        # Insert new market
        cur.execute(
            """
            INSERT INTO markets (platform, external_id, title, description, category, end_date, status, market_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                market["platform"],
                market["external_id"],
                market["title"],
                market["description"],
                market["category"],
                market["end_date"],
                market["status"],
                market["market_url"]
            )
        )
        market_id = cur.fetchone()[0]

        # Insert current price
        if market.get("yes_price") is not None:
            cur.execute(
                """
                INSERT INTO market_current_prices (market_id, yes_price, no_price, volume_24h, open_interest, fetched_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                (
                    market_id,
                    market.get("yes_price"),
                    market.get("no_price"),
                    market.get("volume_24h"),
                    market.get("open_interest")
                )
            )

        return "inserted"


async def sync_price_history(market_ids: Optional[List[str]] = None, days: int = 30) -> dict:
    """
    Sync historical price data for markets.

    Args:
        market_ids: Optional list of market IDs to sync. If None, syncs all active markets.
        days: Number of days of history to fetch

    Returns:
        Dictionary with sync statistics
    """
    logger.info(f"Starting price history sync for last {days} days...")

    conn = get_db_connection()
    cur = conn.cursor()

    stats = {"synced": 0, "errors": 0}

    try:
        # Get markets to sync
        if market_ids:
            placeholders = ",".join(["%s"] * len(market_ids))
            cur.execute(
                f"""
                SELECT id, platform, external_id
                FROM markets
                WHERE id IN ({placeholders})
                """,
                market_ids
            )
        else:
            cur.execute(
                """
                SELECT id, platform, external_id
                FROM markets
                WHERE status = 'active'
                LIMIT 50
                """
            )

        markets = cur.fetchall()

        kalshi_client = KalshiClient()
        polymarket_client = PolymarketClient()

        for market_id, platform, external_id in markets:
            try:
                if platform == "kalshi":
                    history = await kalshi_client.get_market_history(external_id, days)
                    _store_kalshi_history(cur, market_id, history)
                elif platform == "polymarket":
                    history = await polymarket_client.get_market_history(external_id, days)
                    _store_polymarket_history(cur, market_id, history)

                stats["synced"] += 1

            except Exception as e:
                logger.error(f"Error syncing history for {platform}:{external_id}: {e}")
                stats["errors"] += 1

        conn.commit()
        logger.info(f"Price history sync complete: {stats}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during price history sync: {e}")
        raise
    finally:
        cur.close()
        conn.close()

    return stats


def _store_kalshi_history(cur, market_id: str, candles: List[dict]):
    """Store Kalshi candlestick data as price history."""
    for candle in candles:
        cur.execute(
            """
            INSERT INTO market_price_history (market_id, timestamp, price, volume)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (market_id, timestamp) DO UPDATE
            SET price = EXCLUDED.price,
                volume = EXCLUDED.volume
            """,
            (
                market_id,
                datetime.fromtimestamp(candle["start_time"]),
                candle["close"] / 100,  # Convert cents to dollars
                candle["volume"]
            )
        )


def _store_polymarket_history(cur, market_id: str, history: List[dict]):
    """Store Polymarket price history."""
    for point in history:
        cur.execute(
            """
            INSERT INTO market_price_history (market_id, timestamp, price, volume)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (market_id, timestamp) DO UPDATE
            SET price = EXCLUDED.price,
                volume = EXCLUDED.volume
            """,
            (
                market_id,
                datetime.fromtimestamp(point["t"]),
                point["p"],
                point.get("v")
            )
        )


def _filter_markets_by_thesis(markets: List[dict], thesis_filters: dict) -> List[dict]:
    """
    Filter markets using thesis-derived categories, keywords, and entities.

    Stricter filtering: Requires either:
    - Entity match (high signal)
    - Category match + keyword match (medium signal)
    - Multiple keyword matches (medium signal)

    Args:
        markets: List of raw market dictionaries
        thesis_filters: Dict with 'categories', 'keywords', and 'entities' sets

    Returns:
        Filtered list of markets
    """
    categories = thesis_filters["categories"]
    keywords = thesis_filters["keywords"]
    entities = thesis_filters["entities"]

    filtered = []

    for market in markets:
        # Get market text to search
        title = (market.get("title") or market.get("question") or "").lower()
        description = (market.get("description") or market.get("subtitle") or "").lower()
        category = (market.get("category") or "").lower()
        text = f"{title} {description}"

        # Check matches
        category_match = any(cat in category for cat in categories)

        # Match keywords: full phrase OR most specific word from multi-word keywords
        # This matches the search logic in market_clients.py
        matched_keywords = []
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in text:
                # Exact phrase match
                matched_keywords.append(kw)
            else:
                # For multi-word keywords, try matching the most specific (longest) word
                kw_words = kw_lower.split()
                if len(kw_words) > 1:
                    specific_word = max(kw_words, key=len)
                    if len(specific_word) > 4 and specific_word in text:
                        matched_keywords.append(kw)

        keyword_match = len(matched_keywords) > 0
        entity_match = any(entity in text for entity in entities)

        # Quality signal logic
        keep = False
        match_reasons = []

        if entity_match:
            # Entity match is high signal - always keep
            keep = True
            match_reasons.append("entity")
        elif len(matched_keywords) >= 2:
            # Multiple keyword matches - strong signal
            keep = True
            match_reasons.append(f"keywords={','.join(matched_keywords[:3])}")
        elif category_match and keyword_match:
            # Category + keyword - medium signal
            keep = True
            match_reasons.append(f"category={category}")
            match_reasons.append(f"keywords={','.join(matched_keywords[:2])}")
        elif keyword_match:
            # Single keyword - accept if it's specific enough (2+ words or appears in title)
            for kw in matched_keywords:
                if len(kw.split()) >= 2 or kw in title:  # Multi-word keyword or in title
                    keep = True
                    match_reasons.append(f"keyword={kw}")
                    break

        if keep:
            filtered.append(market)
            logger.info(f"✓ Kept: {title[:60]}... ({'; '.join(match_reasons)})")

    logger.info(f"Thesis-driven filter: {len(markets)} → {len(filtered)} markets")
    return filtered


async def refresh_current_prices(market_ids: Optional[List[str]] = None) -> dict:
    """
    Refresh current prices for markets.

    This is a lightweight operation that only updates the current_prices table
    without fetching full market metadata.

    Args:
        market_ids: Optional list of market IDs. If None, refreshes all active markets.

    Returns:
        Dictionary with refresh statistics
    """
    logger.info("Refreshing current prices...")

    # For now, we'll just call sync_markets which updates prices
    # In a production system, you'd have a more efficient endpoint
    # that only fetches current prices without full market metadata
    return await sync_markets()


if __name__ == "__main__":
    # For manual testing
    import asyncio

    async def test_sync():
        stats = await sync_markets()
        print(f"Sync stats: {stats}")

    asyncio.run(test_sync())
