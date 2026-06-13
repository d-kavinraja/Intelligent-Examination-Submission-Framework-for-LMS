-- Attempt 1/Attempt 2 submission synchronization queries.
-- PostgreSQL bind parameters use :name notation for application/migration runners.

-- 1. Lock the assessment group after Attempt 1 is submitted.
UPDATE examination_artifacts
SET attempt_2_locked = TRUE
WHERE parsed_reg_no = :student_id
  AND parsed_subject_code = :subject_code
  AND exam_type = :exam_type;

-- 2. Staff opens Attempt 2 for the student.
-- The paper upload must happen after this update; the upload creates attempt_number = 2.
UPDATE examination_artifacts
SET attempt_2_locked = FALSE
WHERE parsed_reg_no = :student_id
  AND parsed_subject_code = :subject_code
  AND exam_type = :exam_type;

-- Clear any stale Attempt 2 completion row so the replacement can be submitted.
DELETE FROM exam_submissions
WHERE student_id = :student_id
  AND subject_code = :subject_code
  AND exam_type = :exam_type
  AND attempt_number = 2;

-- 3. Replace Attempt 1 with Attempt 2 after the student submits Attempt 2.
BEGIN;

WITH attempt_pair AS (
    SELECT
        a1.id AS attempt_1_artifact_id,
        a2.id AS attempt_2_artifact_id
    FROM examination_artifacts a2
    LEFT JOIN examination_artifacts a1
      ON a1.parsed_reg_no = a2.parsed_reg_no
     AND a1.parsed_subject_code = a2.parsed_subject_code
     AND a1.exam_type = a2.exam_type
     AND a1.attempt_number = 1
     AND a1.workflow_status <> 'DELETED'
    WHERE a2.id = :attempt_2_artifact_id
      AND a2.attempt_number = 2
)
DELETE FROM exam_submissions
WHERE student_id = :student_id
  AND subject_code = :subject_code
  AND exam_type = :exam_type
  AND attempt_number = 1;

UPDATE examination_artifacts
SET workflow_status = 'SUPERSEDED'
WHERE id = (
    SELECT attempt_1_artifact_id
    FROM (
        SELECT a1.id AS attempt_1_artifact_id
        FROM examination_artifacts a1
        WHERE a1.parsed_reg_no = :student_id
          AND a1.parsed_subject_code = :subject_code
          AND a1.exam_type = :exam_type
          AND a1.attempt_number = 1
          AND a1.workflow_status <> 'DELETED'
        LIMIT 1
    ) attempt_1
);

UPDATE examination_artifacts
SET attempt_2_locked = TRUE
WHERE parsed_reg_no = :student_id
  AND parsed_subject_code = :subject_code
  AND exam_type = :exam_type;

INSERT INTO audit_logs (
    action,
    action_category,
    actor_type,
    actor_id,
    actor_username,
    artifact_id,
    target_type,
    target_id,
    description,
    request_data,
    response_data
) VALUES (
    'attempt_1_replaced_by_attempt_2',
    'submit',
    'student',
    :moodle_user_id,
    :moodle_username,
    :attempt_2_artifact_id,
    'examination_artifact',
    :attempt_1_artifact_id,
    'Attempt 1 submission removed and replaced by Attempt 2',
    jsonb_build_object(
        'reg_no', :student_id,
        'subject_code', :subject_code,
        'exam_type', :exam_type,
        'removed_attempt', 1,
        'active_attempt', 2,
        'attempt_1_artifact_id', :attempt_1_artifact_id,
        'attempt_2_artifact_id', :attempt_2_artifact_id
    ),
    jsonb_build_object('unlock_previous_submission', :unlock_result_json::jsonb)
);

COMMIT;
