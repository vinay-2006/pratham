-- ============================================================
-- PRATHAM — Migration 004b: Ensure lab_results has all needed columns
-- Run this in Supabase SQL Editor after 004_lab_results_schema.sql
-- Safe to run even if table already exists (uses IF NOT EXISTS / ADD COLUMN IF NOT EXISTS)
-- ============================================================

-- Create table if it doesn't exist yet (full schema)
CREATE TABLE IF NOT EXISTS public.lab_results (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id        UUID REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    model_name       TEXT NOT NULL DEFAULT 'task9_xgboost_heart_model',
    prediction       TEXT NOT NULL,
    risk_probability REAL NOT NULL,
    shap_values      JSONB,
    input_features   JSONB,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- If table already existed without these columns, add them
ALTER TABLE public.lab_results
    ADD COLUMN IF NOT EXISTS model_name       TEXT NOT NULL DEFAULT 'task9_xgboost_heart_model',
    ADD COLUMN IF NOT EXISTS shap_values      JSONB,
    ADD COLUMN IF NOT EXISTS input_features   JSONB;

-- Index
CREATE INDEX IF NOT EXISTS idx_lab_results_intake_id
    ON public.lab_results (intake_id);

-- RLS
ALTER TABLE public.lab_results ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all" ON public.lab_results;
CREATE POLICY "service_role_all" ON public.lab_results
    FOR ALL USING (true) WITH CHECK (true);
