"""
Thesis-market alignment computation using Claude.

Analyzes how prediction markets relate to investment theses.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from langchain_anthropic import ChatAnthropic
from utils import get_db_connection
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Alignment prompt template
ALIGNMENT_PROMPT = """You are an investment analyst evaluating how a prediction market relates to an investment thesis.

THESIS:
Title: {thesis_title}
Content:
{thesis_content}

MARKET:
Question: {market_title}
Description: {market_description}
Current probability: {current_price}%

Analyze the connection between this market outcome and the thesis:

1. **Alignment Score** (0.0-1.0): How relevant is this market to the thesis?
   - 0.0 = Completely unrelated
   - 0.3-0.5 = Tangentially related
   - 0.6-0.8 = Directly relevant
   - 0.9-1.0 = Core thesis indicator

2. **Direction**: If the market resolves YES, does it:
   - "supports" - Support/confirm the thesis
   - "contradicts" - Contradict/challenge the thesis
   - "neutral" - Neither support nor contradict

3. **Reasoning**: 2-3 sentences explaining the connection

Respond ONLY with valid JSON:
{{
  "alignment_score": 0.0-1.0,
  "alignment_direction": "supports" | "contradicts" | "neutral",
  "reasoning": "2-3 sentence explanation"
}}"""


async def compute_all_alignments(min_score: float = 0.3) -> dict:
    """
    Compute alignment scores between all theses and all active markets.

    Only stores alignments with score >= min_score to keep the database lean.

    Args:
        min_score: Minimum alignment score to store (default: 0.3)

    Returns:
        Dictionary with computation statistics
    """
    logger.info(f"Computing thesis-market alignments (min_score={min_score})...")

    conn = get_db_connection()
    cur = conn.cursor()

    stats = {
        "theses": 0,
        "markets": 0,
        "alignments_computed": 0,
        "alignments_stored": 0,
        "errors": 0
    }

    try:
        # Get all theses
        cur.execute("""
            SELECT t.id, t.title,
                   STRING_AGG(s.title || ': ' || s.content, '\n\n' ORDER BY s.position) as content
            FROM theses t
            LEFT JOIN thesis_sections s ON t.id = s.thesis_id
            GROUP BY t.id, t.title
        """)
        theses = cur.fetchall()
        stats["theses"] = len(theses)

        if not theses:
            logger.warning("No theses found. Create some theses first!")
            return stats

        # Get all active markets
        cur.execute("""
            SELECT m.id, m.title, m.description,
                   mcp.yes_price
            FROM markets m
            LEFT JOIN market_current_prices mcp ON m.id = mcp.market_id
            WHERE m.status = 'active'
        """)
        markets = cur.fetchall()
        stats["markets"] = len(markets)

        if not markets:
            logger.warning("No active markets found. Run market sync first!")
            return stats

        # Initialize Claude
        llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0,
            api_key=settings.anthropic_api_key
        )

        # Compute alignments
        for thesis_id, thesis_title, thesis_content in theses:
            logger.info(f"Processing thesis: {thesis_title}")

            for market_id, market_title, market_description, current_price in markets:
                try:
                    alignment = await _compute_single_alignment(
                        llm,
                        thesis_id=thesis_id,
                        thesis_title=thesis_title,
                        thesis_content=thesis_content or "",
                        market_id=market_id,
                        market_title=market_title,
                        market_description=market_description,
                        current_price=current_price
                    )

                    stats["alignments_computed"] += 1

                    # Only store if score meets threshold
                    if alignment["score"] >= min_score:
                        _store_alignment(cur, thesis_id, market_id, alignment)
                        stats["alignments_stored"] += 1

                except Exception as e:
                    logger.error(f"Error computing alignment for thesis={thesis_id}, market={market_id}: {e}")
                    stats["errors"] += 1

            # Commit after each thesis
            conn.commit()

        # Compute global relevance scores
        logger.info("Computing global relevance scores...")
        _compute_global_relevance(cur)
        conn.commit()

        logger.info(f"Alignment computation complete: {stats}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Error during alignment computation: {e}")
        raise
    finally:
        cur.close()
        conn.close()

    return stats


async def _compute_single_alignment(
    llm: ChatAnthropic,
    thesis_id: str,
    thesis_title: str,
    thesis_content: str,
    market_id: str,
    market_title: str,
    market_description: Optional[str],
    current_price: Optional[float]
) -> Dict[str, Any]:
    """
    Use Claude to compute alignment between one thesis and one market.

    Returns:
        Dictionary with score, direction, and reasoning
    """
    prompt = ALIGNMENT_PROMPT.format(
        thesis_title=thesis_title,
        thesis_content=thesis_content[:2000],  # Limit to avoid token limits
        market_title=market_title,
        market_description=market_description or "No description provided",
        current_price=int(current_price * 100) if current_price else "Unknown"
    )

    response = await llm.ainvoke(prompt)
    content = response.content

    # Strip markdown code blocks if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    # Parse JSON response
    try:
        result = json.loads(content)
        return {
            "score": float(result["alignment_score"]),
            "direction": result["alignment_direction"],
            "reasoning": result["reasoning"]
        }
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse LLM response: {content}")
        # Return neutral alignment if parsing fails
        return {
            "score": 0.0,
            "direction": "neutral",
            "reasoning": "Failed to analyze alignment"
        }


def _store_alignment(cur, thesis_id: str, market_id: str, alignment: Dict[str, Any]):
    """Store alignment in database."""
    cur.execute("""
        INSERT INTO thesis_market_alignments
        (thesis_id, market_id, alignment_score, alignment_direction, reasoning)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (thesis_id, market_id) DO UPDATE
        SET alignment_score = EXCLUDED.alignment_score,
            alignment_direction = EXCLUDED.alignment_direction,
            reasoning = EXCLUDED.reasoning,
            computed_at = NOW()
    """, (
        thesis_id,
        market_id,
        alignment["score"],
        alignment["direction"],
        alignment["reasoning"]
    ))


def _compute_global_relevance(cur):
    """
    Compute global relevance scores for Explore tab.

    Aggregates alignment scores across all theses for each market.
    """
    cur.execute("""
        INSERT INTO market_global_relevance (market_id, relevance_score, top_thesis_ids, summary)
        SELECT
            tma.market_id,
            AVG(tma.alignment_score) as relevance_score,
            (ARRAY_AGG(tma.thesis_id ORDER BY tma.alignment_score DESC))[1:3] as top_thesis_ids,
            'Relevant to ' || COUNT(DISTINCT tma.thesis_id) || ' theses' as summary
        FROM thesis_market_alignments tma
        WHERE tma.alignment_score >= 0.3
        GROUP BY tma.market_id
        ON CONFLICT (market_id) DO UPDATE
        SET relevance_score = EXCLUDED.relevance_score,
            top_thesis_ids = EXCLUDED.top_thesis_ids,
            summary = EXCLUDED.summary,
            computed_at = NOW()
    """)

    logger.info("Global relevance scores computed")


if __name__ == "__main__":
    import asyncio

    async def test():
        stats = await compute_all_alignments(min_score=0.3)
        print(f"Alignment stats: {stats}")

    asyncio.run(test())
