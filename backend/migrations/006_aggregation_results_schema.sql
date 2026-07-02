-- ============================================================
-- PRATHAM — Migration 006: aggregation_results table
-- Run this in Supabase SQL Editor
-- Safe to run multiple times (uses IF NOT EXISTS)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- aggregation_results: one row per aggregation run for an intake
CREATE TABLE IF NOT EXISTS public.aggregation_results (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id               UUID        REFERENCES public.emergency_intake(id) ON DELETE CASCADE,

    -- Per-condition probability distribution (sums to 1.0 when not suppressed)
    acs_probability         REAL,
    pe_probability          REAL,
    pneumonia_probability   REAL,
    arrhythmia_probability  REAL,
    other_probability       REAL,

    -- Winning condition (argmax of probability distribution)
    primary_condition       TEXT,

    -- Suppression metadata
    confidence_suppressed   BOOLEAN     NOT NULL DEFAULT FALSE,
    suppression_reason      TEXT,

    -- Debug / audit payloads
    raw_scores_json         JSONB,
    evidence_breakdown_json JSONB,

    -- Which upstream sources were available at aggregation time
    source_summary_json     JSONB,

    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Fast lookups by intake
CREATE INDEX IF NOT EXISTS idx_aggregation_results_intake_id
    ON public.aggregation_results (intake_id);

-- Most-recent-first ordering index
CREATE INDEX IF NOT EXISTS idx_aggregation_results_created_at
    ON public.aggregation_results (created_at DESC);

-- RLS — service_role key bypasses; deny anon by default
ALTER TABLE public.aggregation_results ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all" ON public.aggregation_results;
CREATE POLICY "service_role_all" ON public.aggregation_results
    FOR ALL USING (true) WITH CHECK (true);
