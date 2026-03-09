"""Documents endpoint for tag approval workflow."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils import get_db_connection, mark_document_reviewed

router = APIRouter(prefix="/api/documents", tags=["documents"])


class PendingDocument(BaseModel):
    """Pending document model."""

    id: str
    title: str
    source_type: str
    thesis: str
    topic: str
    sector: str
    entities: list[str]
    summary: str
    content: str
    ingested_date: str


@router.get("/pending")
async def get_pending_documents():
    """
    Get all documents pending review.

    Returns documents with status='pending_review' for tag approval workflow.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, source_type, thesis, topic, sector, entities, summary, content, ingested_date
        FROM imprint_documents
        WHERE status = 'pending_review'
        ORDER BY ingested_date DESC
    """)

    columns = ['id', 'title', 'source_type', 'thesis', 'topic', 'sector', 'entities', 'summary', 'content', 'ingested_date']
    rows = cur.fetchall()

    documents = []
    for row in rows:
        doc = dict(zip(columns, row))
        # Convert UUID to string
        doc['id'] = str(doc['id'])
        # Convert datetime to ISO string
        doc['ingested_date'] = doc['ingested_date'].isoformat() if doc['ingested_date'] else None
        # Ensure entities is a list
        doc['entities'] = doc['entities'] or []
        documents.append(doc)

    cur.close()
    conn.close()

    return {"documents": documents}


@router.post("/{document_id}/approve")
async def approve_document(document_id: str):
    """
    Approve a document and set status to 'active'.
    """
    try:
        mark_document_reviewed(document_id, status='active')
        return {"message": "Document approved", "document_id": document_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{document_id}/reject")
async def reject_document(document_id: str):
    """
    Reject a document and set status to 'rejected'.
    """
    try:
        mark_document_reviewed(document_id, status='rejected')
        return {"message": "Document rejected", "document_id": document_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document permanently.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Delete related ingestion logs first
        cur.execute("DELETE FROM ingestion_log WHERE document_id = %s", (document_id,))

        # Delete the document
        cur.execute("DELETE FROM imprint_documents WHERE id = %s", (document_id,))

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Document deleted", "document_id": document_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
