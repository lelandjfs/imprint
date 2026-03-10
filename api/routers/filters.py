"""Filters endpoint to get available filter values."""

from fastapi import APIRouter
from supabase import create_client
from config import get_settings


router = APIRouter(prefix="/api", tags=["filters"])


@router.get("/filters")
async def get_filters():
    """
    Get distinct values for all filterable fields.

    Returns available values for:
    - sector
    - entities (top 50 most frequent)
    - sentiment
    - document_type
    - catalyst_window
    """
    settings = get_settings()
    supabase = create_client(settings.supabase_url, settings.supabase_anon_key)

    # Get distinct values for each field
    sector_response = supabase.table("imprint_documents").select("sector").execute()
    sentiment_response = supabase.table("imprint_documents").select("sentiment").execute()
    document_type_response = supabase.table("imprint_documents").select("document_type").execute()
    catalyst_window_response = supabase.table("imprint_documents").select("catalyst_window").execute()

    # Get unique values
    sector_values = list(
        {row["sector"] for row in sector_response.data if row.get("sector")}
    )
    sentiment_values = list(
        {row["sentiment"] for row in sentiment_response.data if row.get("sentiment")}
    )
    document_type_values = list(
        {row["document_type"] for row in document_type_response.data if row.get("document_type")}
    )
    catalyst_window_values = list(
        {row["catalyst_window"] for row in catalyst_window_response.data if row.get("catalyst_window")}
    )

    # Get top entities (flatten arrays and count frequency)
    entities_response = (
        supabase.table("imprint_documents").select("entities").execute()
    )
    entity_counts = {}
    for row in entities_response.data:
        if row.get("entities"):
            for entity in row["entities"]:
                entity_counts[entity] = entity_counts.get(entity, 0) + 1

    # Get top 50 entities
    top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:50]
    entity_values = [entity for entity, count in top_entities]

    return {
        "sector": sorted(sector_values),
        "entities": entity_values,
        "sentiment": sorted(sentiment_values),
        "document_type": sorted(document_type_values),
        "catalyst_window": sorted(catalyst_window_values),
    }
