-- Migration: Create theses, thesis_sections, and thesis_citations tables
-- Date: 2026-03-12
-- Description: Database schema for thesis notebook feature with drag-and-drop citations

-- Create theses table
CREATE TABLE IF NOT EXISTS theses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id TEXT,
    position INTEGER DEFAULT 0
);

-- Create thesis_sections table
CREATE TABLE IF NOT EXISTS thesis_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thesis_id UUID NOT NULL REFERENCES theses(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Untitled Section',
    content TEXT DEFAULT '',
    position INTEGER NOT NULL DEFAULT 0,
    collapsed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create thesis_citations junction table
CREATE TABLE IF NOT EXISTS thesis_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id UUID NOT NULL REFERENCES thesis_sections(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES imprint_documents(id) ON DELETE CASCADE,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(section_id, document_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_thesis_sections_thesis_id ON thesis_sections(thesis_id);
CREATE INDEX IF NOT EXISTS idx_thesis_sections_position ON thesis_sections(thesis_id, position);
CREATE INDEX IF NOT EXISTS idx_thesis_citations_section_id ON thesis_citations(section_id);
CREATE INDEX IF NOT EXISTS idx_thesis_citations_document_id ON thesis_citations(document_id);

-- Create trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_theses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for theses table
DROP TRIGGER IF EXISTS theses_updated_at_trigger ON theses;
CREATE TRIGGER theses_updated_at_trigger
    BEFORE UPDATE ON theses
    FOR EACH ROW
    EXECUTE FUNCTION update_theses_updated_at();

-- Create trigger for thesis_sections table
DROP TRIGGER IF EXISTS thesis_sections_updated_at_trigger ON thesis_sections;
CREATE TRIGGER thesis_sections_updated_at_trigger
    BEFORE UPDATE ON thesis_sections
    FOR EACH ROW
    EXECUTE FUNCTION update_theses_updated_at();
