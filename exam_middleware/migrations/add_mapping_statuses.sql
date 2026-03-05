-- Migration: Add MAPPING_FAILED and MAPPING_AMBIGUOUS to workflowstatus enum
-- Run this on the production PostgreSQL database BEFORE deploying the new code.
-- PostgreSQL requires ALTER TYPE to add new values to an existing enum.
-- These are safe, additive operations — no data loss.

ALTER TYPE workflowstatus ADD VALUE IF NOT EXISTS 'MAPPING_FAILED';
ALTER TYPE workflowstatus ADD VALUE IF NOT EXISTS 'MAPPING_AMBIGUOUS';
