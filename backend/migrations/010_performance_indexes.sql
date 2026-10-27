-- ============================================================================
-- 010_performance_indexes.sql
-- PRATHAM Performance Optimization — Missing Indexes + Workflow RPC
-- ============================================================================
--
-- PURPOSE:
--   1. Add missing indexes on 7 tables that have no index beyond PK
--   2. Add composite index on workflow_logs(intake_id, changed_at DESC)
--      to support get_batch_latest_status efficiently
--   3. Add RPC function for DISTINCT ON latest workflow status per intake
--
-- TABLES WITH EXISTING INDEXES (no changes needed):
--   pipeline_status     — idx_pipeline_intake, idx_pipeline_stage (UNIQUE)
--   evidence            — idx_evidence_intake_id, idx_evidence_investigation_id
--   lab_results         — idx_lab_results_intake_id
--   imaging_results     — idx_imaging_results_intake_id
--   aggregation_results — idx_aggregation_results_intake_id, idx_aggregation_results_created_at
--   workflow_logs       — idx_workflow_logs_intake_id, idx_workflow_logs_changed_at
--
-- TABLES MISSING INDEXES (added below):
--   emergency_intake          — created_at DESC, status
--   vitals                    — intake_id
--   symptoms                  — intake_id
--   nlp_extractions           — intake_id
--   risk_scores               — intake_id
--   investigation_recommendations — intake_id
--   preparation_alerts        — intake_id
--
-- ============================================================================


-- ── 1. emergency_intake ─────────────────────────────────────────────────────
-- Used by: list_recent (ORDER BY created_at DESC), dashboard (filter by status)

CREATE INDEX IF NOT EXISTS idx_emergency_intake_created_at
    ON public.emergency_intake (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_emergency_intake_status
    ON public.emergency_intake (status);


-- ── 2. vitals ───────────────────────────────────────────────────────────────
-- Used by: report_service FK join, patient queue FK join

CREATE INDEX IF NOT EXISTS idx_vitals_intake_id
    ON public.vitals (intake_id);


-- ── 3. symptoms ─────────────────────────────────────────────────────────────
-- Used by: report_service FK join

CREATE INDEX IF NOT EXISTS idx_symptoms_intake_id
    ON public.symptoms (intake_id);


-- ── 4. nlp_extractions ──────────────────────────────────────────────────────
-- Used by: report_service.get_by_intake_id

CREATE INDEX IF NOT EXISTS idx_nlp_extractions_intake_id
    ON public.nlp_extractions (intake_id);


-- ── 5. risk_scores ──────────────────────────────────────────────────────────
-- Used by: report_service FK join, patient queue FK join

CREATE INDEX IF NOT EXISTS idx_risk_scores_intake_id
    ON public.risk_scores (intake_id);


-- ── 6. investigation_recommendations ────────────────────────────────────────
-- Used by: get_by_intake_ids (nurse queue, doctor review batch queries)

CREATE INDEX IF NOT EXISTS idx_investigation_recommendations_intake_id
    ON public.investigation_recommendations (intake_id);


-- ── 7. preparation_alerts ───────────────────────────────────────────────────
-- Used by: get_by_intake_id (intake response, report)

CREATE INDEX IF NOT EXISTS idx_preparation_alerts_intake_id
    ON public.preparation_alerts (intake_id);


-- ── 8. workflow_logs — composite index ──────────────────────────────────────
-- Existing indexes: intake_id (single), changed_at DESC (single)
-- The batch query filters by intake_id AND orders by changed_at DESC.
-- A composite index allows the DB to do both in a single index scan.

CREATE INDEX IF NOT EXISTS idx_workflow_logs_intake_changed
    ON public.workflow_logs (intake_id, changed_at DESC);


-- ── 9. RPC: Efficient "latest workflow status per intake" ───────────────────
-- Uses DISTINCT ON (intake_id) with ORDER BY (intake_id, changed_at DESC)
-- to return exactly one row per intake — the most recent status.
-- This replaces the Python-side deduplication in get_batch_latest_status.

CREATE OR REPLACE FUNCTION public.get_latest_workflow_statuses(p_intake_ids UUID[])
RETURNS TABLE(intake_id UUID, new_status TEXT)
LANGUAGE sql
STABLE
AS $$
    SELECT DISTINCT ON (wl.intake_id)
           wl.intake_id,
           wl.new_status
      FROM public.workflow_logs wl
     WHERE wl.intake_id = ANY(p_intake_ids)
     ORDER BY wl.intake_id, wl.changed_at DESC;
$$;
