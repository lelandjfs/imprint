-- Migration: Update match_imprint_documents RPC function to include sentiment filtering
-- Adds sentiment parameter and returns sentiment field

-- Drop all previous versions to avoid overload conflicts
DROP FUNCTION IF EXISTS match_imprint_documents(
    query_embedding VECTOR(1536),
    match_count INT,
    filter_thesis TEXT,
    filter_sector TEXT,
    filter_entities TEXT[],
    filter_status TEXT
);

DROP FUNCTION IF EXISTS match_imprint_documents(
    query_embedding VECTOR(1536),
    match_count INT,
    filter_thesis TEXT[],
    filter_sector TEXT[],
    filter_entities TEXT[],
    filter_status TEXT
);

-- Create updated function with sentiment support
CREATE OR REPLACE FUNCTION match_imprint_documents(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    filter_thesis TEXT[] DEFAULT NULL,
    filter_sector TEXT[] DEFAULT NULL,
    filter_entities TEXT[] DEFAULT NULL,
    filter_sentiment TEXT[] DEFAULT NULL,  -- NEW: Sentiment filter
    filter_status TEXT DEFAULT 'active'
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    summary TEXT,
    thesis TEXT,
    topic TEXT,
    sector TEXT,
    entities TEXT[],
    sentiment TEXT,    -- NEW: Return sentiment
    weighting INTEGER, -- NEW: Return weighting
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
        d.thesis,
        d.topic,
        d.sector,
        d.entities,
        d.sentiment,        -- NEW: Include sentiment in results
        d.weighting,        -- NEW: Include weighting in results
        d.source_url,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM imprint_documents d
    WHERE d.status = filter_status
      AND (filter_thesis IS NULL OR d.thesis = ANY(filter_thesis))
      AND (filter_sector IS NULL OR d.sector = ANY(filter_sector))
      AND (filter_entities IS NULL OR d.entities && filter_entities)
      AND (filter_sentiment IS NULL OR d.sentiment = ANY(filter_sentiment))  -- NEW: Sentiment filter
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
