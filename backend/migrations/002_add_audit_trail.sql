-- ============================================================
-- PRATHAM — Migration: Add audit trail columns to investigation_recommendations
-- Run this in Supabase SQL Editor
-- ============================================================

-- Add audit trail columns
ALTER TABLE public.investigation_recommendations
  ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS approved_by TEXT,
  ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS rejected_by TEXT,
  ADD COLUMN IF NOT EXISTS review_notes TEXT;

-- Also add updated_at to emergency_intake for tracking status changes
ALTER TABLE public.emergency_intake
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
