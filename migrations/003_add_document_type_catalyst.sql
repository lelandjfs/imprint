-- Add document_type and catalyst_window back
ALTER TABLE imprint_documents
ADD COLUMN IF NOT EXISTS document_type TEXT CHECK (document_type IN ('memo', 'article', 'research_report', 'transcript', 'presentation', 'other')),
ADD COLUMN IF NOT EXISTS catalyst_window TEXT CHECK (catalyst_window IN ('immediate', 'near_term', 'medium_term', 'long_term', 'structural'));

-- Remove old unused columns (thesis, angle)
ALTER TABLE imprint_documents
DROP COLUMN IF EXISTS thesis,
DROP COLUMN IF EXISTS angle;

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_document_type ON imprint_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_catalyst_window ON imprint_documents(catalyst_window);
