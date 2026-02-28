-- Migration Script: Add Auto-Processed Field to Track ML-Extracted Files
-- Target: PostgreSQL / Examination Middleware Database
-- Purpose: Track files that were auto-extracted and renamed via ML pipeline

-- Add auto_processed column to examination_artifacts table
-- This field indicates whether the file was extracted and renamed by the ML pipeline
ALTER TABLE examination_artifacts ADD COLUMN IF NOT EXISTS auto_processed BOOLEAN NOT NULL DEFAULT false;

-- Optional: Create an index for filtering queries
CREATE INDEX IF NOT EXISTS idx_examination_artifacts_auto_processed 
ON examination_artifacts(auto_processed) 
WHERE auto_processed = true;

-- Verification query (run after migration):
-- SELECT COUNT(*) FROM examination_artifacts WHERE auto_processed = true;
