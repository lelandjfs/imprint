"""
Thesis analysis service for extracting categories, keywords, and entities.

Uses Claude to analyze investment theses and extract relevant filters
for market discovery.
"""

import logging
import json
from typing import Dict, List, Set
from langchain_anthropic import ChatAnthropic
from utils import get_db_connection
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

THESIS_ANALYSIS_PROMPT = """You are analyzing an investment thesis to extract relevant categories, keywords, and topics for finding related prediction markets.

THESIS:
Title: {thesis_title}
Content:
{thesis_content}

Extract the following:

1. **Categories**: Which prediction market categories are relevant? Choose from:
   - Economics (Fed policy, GDP, inflation, employment, macro)
   - Politics (elections, policy, government, regulation)
   - Technology (AI, chips, semiconductors, software)
   - Crypto (Bitcoin, Ethereum, DeFi, crypto markets)
   - Science (research, climate, energy)
   - Business (earnings, IPOs, M&A, corporate)

2. **Keywords**: 10-20 keywords that should appear in relevant market titles/descriptions.
   Include:
   - Specific topics (e.g., "interest rates", "AI inference", "semiconductor")
   - Technical terms (e.g., "capex", "margin", "supply chain")
   - Avoid generic words (e.g., "important", "increase")

Respond ONLY with valid JSON:
{{
  "categories": ["Economics", "Technology"],
  "keywords": ["interest rates", "inflation", "AI", "NVDA", "data centers"]
}}"""


async def analyze_all_theses() -> Dict[str, any]:
    """
    Analyze all theses to extract categories and keywords for market discovery.

    Returns:
        Dictionary with:
        - categories: Set of all relevant categories across theses
        - keywords: Set of all keywords across theses
        - entities: Set of entities from cited documents
    """
    logger.info("Analyzing theses for market discovery...")

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get all theses with content
        cur.execute("""
            SELECT t.id, t.title,
                   STRING_AGG(s.title || ': ' || s.content, '\n\n' ORDER BY s.position) as content
            FROM theses t
            LEFT JOIN thesis_sections s ON t.id = s.thesis_id
            GROUP BY t.id, t.title
        """)
        theses = cur.fetchall()

        if not theses:
            logger.warning("No theses found")
            return {"categories": set(), "keywords": set(), "entities": set()}

        # Initialize Claude
        llm = ChatAnthropic(
            model="claude-sonnet-4-5-20250929",
            temperature=0,
            api_key=settings.anthropic_api_key
        )

        all_categories = set()
        all_keywords = set()

        # Analyze each thesis
        for thesis_id, thesis_title, thesis_content in theses:
            try:
                result = await _analyze_single_thesis(
                    llm,
                    thesis_title,
                    thesis_content or ""
                )

                all_categories.update(result["categories"])
                all_keywords.update(result["keywords"])

            except Exception as e:
                logger.error(f"Error analyzing thesis {thesis_id}: {e}")

        # Get entities from cited documents in theses
        entities = _get_thesis_entities(cur)

        logger.info(f"Extracted {len(all_categories)} categories, {len(all_keywords)} keywords, {len(entities)} entities")

        return {
            "categories": all_categories,
            "keywords": all_keywords,
            "entities": entities
        }

    finally:
        cur.close()
        conn.close()


async def _analyze_single_thesis(
    llm: ChatAnthropic,
    thesis_title: str,
    thesis_content: str
) -> Dict[str, List[str]]:
    """
    Use Claude to analyze a single thesis.

    Returns:
        Dictionary with categories and keywords
    """
    prompt = THESIS_ANALYSIS_PROMPT.format(
        thesis_title=thesis_title,
        thesis_content=thesis_content[:3000]  # Limit to avoid token limits
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
            "categories": [c.lower() for c in result.get("categories", [])],
            "keywords": [k.lower() for k in result.get("keywords", [])]
        }
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse thesis analysis: {content}")
        return {"categories": [], "keywords": []}


def _get_thesis_entities(cur) -> Set[str]:
    """
    Get all entities from documents cited in theses.

    This gives us a curated list of entities that matter to the user's research.
    """
    cur.execute("""
        SELECT DISTINCT UNNEST(d.entities) as entity
        FROM imprint_documents d
        JOIN thesis_citations tc ON d.id = tc.document_id
        WHERE d.entities IS NOT NULL
        AND d.status = 'active'
    """)

    entities = {row[0].lower() for row in cur.fetchall()}

    # If no citations yet, fall back to top entities from all active documents
    if not entities:
        logger.info("No thesis citations found, using top entities from all documents")
        cur.execute("""
            SELECT entity, COUNT(*) as cnt
            FROM (
                SELECT UNNEST(entities) as entity
                FROM imprint_documents
                WHERE status = 'active'
                AND entities IS NOT NULL
            ) e
            GROUP BY entity
            ORDER BY cnt DESC
            LIMIT 50
        """)
        entities = {row[0].lower() for row in cur.fetchall()}

    logger.info(f"Found {len(entities)} entities from research: {list(entities)[:10]}...")
    return entities


if __name__ == "__main__":
    import asyncio

    async def test():
        result = await analyze_all_theses()
        print(f"Categories: {result['categories']}")
        print(f"Keywords: {result['keywords']}")
        print(f"Entities: {list(result['entities'])[:20]}")

    asyncio.run(test())
