-- ============================================================
-- PRATHAM — Migration 006b: Add missing columns to aggregation_results
-- 
-- The original CREATE TABLE in 006 was never applied to the live DB.
-- This ALTER TABLE safely adds the 4 missing columns.
-- Safe to run multiple times (uses IF NOT EXISTS via DO block).
-- ============================================================

DO $$
BEGIN
    -- primary_condition: winning condition (argmax of probability distribution)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'aggregation_results'
          AND column_name = 'primary_condition'
    ) THEN
        ALTER TABLE public.aggregation_results
            ADD COLUMN primary_condition TEXT;
        RAISE NOTICE 'Added column: primary_condition';
    END IF;

    -- raw_scores_json: debug/audit payload of raw heuristic scores
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'aggregation_results'
          AND column_name = 'raw_scores_json'
    ) THEN
        ALTER TABLE public.aggregation_results
            ADD COLUMN raw_scores_json JSONB;
        RAISE NOTICE 'Added column: raw_scores_json';
    END IF;

    -- evidence_breakdown_json: per-condition explainability trail
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'aggregation_results'
          AND column_name = 'evidence_breakdown_json'
    ) THEN
        ALTER TABLE public.aggregation_results
            ADD COLUMN evidence_breakdown_json JSONB;
        RAISE NOTICE 'Added column: evidence_breakdown_json';
    END IF;

    -- source_summary_json: which upstream sources were available
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'aggregation_results'
          AND column_name = 'source_summary_json'
    ) THEN
        ALTER TABLE public.aggregation_results
            ADD COLUMN source_summary_json JSONB;
        RAISE NOTICE 'Added column: source_summary_json';
    END IF;
END
$$;

-- Drop the legacy total_evidence_strength column if it exists
-- (replaced by raw_scores_json in the new schema)
-- Uncomment the line below if you want to clean up:
-- ALTER TABLE public.aggregation_results DROP COLUMN IF EXISTS total_evidence_strength;
