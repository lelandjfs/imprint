-- Migration: Add investing-focused schema fields
-- Adds: sentiment, weighting
-- Makes nullable: thesis, document_type, angle, catalyst_window (backward compatibility)

-- Add new fields
ALTER TABLE imprint_documents
ADD COLUMN IF NOT EXISTS sentiment TEXT CHECK (sentiment IN ('bullish', 'bearish', 'neutral', 'mixed')),
ADD COLUMN IF NOT EXISTS weighting INTEGER CHECK (weighting >= 1 AND weighting <= 5);

-- Make old fields nullable for backward compatibility
ALTER TABLE imprint_documents
ALTER COLUMN thesis DROP NOT NULL,
ALTER COLUMN document_type DROP NOT NULL,
ALTER COLUMN angle DROP NOT NULL,
ALTER COLUMN catalyst_window DROP NOT NULL;

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_sentiment ON imprint_documents(sentiment);
CREATE INDEX IF NOT EXISTS idx_weighting ON imprint_documents(weighting);

-- Verify changes
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'imprint_documents'
AND column_name IN ('sentiment', 'weighting', 'thesis', 'document_type', 'angle', 'catalyst_window')
ORDER BY column_name;
