-- ============================================================
-- PRATHAM — Migration 003: Add investigation_id FK to evidence table
-- Run this in Supabase SQL Editor
-- ============================================================

-- Add investigation_id FK column so evidence rows can be linked
-- to the specific investigation_recommendations row they satisfy.
-- ON DELETE SET NULL: removing an investigation doesn't orphan the file.
ALTER TABLE public.evidence
  ADD COLUMN IF NOT EXISTS investigation_id UUID
    REFERENCES public.investigation_recommendations(id) ON DELETE SET NULL;

-- Index for fast evidence lookups by investigation
CREATE INDEX IF NOT EXISTS idx_evidence_investigation_id
  ON public.evidence (investigation_id);

-- Ensure the evidence table has RLS enabled and service_role policy
ALTER TABLE public.evidence ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "service_role_all" ON public.evidence;
CREATE POLICY "service_role_all" ON public.evidence
  FOR ALL USING (true) WITH CHECK (true);
