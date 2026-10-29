-- ============================================================================
-- PRATHAM v7.0 — Consolidated Database Schema
-- ============================================================================
--
-- This file is the SINGLE SOURCE OF TRUTH for all PRATHAM database objects.
-- It consolidates the base schema.sql and all 9 migrations (002–008) into one
-- definitive DDL.
--
-- PURPOSE:   Documentation artifact. Represents the complete target schema.
-- USAGE:     Reference only. Do NOT run blindly against a populated database.
--            For fresh installations, this file can be executed in order.
--
-- Tables:    14 total (listed below with domain ownership)
-- Generated: 2026-07-11
-- ============================================================================


-- ============================================================================
-- 0. EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================================
-- 1. PATIENTS
-- Domain Owner: Patient
-- Type: Current State (operational)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.patients (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name          TEXT        NOT NULL,
    last_name           TEXT        NOT NULL,
    date_of_birth       TEXT,                              -- ISO 8601 date string
    gender              TEXT,                              -- male | female | other | prefer_not_to_say
    contact_number      TEXT,
    allergies           TEXT[]      DEFAULT '{}',
    current_medications TEXT[]      DEFAULT '{}',
    past_medical_history TEXT[]     DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================================
-- 2. EMERGENCY INTAKE
-- Domain Owner: Triage
-- Type: Current State (operational)
-- Status: Projection column — authoritative status derived from workflow_logs
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.emergency_intake (
    id                    UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id            UUID        REFERENCES public.patients(id) ON DELETE CASCADE,
    case_id               TEXT        UNIQUE,                -- Human-readable ID (e.g. ED-20260711-0001)
    arrival_type          TEXT        DEFAULT 'walk_in',     -- walk_in | ambulance | referral
    ambulance_eta         INTEGER,                           -- Minutes (null if walk_in/referral)
    emergency_description TEXT,
    chief_complaint       TEXT,
    status                TEXT        DEFAULT 'intake_submitted'
                          CHECK (status IN (
                              'intake_submitted',
                              'en_route',
                              'arrived',
                              'awaiting_doctor_approval',
                              'investigations_approved',
                              'evidence_upload_pending',
                              'analysis_running',
                              'clinical_report_ready',
                              'under_doctor_review',
                              'case_closed',
                              'offline_care'
                          )),
    severity_level        TEXT,                              -- low | moderate | high | critical
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    updated_at            TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================================
-- 3. VITALS
-- Domain Owner: Triage
-- Type: Current State (operational)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.vitals (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id       UUID        REFERENCES public.patients(id) ON DELETE CASCADE,
    intake_id        UUID        REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    heart_rate       REAL,
    spo2             REAL,
    bp_systolic      REAL,
    bp_diastolic     REAL,
    temperature      REAL,
    respiratory_rate REAL,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================================
-- 4. SYMPTOMS
-- Domain Owner: Triage
-- Type: Current State (operational)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.symptoms (
    id                     UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id              UUID        REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    chest_pain             BOOLEAN     DEFAULT FALSE,
    breathlessness         BOOLEAN     DEFAULT FALSE,
    trauma                 BOOLEAN     DEFAULT FALSE,
    bleeding               BOOLEAN     DEFAULT FALSE,
    unconsciousness        BOOLEAN     DEFAULT FALSE,
    neurological_symptoms  BOOLEAN     DEFAULT FALSE,
    created_at             TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================================
-- 5. NLP EXTRACTIONS
-- Domain Owner: AI
-- Type: Current State (operational — latest extraction per intake)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.nlp_extractions (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id               UUID        REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    head_trauma             BOOLEAN     DEFAULT FALSE,
    loss_of_consciousness   BOOLEAN     DEFAULT FALSE,
    neurological_risk_flag  BOOLEAN     DEFAULT FALSE,
    respiratory_distress    BOOLEAN     DEFAULT FALSE,
    cardiac_risk_flag       BOOLEAN     DEFAULT FALSE,
    extracted_entities      TEXT[]      DEFAULT '{}',
    raw_llm_output          JSONB,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================================
-- 6. RISK SCORES
-- Domain Owner: AI
-- Type: Current State (operational — latest scores per intake)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.risk_scores (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id           UUID        REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    cardiac_risk        INTEGER     DEFAULT 0,       -- 0-100
    respiratory_risk    INTEGER     DEFAULT 0,       -- 0-100
    trauma_risk         INTEGER     DEFAULT 0,       -- 0-100
    neurological_risk   INTEGER     DEFAULT 0,       -- 0-100
    overall_severity    TEXT,                         -- low | moderate | high | critical
    created_at          TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================================
-- 7. PREPARATION ALERTS
-- Domain Owner: Notification
-- Type: Current State (operational)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.preparation_alerts (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id   UUID        REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    alert_type  TEXT        NOT NULL,     -- icu_standby | oxygen_prep | trauma_team | ct_scanner | emergency_bed | blood_bank
    status      TEXT        DEFAULT 'pending',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================================
-- 8. INVESTIGATION RECOMMENDATIONS
-- Domain Owner: Investigation
-- Type: Current State (operational)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.investigation_recommendations (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id           UUID        REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    investigation_type  TEXT        NOT NULL,
    status              TEXT        DEFAULT 'pending_approval'
                        CHECK (status IN ('pending_approval', 'approved', 'rejected', 'needs_info')),
    approved_at         TIMESTAMPTZ,
    approved_by         TEXT,
    rejected_at         TIMESTAMPTZ,
    rejected_by         TEXT,
    review_notes        TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);


-- ============================================================================
-- 9. PIPELINE STATUS
-- Domain Owner: Pipeline
-- Type: Current State (operational — one row per stage per intake)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.pipeline_status (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    intake_id       UUID        NOT NULL REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    stage           TEXT        NOT NULL CHECK (stage IN ('nlp', 'risk', 'lab', 'imaging', 'aggregation')),
    status          TEXT        NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    duration_ms     INTEGER,
    error_message   TEXT,
    attempt_count   INTEGER     NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pipeline_stage
    ON public.pipeline_status(intake_id, stage);

CREATE INDEX IF NOT EXISTS idx_pipeline_intake
    ON public.pipeline_status(intake_id);


-- ============================================================================
-- 10. EVIDENCE
-- Domain Owner: Evidence
-- Type: Current State (operational)
-- NOTE: This table was created directly in Supabase and never had formal DDL.
--       This is the first formal schema definition.
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.evidence (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id           UUID        NOT NULL REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    investigation_id    UUID        REFERENCES public.investigation_recommendations(id) ON DELETE SET NULL,
    evidence_type       TEXT        NOT NULL
                        CHECK (evidence_type IN ('xray', 'lab_report', 'ecg', 'clinical_notes', 'ct_scan', 'mri', 'blood_work', 'ultrasound')),
    file_name           TEXT        NOT NULL,
    file_url            TEXT,                    -- Signed URL (time-limited)
    file_size           INTEGER,                 -- Bytes
    uploaded_at         TIMESTAMPTZ DEFAULT NOW(),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_intake_id
    ON public.evidence(intake_id);

CREATE INDEX IF NOT EXISTS idx_evidence_investigation_id
    ON public.evidence(investigation_id);


-- ============================================================================
-- 11. LAB RESULTS
-- Domain Owner: AI
-- Type: Current State (operational — ML model predictions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.lab_results (
    id                UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id         UUID        REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    model_name        TEXT        NOT NULL DEFAULT 'task9_xgboost_heart_model',
    prediction        TEXT        NOT NULL,
    risk_probability  REAL        NOT NULL,
    shap_values       JSONB,
    input_features    JSONB,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lab_results_intake_id
    ON public.lab_results(intake_id);


-- ============================================================================
-- 12. IMAGING RESULTS
-- Domain Owner: AI
-- Type: Current State (operational — ML model predictions)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.imaging_results (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id               UUID        REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    evidence_id             UUID,
    model_name              TEXT        NOT NULL DEFAULT 'task10_efficientnetb0_pneumonia',
    prediction              TEXT        NOT NULL,
    pneumonia_probability   REAL        NOT NULL DEFAULT 0,
    confidence              REAL        NOT NULL DEFAULT 0,
    gradcam_url             TEXT        DEFAULT '',      -- Signed URL to Grad-CAM heatmap overlay
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_imaging_results_intake_id
    ON public.imaging_results(intake_id);


-- ============================================================================
-- 13. AGGREGATION RESULTS
-- Domain Owner: AI (Clinical Reasoning)
-- Type: Current State (operational — latest aggregation per intake)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.aggregation_results (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id               UUID        REFERENCES public.emergency_intake(id) ON DELETE CASCADE,

    -- Per-condition probability distribution
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

CREATE INDEX IF NOT EXISTS idx_aggregation_results_intake_id
    ON public.aggregation_results(intake_id);

CREATE INDEX IF NOT EXISTS idx_aggregation_results_created_at
    ON public.aggregation_results(created_at DESC);


-- ============================================================================
-- 14. WORKFLOW LOGS
-- Domain Owner: Workflow
-- Type: Historical (append-only audit log — NEVER queried for current state)
-- SSOT for patient status per ADR-001
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.workflow_logs (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    intake_id   UUID        REFERENCES public.emergency_intake(id) ON DELETE CASCADE,
    old_status  TEXT,
    new_status  TEXT        NOT NULL,
    actor_type  TEXT        NOT NULL CHECK (actor_type IN ('System', 'Nurse', 'Doctor')),
    actor_name  TEXT        NOT NULL,
    reason      TEXT,
    changed_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_logs_intake_id
    ON public.workflow_logs(intake_id);

CREATE INDEX IF NOT EXISTS idx_workflow_logs_changed_at
    ON public.workflow_logs(changed_at DESC);


-- ============================================================================
-- ROW LEVEL SECURITY
-- All tables: RLS enabled, service_role has full access
-- ============================================================================

ALTER TABLE public.patients                       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.emergency_intake               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vitals                         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.symptoms                       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.nlp_extractions                ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.risk_scores                    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.preparation_alerts             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investigation_recommendations  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pipeline_status                ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence                       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lab_results                    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.imaging_results                ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.aggregation_results            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workflow_logs                  ENABLE ROW LEVEL SECURITY;


-- Service-role full access policies
DROP POLICY IF EXISTS "service_role_all" ON public.patients;
CREATE POLICY "service_role_all" ON public.patients FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.emergency_intake;
CREATE POLICY "service_role_all" ON public.emergency_intake FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.vitals;
CREATE POLICY "service_role_all" ON public.vitals FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.symptoms;
CREATE POLICY "service_role_all" ON public.symptoms FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.nlp_extractions;
CREATE POLICY "service_role_all" ON public.nlp_extractions FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.risk_scores;
CREATE POLICY "service_role_all" ON public.risk_scores FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.preparation_alerts;
CREATE POLICY "service_role_all" ON public.preparation_alerts FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.investigation_recommendations;
CREATE POLICY "service_role_all" ON public.investigation_recommendations FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.pipeline_status;
CREATE POLICY "service_role_all" ON public.pipeline_status FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.evidence;
CREATE POLICY "service_role_all" ON public.evidence FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.lab_results;
CREATE POLICY "service_role_all" ON public.lab_results FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.imaging_results;
CREATE POLICY "service_role_all" ON public.imaging_results FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.aggregation_results;
CREATE POLICY "service_role_all" ON public.aggregation_results FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all" ON public.workflow_logs;
CREATE POLICY "service_role_all" ON public.workflow_logs FOR ALL USING (true) WITH CHECK (true);


-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
-- Total: 14 tables, 14 RLS policies, 9 indexes
-- Domain coverage:
--   Patient:        patients
--   Triage:         emergency_intake, vitals, symptoms
--   AI:             nlp_extractions, risk_scores, lab_results, imaging_results, aggregation_results
--   Investigation:  investigation_recommendations
--   Evidence:       evidence
--   Pipeline:       pipeline_status
--   Notification:   preparation_alerts
--   Workflow:       workflow_logs (historical/audit only)
-- ============================================================================
