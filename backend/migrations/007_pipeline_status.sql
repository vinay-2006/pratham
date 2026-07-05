-- ============================================================
-- Migration 007: Pipeline Status Tracking
-- Tracks the execution state of each AI subsystem stage
-- per emergency intake. Central source of truth for pipeline
-- progress used by both Nurse Workspace and Doctor Report.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.pipeline_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    intake_id UUID NOT NULL
        REFERENCES public.emergency_intake(id)
        ON DELETE CASCADE,

    stage TEXT NOT NULL
        CHECK (
            stage IN (
                'nlp',
                'risk',
                'lab',
                'imaging',
                'aggregation'
            )
        ),

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (
            status IN (
                'pending',
                'running',
                'completed',
                'failed'
            )
        ),

    started_at   TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms  INTEGER,
    error_message TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,

    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- One row per stage per intake
CREATE UNIQUE INDEX IF NOT EXISTS idx_pipeline_stage
    ON public.pipeline_status(intake_id, stage);

-- Fast lookup by intake
CREATE INDEX IF NOT EXISTS idx_pipeline_intake
    ON public.pipeline_status(intake_id);

-- RLS + service_role policy (consistent with rest of schema)
ALTER TABLE public.pipeline_status ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_all"
    ON public.pipeline_status
    FOR ALL
    USING (true)
    WITH CHECK (true);
