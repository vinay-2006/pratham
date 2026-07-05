-- ============================================================
-- PRATHAM — Full database schema
-- Run this in Supabase SQL Editor to recreate all tables
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. PATIENTS
CREATE TABLE IF NOT EXISTS public.patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth TEXT,
    gender TEXT,
    contact_number TEXT,
    allergies TEXT[] DEFAULT '{}',
    current_medications TEXT[] DEFAULT '{}',
    past_medical_history TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. EMERGENCY INTAKE
CREATE TABLE IF NOT EXISTS public.emergency_intake (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES public.patients(id) ON DELETE CASCADE,
    ambulance_eta INTEGER,
    emergency_description TEXT,
    chief_complaint TEXT,
    status TEXT DEFAULT 'intake_pending',
    severity_level TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. VITALS
CREATE TABLE IF NOT EXISTS public.vitals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES public.patients(id) ON DELETE CASCADE,
    intake_id UUID REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    heart_rate REAL,
    spo2 REAL,
    bp_systolic REAL,
    bp_diastolic REAL,
    temperature REAL,
    respiratory_rate REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. SYMPTOMS
CREATE TABLE IF NOT EXISTS public.symptoms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id UUID REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    chest_pain BOOLEAN DEFAULT FALSE,
    breathlessness BOOLEAN DEFAULT FALSE,
    trauma BOOLEAN DEFAULT FALSE,
    bleeding BOOLEAN DEFAULT FALSE,
    unconsciousness BOOLEAN DEFAULT FALSE,
    neurological_symptoms BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. NLP EXTRACTIONS
CREATE TABLE IF NOT EXISTS public.nlp_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id UUID REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    head_trauma BOOLEAN DEFAULT FALSE,
    loss_of_consciousness BOOLEAN DEFAULT FALSE,
    neurological_risk_flag BOOLEAN DEFAULT FALSE,
    respiratory_distress BOOLEAN DEFAULT FALSE,
    cardiac_risk_flag BOOLEAN DEFAULT FALSE,
    extracted_entities TEXT[] DEFAULT '{}',
    raw_llm_output JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. RISK SCORES
CREATE TABLE IF NOT EXISTS public.risk_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id UUID REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    cardiac_risk INTEGER DEFAULT 0,
    respiratory_risk INTEGER DEFAULT 0,
    trauma_risk INTEGER DEFAULT 0,
    neurological_risk INTEGER DEFAULT 0,
    overall_severity TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. PREPARATION ALERTS
CREATE TABLE IF NOT EXISTS public.preparation_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id UUID REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. INVESTIGATION RECOMMENDATIONS
CREATE TABLE IF NOT EXISTS public.investigation_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id UUID REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    investigation_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending_approval',
    approved_at TIMESTAMPTZ,
    approved_by TEXT,
    rejected_at TIMESTAMPTZ,
    rejected_by TEXT,
    review_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. PIPELINE STATUS (Task 14)
CREATE TABLE IF NOT EXISTS public.pipeline_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intake_id UUID NOT NULL REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    stage TEXT NOT NULL CHECK (stage IN ('nlp', 'risk', 'lab', 'imaging', 'aggregation')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    error_message TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pipeline_stage ON public.pipeline_status(intake_id, stage);
CREATE INDEX IF NOT EXISTS idx_pipeline_intake ON public.pipeline_status(intake_id);

-- ============================================================
-- Disable RLS on all tables (service_role key bypasses anyway)
-- ============================================================
ALTER TABLE public.patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.emergency_intake ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.symptoms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nlp_extractions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.risk_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.preparation_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investigation_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pipeline_status ENABLE ROW LEVEL SECURITY;

-- Allow service_role full access
CREATE POLICY "service_role_all" ON public.patients FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON public.emergency_intake FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON public.vitals FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON public.symptoms FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON public.nlp_extractions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON public.risk_scores FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON public.preparation_alerts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON public.investigation_recommendations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON public.pipeline_status FOR ALL USING (true) WITH CHECK (true);

