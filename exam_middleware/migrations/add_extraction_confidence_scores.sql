-- Migration: Add AI extraction confidence score columns
-- Purpose: Store confidence percentages from YOLO + CRNN models for visualization
-- Date: 2026-03-02

ALTER TABLE examination_artifacts
ADD COLUMN IF NOT EXISTS register_confidence INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS subject_confidence INTEGER DEFAULT NULL;

-- Add comment explaining the fields
COMMENT ON COLUMN examination_artifacts.register_confidence IS 'AI confidence score (0-100%) for register number extraction';
COMMENT ON COLUMN examination_artifacts.subject_confidence IS 'AI confidence score (0-100%) for subject code extraction';

-- Update existing records with NULL confidence (as fallback for historical data)
UPDATE examination_artifacts 
SET register_confidence = NULL, subject_confidence = NULL 
WHERE register_confidence IS NULL AND auto_processed = true;
