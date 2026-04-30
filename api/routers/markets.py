"""Markets endpoint for prediction markets from Kalshi and Polymarket."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from utils import get_db_connection

router = APIRouter(prefix="/api/markets", tags=["markets"])


# ========== Pydantic Models ==========

class MarketBase(BaseModel):
    """Base market model."""
    id: str
    platform: str
    external_id: str
    title: str
    description: str | None
    category: str | None
    end_date: str | None
    status: str
    market_url: str


class MarketPrice(BaseModel):
    """Current market price model."""
    yes_price: float
    no_price: float | None
    volume_24h: float | None
    open_interest: float | None
    fetched_at: str


class MarketPricePoint(BaseModel):
    """Price history point."""
    timestamp: str
    price: float
    volume: float | None


class MarketDetail(MarketBase):
    """Market with price history."""
    current_price: MarketPrice | None
    price_history: List[MarketPricePoint] | None


class ThesisInfo(BaseModel):
    """Thesis information for alignment."""
    id: str
    title: str


class MarketAlignment(BaseModel):
    """Thesis-market alignment."""
    thesis: ThesisInfo
    alignment_score: float
    alignment_direction: str
    reasoning: str


class MarketExploreItem(MarketBase):
    """Market item for Explore view."""
    current_price: MarketPrice | None
    relevance_score: float
    top_alignments: List[MarketAlignment]


class MarketThesisItem(MarketBase):
    """Market item for Thesis Alignment view."""
    current_price: MarketPrice | None
    alignment_score: float
    alignment_direction: str
    reasoning: str


# ========== Endpoints ==========

@router.get("")
async def list_markets(
    platform: Optional[str] = None,
    category: Optional[str] = None,
    status: str = "active",
    limit: int = Query(50, le=100),
    offset: int = 0
):
    """
    List markets with optional filters.

    Args:
        platform: Filter by platform ('kalshi' or 'polymarket')
        category: Filter by category
        status: Filter by status (default: 'active')
        limit: Maximum number of results (default: 50, max: 100)
        offset: Pagination offset

    Returns:
        Dictionary with 'markets' list and 'total' count
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Build WHERE clause
        where_conditions = ["m.status = %s"]
        params = [status]

        if platform:
            where_conditions.append("m.platform = %s")
            params.append(platform)

        if category:
            where_conditions.append("m.category = %s")
            params.append(category)

        where_clause = " AND ".join(where_conditions)

        # Get total count
        cur.execute(f"""
            SELECT COUNT(*)
            FROM markets m
            WHERE {where_clause}
        """, params)
        total = cur.fetchone()[0]

        # Get markets with current prices
        params.extend([limit, offset])
        cur.execute(f"""
            SELECT
                m.id, m.platform, m.external_id, m.title, m.description,
                m.category, m.end_date, m.status, m.market_url,
                mcp.yes_price, mcp.no_price, mcp.volume_24h,
                mcp.open_interest, mcp.fetched_at
            FROM markets m
            LEFT JOIN market_current_prices mcp ON m.id = mcp.market_id
            WHERE {where_clause}
            ORDER BY m.created_at DESC
            LIMIT %s OFFSET %s
        """, params)

        markets = []
        for row in cur.fetchall():
            market = {
                "id": str(row[0]),
                "platform": row[1],
                "external_id": row[2],
                "title": row[3],
                "description": row[4],
                "category": row[5],
                "end_date": row[6].isoformat() if row[6] else None,
                "status": row[7],
                "market_url": row[8],
                "current_price": {
                    "yes_price": float(row[9]) if row[9] is not None else None,
                    "no_price": float(row[10]) if row[10] is not None else None,
                    "volume_24h": float(row[11]) if row[11] is not None else None,
                    "open_interest": float(row[12]) if row[12] is not None else None,
                    "fetched_at": row[13].isoformat() if row[13] else None,
                } if row[9] is not None else None
            }
            markets.append(market)

        cur.close()
        conn.close()

        return {
            "markets": markets,
            "total": total
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explore")
async def explore_markets(limit: int = Query(20, le=50)):
    """
    Get markets for "Explore" view - ranked by global relevance across all theses.

    Returns markets with pre-computed relevance scores and top aligned theses.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get markets with global relevance scores
        cur.execute("""
            SELECT
                m.id, m.platform, m.external_id, m.title, m.description,
                m.category, m.end_date, m.status, m.market_url,
                mcp.yes_price, mcp.no_price, mcp.volume_24h,
                mcp.open_interest, mcp.fetched_at,
                mgr.relevance_score, mgr.top_thesis_ids
            FROM markets m
            LEFT JOIN market_current_prices mcp ON m.id = mcp.market_id
            LEFT JOIN market_global_relevance mgr ON m.id = mgr.market_id
            WHERE m.status = 'active' AND mgr.relevance_score IS NOT NULL
            ORDER BY mgr.relevance_score DESC
            LIMIT %s
        """, (limit,))

        markets = []
        for row in cur.fetchall():
            market_id = str(row[0])
            top_thesis_ids = row[15] if row[15] else []

            # Get top alignments
            alignments = []
            if top_thesis_ids:
                placeholders = ",".join(["%s"] * len(top_thesis_ids))
                cur.execute(f"""
                    SELECT
                        t.id, t.title,
                        tma.alignment_score, tma.alignment_direction, tma.reasoning
                    FROM thesis_market_alignments tma
                    JOIN theses t ON tma.thesis_id = t.id
                    WHERE tma.market_id = %s AND tma.thesis_id IN ({placeholders})
                    ORDER BY tma.alignment_score DESC
                    LIMIT 3
                """, [market_id] + top_thesis_ids)

                for arow in cur.fetchall():
                    alignments.append({
                        "thesis": {
                            "id": str(arow[0]),
                            "title": arow[1]
                        },
                        "alignment_score": float(arow[2]),
                        "alignment_direction": arow[3],
                        "reasoning": arow[4]
                    })

            market = {
                "id": market_id,
                "platform": row[1],
                "external_id": row[2],
                "title": row[3],
                "description": row[4],
                "category": row[5],
                "end_date": row[6].isoformat() if row[6] else None,
                "status": row[7],
                "market_url": row[8],
                "current_price": {
                    "yes_price": float(row[9]) if row[9] is not None else None,
                    "no_price": float(row[10]) if row[10] is not None else None,
                    "volume_24h": float(row[11]) if row[11] is not None else None,
                    "open_interest": float(row[12]) if row[12] is not None else None,
                    "fetched_at": row[13].isoformat() if row[13] else None,
                } if row[9] is not None else None,
                "relevance_score": float(row[14]) if row[14] else 0.0,
                "top_alignments": alignments
            }
            markets.append(market)

        cur.close()
        conn.close()

        return {"markets": markets}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thesis/{thesis_id}")
async def markets_for_thesis(
    thesis_id: str,
    limit: int = Query(20, le=50)
):
    """
    Get markets aligned to a specific thesis.

    Returns markets with pre-computed alignment scores and reasoning.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Verify thesis exists
        cur.execute("SELECT id FROM theses WHERE id = %s", (thesis_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Thesis not found")

        # Get aligned markets
        cur.execute("""
            SELECT
                m.id, m.platform, m.external_id, m.title, m.description,
                m.category, m.end_date, m.status, m.market_url,
                mcp.yes_price, mcp.no_price, mcp.volume_24h,
                mcp.open_interest, mcp.fetched_at,
                tma.alignment_score, tma.alignment_direction, tma.reasoning
            FROM markets m
            JOIN thesis_market_alignments tma ON m.id = tma.market_id
            LEFT JOIN market_current_prices mcp ON m.id = mcp.market_id
            WHERE tma.thesis_id = %s AND m.status = 'active'
            ORDER BY tma.alignment_score DESC
            LIMIT %s
        """, (thesis_id, limit))

        markets = []
        for row in cur.fetchall():
            market = {
                "id": str(row[0]),
                "platform": row[1],
                "external_id": row[2],
                "title": row[3],
                "description": row[4],
                "category": row[5],
                "end_date": row[6].isoformat() if row[6] else None,
                "status": row[7],
                "market_url": row[8],
                "current_price": {
                    "yes_price": float(row[9]) if row[9] is not None else None,
                    "no_price": float(row[10]) if row[10] is not None else None,
                    "volume_24h": float(row[11]) if row[11] is not None else None,
                    "open_interest": float(row[12]) if row[12] is not None else None,
                    "fetched_at": row[13].isoformat() if row[13] else None,
                } if row[9] is not None else None,
                "alignment_score": float(row[14]),
                "alignment_direction": row[15],
                "reasoning": row[16]
            }
            markets.append(market)

        cur.close()
        conn.close()

        return {"markets": markets}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{market_id}")
async def get_market(
    market_id: str,
    include_history: bool = True,
    history_days: int = Query(30, le=90)
):
    """
    Get single market with current price and optional price history.

    Args:
        market_id: Market UUID
        include_history: Whether to include price history (default: True)
        history_days: Number of days of history to return (default: 30, max: 90)
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get market with current price
        cur.execute("""
            SELECT
                m.id, m.platform, m.external_id, m.title, m.description,
                m.category, m.end_date, m.status, m.market_url,
                mcp.yes_price, mcp.no_price, mcp.volume_24h,
                mcp.open_interest, mcp.fetched_at
            FROM markets m
            LEFT JOIN market_current_prices mcp ON m.id = mcp.market_id
            WHERE m.id = %s
        """, (market_id,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Market not found")

        market = {
            "id": str(row[0]),
            "platform": row[1],
            "external_id": row[2],
            "title": row[3],
            "description": row[4],
            "category": row[5],
            "end_date": row[6].isoformat() if row[6] else None,
            "status": row[7],
            "market_url": row[8],
            "current_price": {
                "yes_price": float(row[9]) if row[9] is not None else None,
                "no_price": float(row[10]) if row[10] is not None else None,
                "volume_24h": float(row[11]) if row[11] is not None else None,
                "open_interest": float(row[12]) if row[12] is not None else None,
                "fetched_at": row[13].isoformat() if row[13] else None,
            } if row[9] is not None else None,
            "price_history": None
        }

        # Get price history if requested
        if include_history:
            cur.execute("""
                SELECT timestamp, price, volume
                FROM market_price_history
                WHERE market_id = %s
                    AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """, (market_id, history_days))

            history = []
            for hrow in cur.fetchall():
                history.append({
                    "timestamp": hrow[0].isoformat(),
                    "price": float(hrow[1]),
                    "volume": float(hrow[2]) if hrow[2] is not None else None
                })

            market["price_history"] = history

        cur.close()
        conn.close()

        return market

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
