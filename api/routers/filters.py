"""Filters endpoint to get available filter values."""

from fastapi import APIRouter
from supabase import create_client
from api.config import get_settings


router = APIRouter(prefix="/api", tags=["filters"])


@router.get("/filters")
async def get_filters():
    """
    Get distinct values for all filterable fields.

    Returns available values for:
    - thesis
    - sector
    - entities (top 50 most frequent)
    - document_type
    - angle
    - catalyst_window
    """
    settings = get_settings()
    supabase = create_client(settings.supabase_url, settings.supabase_anon_key)

    # Get distinct values for each field
    thesis_response = supabase.table("imprint_documents").select("thesis").execute()
    sector_response = supabase.table("imprint_documents").select("sector").execute()
    doc_type_response = (
        supabase.table("imprint_documents").select("document_type").execute()
    )
    angle_response = supabase.table("imprint_documents").select("angle").execute()
    catalyst_response = (
        supabase.table("imprint_documents").select("catalyst_window").execute()
    )

    # Get unique values
    thesis_values = list(
        {row["thesis"] for row in thesis_response.data if row.get("thesis")}
    )
    sector_values = list(
        {row["sector"] for row in sector_response.data if row.get("sector")}
    )
    doc_type_values = list(
        {
            row["document_type"]
            for row in doc_type_response.data
            if row.get("document_type")
        }
    )
    angle_values = list(
        {row["angle"] for row in angle_response.data if row.get("angle")}
    )
    catalyst_values = list(
        {
            row["catalyst_window"]
            for row in catalyst_response.data
            if row.get("catalyst_window")
        }
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
        "thesis": sorted(thesis_values),
        "sector": sorted(sector_values),
        "entities": entity_values,
        "document_type": sorted(doc_type_values),
        "angle": sorted(angle_values),
        "catalyst_window": sorted(catalyst_values),
    }
