-- 008_workflow_updates.sql
ALTER TABLE public.emergency_intake 
ADD COLUMN IF NOT EXISTS case_id TEXT UNIQUE,
ADD COLUMN IF NOT EXISTS arrival_type TEXT DEFAULT 'walk_in';

CREATE TABLE IF NOT EXISTS public.workflow_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id UUID REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    old_status TEXT,
    new_status TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('System', 'Nurse', 'Doctor')),
    actor_name TEXT NOT NULL,
    reason TEXT,
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.workflow_logs ENABLE ROW LEVEL SECURITY;

-- If policy exists, drop it first to avoid duplicate errors
DROP POLICY IF EXISTS "service_role_all" ON public.workflow_logs;
CREATE POLICY "service_role_all" ON public.workflow_logs FOR ALL USING (true) WITH CHECK (true);
