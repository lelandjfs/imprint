-- Migration: Add unique constraint on source_url to prevent duplicate documents
-- Date: 2026-03-30
-- Description: Prevents race condition duplicates by enforcing uniqueness at database level
--              This ensures the same source (email, PDF, bookmark) cannot be ingested multiple times
--              even if multiple processes run simultaneously

ALTER TABLE imprint_documents
ADD CONSTRAINT unique_source_url UNIQUE (source_url);
