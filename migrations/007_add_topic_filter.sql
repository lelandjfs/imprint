-- Migration: Add topic filter with thematic matching
-- Date: 2026-03-16
-- Description: Enable topic-based filtering using pattern matching (not exact match)

DROP FUNCTION IF EXISTS match_imprint_documents(VECTOR, INT, TEXT[], TEXT[], TEXT[], TEXT[], INTEGER[], TEXT);

CREATE OR REPLACE FUNCTION match_imprint_documents(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    filter_sector TEXT[] DEFAULT NULL,
    filter_entities TEXT[] DEFAULT NULL,
    filter_sentiment TEXT[] DEFAULT NULL,
    filter_catalyst_window TEXT[] DEFAULT NULL,
    filter_weighting INTEGER[] DEFAULT NULL,
    filter_topic TEXT DEFAULT NULL,
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
LANGUAGE plpgsql
AS $$
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
      AND (filter_catalyst_window IS NULL OR d.catalyst_window = ANY(filter_catalyst_window))
      AND (filter_weighting IS NULL OR d.weighting = ANY(filter_weighting))
      AND (filter_topic IS NULL OR d.topic ILIKE '%' || filter_topic || '%')
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
