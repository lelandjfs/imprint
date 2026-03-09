-- First drop the old function to avoid overload conflicts
DROP FUNCTION IF EXISTS match_imprint_documents(
    query_embedding VECTOR(1536),
    match_count INT,
    filter_thesis TEXT,
    filter_sector TEXT,
    filter_entities TEXT[],
    filter_status TEXT
);

-- Create the new multi-select function
CREATE OR REPLACE FUNCTION match_imprint_documents(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    filter_thesis TEXT[] DEFAULT NULL,  -- Changed to array for multi-select
    filter_sector TEXT[] DEFAULT NULL,  -- Changed to array for multi-select
    filter_entities TEXT[] DEFAULT NULL,
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
        d.source_url,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM imprint_documents d
    WHERE d.status = filter_status
      AND (filter_thesis IS NULL OR d.thesis = ANY(filter_thesis))  -- Updated to use ANY for multi-select
      AND (filter_sector IS NULL OR d.sector = ANY(filter_sector))  -- Updated to use ANY for multi-select
      AND (filter_entities IS NULL OR d.entities && filter_entities)
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
