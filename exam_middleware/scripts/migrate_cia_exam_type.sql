-- Migration Script: CIA Exam Type Separation & Re-Attempt Handling
-- Target: PostgreSQL / Examination Middleware Database

-- 1. Add exam_type columns with defaults
ALTER TABLE subject_mappings ADD COLUMN IF NOT EXISTS exam_type VARCHAR(10) NOT NULL DEFAULT 'CIA1';
ALTER TABLE examination_artifacts ADD COLUMN IF NOT EXISTS exam_type VARCHAR(10) NOT NULL DEFAULT 'CIA1';
ALTER TABLE examination_artifacts ADD COLUMN IF NOT EXISTS attempt_number INTEGER NOT NULL DEFAULT 1;

-- 2. Drop old unique constraints
-- Note: These names may vary if they were created automatically.
-- We drop the known named constraints and try to drop the default ones if they exist.

-- For subject_mappings
ALTER TABLE subject_mappings DROP CONSTRAINT IF EXISTS subject_mappings_subject_code_key;
ALTER TABLE subject_mappings DROP CONSTRAINT IF EXISTS uq_subject_code;

-- For examination_artifacts
-- The previous unique constraint was usually on (parsed_reg_no, parsed_subject_code)
ALTER TABLE examination_artifacts DROP CONSTRAINT IF EXISTS uq_paper_submission;
ALTER TABLE examination_artifacts DROP CONSTRAINT IF EXISTS examination_artifacts_parsed_reg_no_parsed_subject_code_key;

-- 3. Add new unique constraints
ALTER TABLE subject_mappings ADD CONSTRAINT uq_subject_exam_type UNIQUE (subject_code, exam_type);
ALTER TABLE examination_artifacts ADD CONSTRAINT uq_paper_submission UNIQUE (parsed_reg_no, parsed_subject_code, exam_type, attempt_number);

-- 4. Add index for exam_type performance
CREATE INDEX IF NOT EXISTS ix_artifacts_exam_type ON examination_artifacts (exam_type);

-- 5. Add SUPERSEDED to workflow_status enum
-- PostgreSQL ENUM handling: check if exists before adding
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid WHERE t.typname = 'workflowstatus' AND e.enumlabel = 'SUPERSEDED') THEN
        ALTER TYPE workflowstatus ADD VALUE 'SUPERSEDED';
    END IF;
END
$$;
