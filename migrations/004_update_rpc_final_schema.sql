-- Migration: Update match_imprint_documents RPC function for final schema
-- Removes thesis, adds document_type and catalyst_window

-- Drop previous version
DROP FUNCTION IF EXISTS match_imprint_documents(
    query_embedding VECTOR(1536),
    match_count INT,
    filter_thesis TEXT[],
    filter_sector TEXT[],
    filter_entities TEXT[],
    filter_sentiment TEXT[],
    filter_status TEXT
);

-- Create final version with document_type and catalyst_window
CREATE OR REPLACE FUNCTION match_imprint_documents(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    filter_sector TEXT[] DEFAULT NULL,
    filter_entities TEXT[] DEFAULT NULL,
    filter_sentiment TEXT[] DEFAULT NULL,
    filter_status TEXT DEFAULT 'active'
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    summary TEXT,
    topic TEXT,
    sector TEXT,
    entities TEXT[],
    sentiment TEXT,
    document_type TEXT,
    catalyst_window TEXT,
    weighting INTEGER,
    source_url TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.title,
        d.content,
        d.summary,
        d.topic,
        d.sector,
        d.entities,
        d.sentiment,
        d.document_type,
        d.catalyst_window,
        d.weighting,
        d.source_url,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM imprint_documents d
    WHERE d.status = filter_status
      AND (filter_sector IS NULL OR d.sector = ANY(filter_sector))
      AND (filter_entities IS NULL OR d.entities && filter_entities)
      AND (filter_sentiment IS NULL OR d.sentiment = ANY(filter_sentiment))
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
