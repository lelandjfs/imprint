"""
API clients for Kalshi and Polymarket prediction markets.
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class KalshiClient:
    """
    Kalshi API client for fetching prediction market data.

    Public API documentation: https://trading-api.kalshi.com/docs
    No authentication required for public market data.
    """

    BASE_URL = "https://trading-api.kalshi.com/trade-api/v2"

    async def get_markets(
        self,
        status: str = "open",
        limit: int = 200,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch markets from Kalshi.

        Args:
            status: Market status ('open', 'closed', 'settled')
            limit: Maximum number of markets to return
            category: Optional category filter

        Returns:
            List of market dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "status": status,
                    "limit": limit
                }

                if category:
                    params["series_ticker"] = category

                response = await client.get(
                    f"{self.BASE_URL}/markets",
                    params=params
                )
                response.raise_for_status()

                data = response.json()
                markets = data.get("markets", [])

                logger.info(f"Fetched {len(markets)} markets from Kalshi")
                return markets

        except Exception as e:
            logger.error(f"Error fetching Kalshi markets: {e}")
            return []

    async def get_market_history(
        self,
        ticker: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch price history for a specific market.

        Args:
            ticker: Market ticker (e.g., "NASDAQ100-23DEC31")
            days: Number of days of history

        Returns:
            List of price history points
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Kalshi uses candlestick data
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=days)

                response = await client.get(
                    f"{self.BASE_URL}/markets/{ticker}/candlesticks",
                    params={
                        "start_time": int(start_time.timestamp()),
                        "end_time": int(end_time.timestamp()),
                        "period": "1d"  # Daily candles
                    }
                )
                response.raise_for_status()

                data = response.json()
                candles = data.get("candlesticks", [])

                logger.info(f"Fetched {len(candles)} candles for {ticker}")
                return candles

        except Exception as e:
            logger.error(f"Error fetching Kalshi history for {ticker}: {e}")
            return []

    def normalize_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Kalshi market data to our schema.

        Args:
            market: Raw market data from Kalshi API

        Returns:
            Normalized market dictionary
        """
        return {
            "platform": "kalshi",
            "external_id": market.get("ticker"),
            "title": market.get("title"),
            "description": market.get("subtitle") or market.get("title"),
            "category": market.get("category"),
            "end_date": market.get("close_time"),
            "status": self._map_status(market.get("status")),
            "market_url": f"https://kalshi.com/markets/{market.get('ticker')}",
            "yes_price": market.get("yes_bid", 0) / 100 if market.get("yes_bid") else None,  # Convert cents to dollars
            "no_price": market.get("no_bid", 0) / 100 if market.get("no_bid") else None,
            "volume_24h": market.get("volume_24h"),
            "open_interest": market.get("open_interest")
        }

    def _map_status(self, kalshi_status: str) -> str:
        """Map Kalshi status to our status enum."""
        status_map = {
            "open": "active",
            "closed": "closed",
            "settled": "resolved"
        }
        return status_map.get(kalshi_status, "active")


class PolymarketClient:
    """
    Polymarket API client for fetching prediction market data.

    Public API documentation: https://docs.polymarket.com
    Uses the CLOB (Central Limit Order Book) API.
    """

    BASE_URL = "https://clob.polymarket.com"
    GAMMA_URL = "https://gamma-api.polymarket.com"

    async def search_markets(
        self,
        keywords: List[str],
        active: bool = True,
        limit_per_keyword: int = 50,
        max_fetch: int = 3000
    ) -> List[Dict[str, Any]]:
        """
        Search for markets matching specific keywords using pagination.

        Args:
            keywords: List of search terms
            active: Only fetch active markets
            limit_per_keyword: Max markets per keyword search
            max_fetch: Max total markets to fetch across all batches

        Returns:
            Deduplicated list of matching markets
        """
        all_markets = {}  # Use dict to deduplicate by market ID

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                for keyword in keywords:
                    try:
                        keyword_lower = keyword.lower()
                        keyword_words = keyword_lower.split()
                        matches = []

                        # Paginate through markets until we have enough matches
                        offset = 0
                        batch_size = 1000

                        while offset < max_fetch and len(matches) < limit_per_keyword:
                            params = {
                                "closed": "false" if active else "true",
                                "limit": batch_size,
                                "offset": offset
                            }

                            response = await client.get(
                                f"{self.GAMMA_URL}/markets",
                                params=params
                            )
                            response.raise_for_status()
                            batch = response.json()

                            if not batch:
                                break  # No more markets

                            # Filter batch by keyword
                            for m in batch:
                                text = (m.get('question', '') + ' ' + m.get('description', '')).lower()

                                # Match if full keyword appears (stricter matching)
                                if keyword_lower in text:
                                    matches.append(m)
                                elif len(keyword_words) > 1:
                                    # For multi-word keywords, require the most specific word (longest word)
                                    # e.g., "nuclear power" → only match if "nuclear" appears (not just "power")
                                    specific_word = max(keyword_words, key=len)
                                    if len(specific_word) > 4 and specific_word in text:
                                        matches.append(m)

                                if len(matches) >= limit_per_keyword:
                                    break

                            offset += batch_size

                        # Add to deduplicated dict
                        for m in matches[:limit_per_keyword]:
                            market_id = m.get('id') or m.get('condition_id')
                            if market_id:
                                all_markets[market_id] = m

                        logger.info(f"Keyword '{keyword}': found {len(matches)} matches")

                    except Exception as e:
                        logger.error(f"Error searching for '{keyword}': {e}")
                        continue

                result = list(all_markets.values())
                logger.info(f"Total unique markets from search: {len(result)}")
                return result

        except Exception as e:
            logger.error(f"Error in market search: {e}")
            return []

    async def get_markets(
        self,
        active: bool = True,
        limit: int = 200,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetch markets from Polymarket.

        Args:
            active: Only fetch active markets
            limit: Maximum number of markets to return
            offset: Pagination offset

        Returns:
            List of market dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Use Gamma API for market list
                params = {
                    "closed": "false" if active else "true",
                    "limit": limit,
                    "offset": offset
                }

                response = await client.get(
                    f"{self.GAMMA_URL}/markets",
                    params=params
                )
                response.raise_for_status()

                markets = response.json()

                logger.info(f"Fetched {len(markets)} markets from Polymarket")
                return markets

        except Exception as e:
            logger.error(f"Error fetching Polymarket markets: {e}")
            return []

    async def get_market_history(
        self,
        condition_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch price history for a specific market.

        Args:
            condition_id: Market condition ID
            days: Number of days of history

        Returns:
            List of price history points
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=days)

                response = await client.get(
                    f"{self.GAMMA_URL}/prices-history",
                    params={
                        "market": condition_id,
                        "startTs": int(start_time.timestamp()),
                        "endTs": int(end_time.timestamp()),
                        "interval": "1d"
                    }
                )
                response.raise_for_status()

                data = response.json()
                history = data.get("history", [])

                logger.info(f"Fetched {len(history)} price points for {condition_id}")
                return history

        except Exception as e:
            logger.error(f"Error fetching Polymarket history for {condition_id}: {e}")
            return []

    def normalize_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Polymarket market data to our schema.

        Args:
            market: Raw market data from Polymarket API

        Returns:
            Normalized market dictionary
        """
        # Polymarket markets can be binary or multi-outcome
        # We'll focus on binary markets for now
        tokens = market.get("tokens", [])
        yes_token = next((t for t in tokens if t.get("outcome") == "Yes"), None)
        no_token = next((t for t in tokens if t.get("outcome") == "No"), None)

        return {
            "platform": "polymarket",
            "external_id": market.get("condition_id") or market.get("id"),
            "title": market.get("question"),
            "description": market.get("description"),
            "category": market.get("category"),
            "end_date": market.get("end_date_iso"),
            "status": "active" if market.get("active") else "closed",
            "market_url": f"https://polymarket.com/event/{market.get('slug', market.get('id'))}",
            "yes_price": float(yes_token.get("price", 0)) if yes_token else None,
            "no_price": float(no_token.get("price", 0)) if no_token else None,
            "volume_24h": market.get("volume_24hr"),
            "open_interest": market.get("liquidity")
        }
