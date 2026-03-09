"""Utility functions for the API."""

import os
import psycopg2
from config import get_settings


def get_db_connection():
    """Get database connection."""
    settings = get_settings()
    return psycopg2.connect(settings.database_url)


def mark_document_reviewed(doc_id, status='active'):
    """Mark a document as reviewed."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE imprint_documents
        SET status = %s
        WHERE id = %s
    """, (status, doc_id))

    conn.commit()
    cur.close()
    conn.close()
