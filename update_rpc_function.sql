-- Update match_imprint_documents to support multi-sector filtering
CREATE OR REPLACE FUNCTION match_imprint_documents(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5,
    filter_thesis TEXT DEFAULT NULL,
    filter_sector TEXT[] DEFAULT NULL,  -- Changed to array
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
      AND (filter_thesis IS NULL OR d.thesis = filter_thesis)
      AND (filter_sector IS NULL OR d.sector = ANY(filter_sector))  -- Updated to use ANY
      AND (filter_entities IS NULL OR d.entities && filter_entities)
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
