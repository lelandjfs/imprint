"""Theses endpoint for thesis notebook workflow."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils import get_db_connection

router = APIRouter(prefix="/api/theses", tags=["theses"])


# ========== Pydantic Models ==========

class ThesisCreate(BaseModel):
    """Request model for creating a thesis."""
    title: str
    user_id: Optional[str] = None


class SectionCreate(BaseModel):
    """Request model for creating a section."""
    title: str = "New Section"
    content: str = ""
    position: Optional[int] = None


class SectionUpdate(BaseModel):
    """Request model for updating a section."""
    title: Optional[str] = None
    content: Optional[str] = None
    collapsed: Optional[bool] = None
    position: Optional[int] = None


class ThesisUpdate(BaseModel):
    """Request model for updating a thesis."""
    title: Optional[str] = None
    position: Optional[int] = None


class CitationAdd(BaseModel):
    """Request model for adding a citation."""
    document_id: str  # UUID as string
    position: Optional[int] = None


class Citation(BaseModel):
    """Citation response model."""
    id: str
    title: str
    sector: str | None
    sentiment: str | None
    summary: str | None
    document_id: str
    position: int


class Section(BaseModel):
    """Section response model."""
    id: str
    thesis_id: str
    title: str
    content: str
    position: int
    collapsed: bool
    citations: List[Citation]
    created_at: str
    updated_at: str


class Thesis(BaseModel):
    """Thesis response model."""
    id: str
    title: str
    position: int
    sections: List[Section]
    created_at: str
    updated_at: str


# ========== Endpoints ==========

@router.get("")
async def list_theses(user_id: Optional[str] = None):
    """
    Get all theses, ordered by position.

    Returns theses with nested sections and citations.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all theses
        where_clause = "WHERE user_id = %s" if user_id else ""
        params = (user_id,) if user_id else ()

        cur.execute(f"""
            SELECT id, title, position, created_at, updated_at
            FROM theses
            {where_clause}
            ORDER BY position, created_at DESC
        """, params)

        theses = []
        for row in cur.fetchall():
            thesis_id = str(row[0])

            # Get sections for this thesis
            cur.execute("""
                SELECT id, thesis_id, title, content, position, collapsed, created_at, updated_at
                FROM thesis_sections
                WHERE thesis_id = %s
                ORDER BY position
            """, (thesis_id,))

            sections = []
            for section_row in cur.fetchall():
                section_id = str(section_row[0])

                # Get citations for this section
                cur.execute("""
                    SELECT
                        tc.id,
                        d.title,
                        d.sector,
                        d.sentiment,
                        d.summary,
                        d.id as document_id,
                        tc.position
                    FROM thesis_citations tc
                    JOIN imprint_documents d ON tc.document_id = d.id
                    WHERE tc.section_id = %s
                    ORDER BY tc.position
                """, (section_id,))

                citations = [
                    Citation(
                        id=str(cit[0]),
                        title=cit[1],
                        sector=cit[2],
                        sentiment=cit[3],
                        summary=cit[4],
                        document_id=str(cit[5]),
                        position=cit[6] or 0
                    )
                    for cit in cur.fetchall()
                ]

                sections.append(Section(
                    id=section_id,
                    thesis_id=str(section_row[1]),
                    title=section_row[2],
                    content=section_row[3] or "",
                    position=section_row[4] or 0,
                    collapsed=section_row[5] or False,
                    citations=citations,
                    created_at=section_row[6].isoformat(),
                    updated_at=section_row[7].isoformat()
                ))

            theses.append(Thesis(
                id=thesis_id,
                title=row[1],
                position=row[2] or 0,
                sections=sections,
                created_at=row[3].isoformat(),
                updated_at=row[4].isoformat()
            ))

        cur.close()
        conn.close()

        return {"theses": theses}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_thesis(thesis: ThesisCreate):
    """Create a new thesis."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO theses (title, user_id)
            VALUES (%s, %s)
            RETURNING id, title, position, created_at, updated_at
        """, (thesis.title, thesis.user_id))

        row = cur.fetchone()
        thesis_id = str(row[0])

        conn.commit()
        cur.close()
        conn.close()

        return Thesis(
            id=thesis_id,
            title=row[1],
            position=row[2] or 0,
            sections=[],
            created_at=row[3].isoformat(),
            updated_at=row[4].isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{thesis_id}")
async def update_thesis(thesis_id: str, update: ThesisUpdate):
    """Update thesis fields (auto-save)."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        updates = []
        values = []

        if update.title is not None:
            updates.append("title = %s")
            values.append(update.title)

        if update.position is not None:
            updates.append("position = %s")
            values.append(update.position)

        if not updates:
            return {"message": "No fields to update"}

        values.append(thesis_id)
        sql = f"UPDATE theses SET {', '.join(updates)} WHERE id = %s"
        cur.execute(sql, values)

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Thesis updated", "thesis_id": thesis_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{thesis_id}")
async def delete_thesis(thesis_id: str):
    """Delete a thesis (cascades to sections and citations)."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM theses WHERE id = %s", (thesis_id,))

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Thesis deleted", "thesis_id": thesis_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{thesis_id}/sections")
async def create_section(thesis_id: str, section: SectionCreate):
    """Create a new section in a thesis."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get max position if not provided
        position = section.position
        if position is None:
            cur.execute("""
                SELECT COALESCE(MAX(position), -1) + 1
                FROM thesis_sections
                WHERE thesis_id = %s
            """, (thesis_id,))
            position = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO thesis_sections (thesis_id, title, content, position)
            VALUES (%s, %s, %s, %s)
            RETURNING id, thesis_id, title, content, position, collapsed, created_at, updated_at
        """, (thesis_id, section.title, section.content, position))

        row = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()

        return Section(
            id=str(row[0]),
            thesis_id=str(row[1]),
            title=row[2],
            content=row[3] or "",
            position=row[4] or 0,
            collapsed=row[5] or False,
            citations=[],
            created_at=row[6].isoformat(),
            updated_at=row[7].isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{thesis_id}/sections/{section_id}")
async def update_section(thesis_id: str, section_id: str, update: SectionUpdate):
    """Update section fields (auto-save)."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        updates = []
        values = []

        if update.title is not None:
            updates.append("title = %s")
            values.append(update.title)

        if update.content is not None:
            updates.append("content = %s")
            values.append(update.content)

        if update.collapsed is not None:
            updates.append("collapsed = %s")
            values.append(update.collapsed)

        if update.position is not None:
            updates.append("position = %s")
            values.append(update.position)

        if not updates:
            return {"message": "No fields to update"}

        values.append(section_id)
        sql = f"UPDATE thesis_sections SET {', '.join(updates)} WHERE id = %s"
        cur.execute(sql, values)

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Section updated", "section_id": section_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{thesis_id}/sections/{section_id}")
async def delete_section(thesis_id: str, section_id: str):
    """Delete a section (cascades to citations)."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM thesis_sections WHERE id = %s", (section_id,))

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Section deleted", "section_id": section_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{thesis_id}/sections/{section_id}/citations")
async def add_citation(thesis_id: str, section_id: str, citation: CitationAdd):
    """Add a citation to a section."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get max position if not provided
        position = citation.position
        if position is None:
            cur.execute("""
                SELECT COALESCE(MAX(position), -1) + 1
                FROM thesis_citations
                WHERE section_id = %s
            """, (section_id,))
            position = cur.fetchone()[0]

        # Insert citation (may fail if duplicate)
        try:
            cur.execute("""
                INSERT INTO thesis_citations (section_id, document_id, position)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (section_id, citation.document_id, position))
            citation_id = str(cur.fetchone()[0])
            conn.commit()
        except Exception as e:
            # Handle unique constraint violation
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise HTTPException(status_code=400, detail="Citation already exists in this section")
            raise

        cur.close()
        conn.close()

        return {"message": "Citation added", "citation_id": citation_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{thesis_id}/sections/{section_id}/citations/{citation_id}")
async def remove_citation(thesis_id: str, section_id: str, citation_id: str):
    """Remove a citation from a section."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("DELETE FROM thesis_citations WHERE id = %s", (citation_id,))

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Citation removed", "citation_id": citation_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{thesis_id}/sections/{section_id}/citations/move")
async def move_citation(
    thesis_id: str,
    section_id: str,
    citation: CitationAdd,
    from_section_id: str
):
    """
    Move a citation from one section to another.

    This is a transaction that removes from source and adds to target.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Begin transaction
        cur.execute("BEGIN")

        # Remove from source section
        cur.execute("""
            DELETE FROM thesis_citations
            WHERE section_id = %s AND document_id = %s
        """, (from_section_id, citation.document_id))

        # Add to target section
        position = citation.position
        if position is None:
            cur.execute("""
                SELECT COALESCE(MAX(position), -1) + 1
                FROM thesis_citations
                WHERE section_id = %s
            """, (section_id,))
            position = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO thesis_citations (section_id, document_id, position)
            VALUES (%s, %s, %s)
            ON CONFLICT (section_id, document_id) DO NOTHING
            RETURNING id
        """, (section_id, citation.document_id, position))

        result = cur.fetchone()
        if result:
            citation_id = str(result[0])
        else:
            # Citation already exists in target
            raise HTTPException(status_code=400, detail="Citation already exists in target section")

        conn.commit()
        cur.close()
        conn.close()

        return {"message": "Citation moved", "citation_id": citation_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
