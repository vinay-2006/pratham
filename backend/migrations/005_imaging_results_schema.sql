-- ============================================================
-- PRATHAM — Migration 005: imaging_results table
-- Run this in Supabase SQL Editor
-- Safe to run multiple times (uses IF NOT EXISTS)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create imaging_results table
CREATE TABLE IF NOT EXISTS public.imaging_results (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id             UUID REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    evidence_id           UUID,
    model_name            TEXT NOT NULL DEFAULT 'task10_efficientnetb0_pneumonia',
    prediction            TEXT NOT NULL,
    pneumonia_probability REAL NOT NULL,
    confidence            REAL NOT NULL,
    created_at            TIMESTAMPTZ DEFAULT NOW()
);

-- If table already existed without these columns, add them
ALTER TABLE public.imaging_results
    ADD COLUMN IF NOT EXISTS evidence_id           UUID,
    ADD COLUMN IF NOT EXISTS model_name            TEXT NOT NULL DEFAULT 'task10_efficientnetb0_pneumonia',
    ADD COLUMN IF NOT EXISTS pneumonia_probability REAL NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS confidence            REAL NOT NULL DEFAULT 0;

-- Index on intake_id for fast patient lookups
CREATE INDEX IF NOT EXISTS idx_imaging_results_intake_id
    ON public.imaging_results (intake_id);

-- RLS
ALTER TABLE public.imaging_results ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all" ON public.imaging_results;
CREATE POLICY "service_role_all" ON public.imaging_results
    FOR ALL USING (true) WITH CHECK (true);
