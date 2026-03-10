"""Documents endpoint for tag approval workflow."""

import os
import re
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from utils import get_db_connection, mark_document_reviewed
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

router = APIRouter(prefix="/api/documents", tags=["documents"])


class PendingDocument(BaseModel):
    """Pending document model."""

    id: str
    title: str
    source_type: str
    topic: str | None
    sector: str | None
    entities: list[str]
    sentiment: str | None
    document_type: str | None
    catalyst_window: str | None
    summary: str | None
    weighting: int | None
    content: str
    source_url: str | None
    ingested_date: str


class DocumentUpdateRequest(BaseModel):
    """Request model for document updates (auto-save)."""

    topic: str | None = None
    sector: str | None = None
    entities: list[str] | None = None
    sentiment: str | None = None
    document_type: str | None = None
    catalyst_window: str | None = None
    summary: str | None = None
    weighting: int | None = None


@router.get("/pending")
async def get_pending_documents():
    """
    Get all documents pending review.

    Returns documents with status='pending_review' for tag approval workflow.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, title, source_type, topic, sector, entities, sentiment, document_type, catalyst_window, summary, weighting, content, source_url, ingested_date
            FROM imprint_documents
            WHERE status = 'pending_review'
            ORDER BY ingested_date DESC
        """)

        columns = ['id', 'title', 'source_type', 'topic', 'sector', 'entities', 'sentiment', 'document_type', 'catalyst_window', 'summary', 'weighting', 'content', 'source_url', 'ingested_date']
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


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


@router.patch("/{document_id}")
async def update_document(document_id: str, update: DocumentUpdateRequest):
    """
    Update individual document fields.

    Used by TagApproval UI for auto-save functionality.
    Only provided fields will be updated.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Build dynamic UPDATE statement for only provided fields
        updates = []
        values = []

        if update.topic is not None:
            updates.append("topic = %s")
            values.append(update.topic)

        if update.sector is not None:
            updates.append("sector = %s")
            values.append(update.sector)

        if update.entities is not None:
            updates.append("entities = %s")
            values.append(update.entities)

        if update.sentiment is not None:
            updates.append("sentiment = %s")
            values.append(update.sentiment)

        if update.document_type is not None:
            updates.append("document_type = %s")
            values.append(update.document_type)

        if update.catalyst_window is not None:
            updates.append("catalyst_window = %s")
            values.append(update.catalyst_window)

        if update.summary is not None:
            updates.append("summary = %s")
            values.append(update.summary)

        if update.weighting is not None:
            updates.append("weighting = %s")
            values.append(update.weighting)

        if not updates:
            return {"message": "No fields to update", "document_id": document_id}

        # Add document_id to values
        values.append(document_id)

        # Execute update
        sql = f"UPDATE imprint_documents SET {', '.join(updates)} WHERE id = %s"
        cur.execute(sql, values)

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Document updated", "document_id": document_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def delete_source_file(source_type: str, source_url: str):
    """
    Delete source file from Gmail or Google Drive.

    - Gmail: Remove "Imprint" label (safer than delete)
    - Drive: Move file to trash (safer than permanent delete)

    Errors are logged but don't block the database deletion.
    """
    try:
        # Get Google credentials
        token_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'token.json')
        if not os.path.exists(token_file):
            print(f"Warning: token.json not found, cannot delete source file")
            return

        creds = Credentials.from_authorized_user_file(token_file)

        if source_type == 'email' and source_url:
            # Extract message ID from gmail://msg_id
            match = re.match(r'gmail://(.+)', source_url)
            if match:
                msg_id = match.group(1)

                # Remove Imprint label using Gmail API
                gmail = build('gmail', 'v1', credentials=creds)

                # Get Imprint label ID
                labels = gmail.users().labels().list(userId='me').execute()
                imprint_label = next((l for l in labels['labels'] if l['name'] == 'Imprint'), None)

                if imprint_label:
                    gmail.users().messages().modify(
                        userId='me',
                        id=msg_id,
                        body={'removeLabelIds': [imprint_label['id']]}
                    ).execute()
                    print(f"Removed Imprint label from email {msg_id}")

        elif source_type in ['pdf', 'image'] and source_url:
            # Extract file ID from Drive URL
            match = re.search(r'/d/([a-zA-Z0-9_-]+)', source_url)
            if match:
                file_id = match.group(1)

                # Trash file using Drive API
                drive = build('drive', 'v3', credentials=creds)
                drive.files().update(fileId=file_id, body={'trashed': True}).execute()
                print(f"Trashed Drive file {file_id}")

    except Exception as e:
        # Log error but don't raise - source deletion is best-effort
        print(f"Warning: Could not delete source file: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    delete_source: bool = Query(False, description="Also delete source file (Gmail/Drive)")
):
    """
    Delete a document permanently.

    If delete_source=True, also attempts to delete the source file:
    - Gmail: Removes "Imprint" label
    - Drive: Moves file to trash
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get source info if delete_source requested
        if delete_source:
            cur.execute(
                "SELECT source_type, source_url FROM imprint_documents WHERE id = %s",
                (document_id,)
            )
            row = cur.fetchone()
            if row:
                source_type, source_url = row
                delete_source_file(source_type, source_url)

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
