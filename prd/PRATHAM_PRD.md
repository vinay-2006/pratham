# PRATHAM — Product Requirements Document

**Version:** 1.0  
**Date:** 2026-08-15  
**Classification:** Internal / Engineering / Product  
**Source of Truth:** Reverse-engineered from repository at `d:\pratham` (commit a0096a8)  
**System Version:** v5.0.0  

---

## 1. Executive Summary

**PRATHAM** (Predictive Risk Assessment & Triage for Healthcare AI Management) is an **Emergency Clinical Intelligence Platform** that helps emergency department teams organize fragmented patient information, extract clinically relevant signals from heterogeneous evidence, assess operational risk, coordinate investigations, and provide explainable clinical intelligence to authorized clinicians.

### The Problem

In emergency departments, critical patient information arrives fragmented — across verbal handoffs, paper forms, imaging studies, lab results, and clinical observations. Clinicians must mentally synthesize this information under time pressure, often missing correlations between symptoms, vitals, labs, and imaging. There is no unified system that aggregates this evidence, computes operational risk, recommends appropriate investigations, and presents explainable intelligence to the attending physician.

### The Solution

PRATHAM provides an end-to-end pipeline from patient arrival to clinical intelligence:

1. **Intake & Triage** — Nurses register patients with demographics, vitals, symptoms, and free-text emergency descriptions, including in-transit (ambulance) scenarios.
2. **Automated Clinical Intelligence** — The system runs NLP extraction (via Groq/LLaMA), rule-based operational risk scoring, investigation recommendations, lab analysis (XGBoost cardiac risk), and imaging analysis (EfficientNetB0 pneumonia detection).
3. **Doctor Review & Approval** — Physicians review recommended investigations, approve/reject them, and review aggregated clinical intelligence reports with full explainability.
4. **Evidence Aggregation** — A deterministic 7-step heuristic pipeline synthesizes all evidence sources into condition probabilities with confidence suppression when evidence is insufficient.
5. **Clinical Report & Explainability** — A two-layer clinical reasoning engine produces fully auditable conclusions, supported by a grounded LLM narrative and an interactive explainability tree.

### Key Differentiators

| Dimension | PRATHAM Approach |
|---|---|
| **Clinical Safety** | Deterministic reasoning; LLM generates narrative only, never computes clinical values |
| **Explainability** | Every AI output traces to evidence sources with supporting/conflicting/missing evidence matrices |
| **Confidence Suppression** | Dual-gate suppression withholds conclusions when evidence is genuinely insufficient |
| **Human-in-the-Loop** | Doctors approve all investigations; system recommends but never prescribes |
| **Architecture** | 7-layer separation isolates clinical calculations from generative synthesis |

### Current Maturity

PRATHAM is a **functional prototype** with a complete end-to-end pipeline, 14 database tables, 21+ API routes, 2 trained ML models, and a full React frontend. It is **not production-deployed** in any hospital setting and has not undergone regulatory review.

### Technology Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python), Pydantic |
| Frontend | React, TanStack Router, TanStack Query, Tailwind CSS, shadcn/ui |
| Database | PostgreSQL via Supabase (14 tables, RLS enabled) |
| ML Models | XGBoost (cardiac risk), TensorFlow/EfficientNetB0 (pneumonia) |
| NLP | Groq API (LLaMA 3.3-70B) with deterministic fallback |
| LLM Narrative | Groq API with rule-based fallback |
| Storage | Supabase Storage (evidence files) |
| Deployment | Docker Compose, Cloudflare Workers (frontend) |

---

## 2. Product Definition

### One Sentence
PRATHAM is an emergency clinical intelligence platform that aggregates patient evidence, computes operational risk, recommends investigations, and presents explainable AI-driven clinical intelligence to authorized emergency care teams.

### 25 Words
PRATHAM organizes emergency patient data through automated NLP extraction, risk scoring, investigation recommendations, and evidence aggregation to deliver explainable clinical intelligence for emergency physicians.

### 100 Words
PRATHAM is a full-stack emergency clinical intelligence platform that assists emergency department teams from patient arrival through clinical decision-making. Nurses register patients with vitals, symptoms, and free-text descriptions. The system automatically extracts clinical signals using LLM-powered NLP, computes rule-based operational risk scores across four categories (cardiac, respiratory, trauma, neurological), generates investigation recommendations through pathway-specific clinical rules, and orchestrates lab/imaging AI analysis. A deterministic 7-step heuristic aggregation pipeline synthesizes all evidence into condition probabilities with confidence suppression. Doctors review explainable clinical intelligence reports featuring evidence trees, subsystem agreement matrices, and grounded LLM narratives — while retaining full clinical decision authority.

### Executive Description
PRATHAM addresses the fundamental challenge of information fragmentation in emergency medicine. When a patient arrives — via walk-in, ambulance, or referral — critical clinical data is scattered across intake forms, vital sign monitors, free-text notes, lab systems, and imaging modalities. PRATHAM unifies this information through a 5-stage AI pipeline (NLP → Risk → Lab → Imaging → Aggregation), transforming raw clinical inputs into structured, explainable intelligence. The platform preserves absolute clinical authority for physicians while providing actionable risk assessment, investigation recommendations, and evidence-based condition probability distributions.

### Technical Description
PRATHAM implements a layered architecture: **API → Services → Workflow Service → Repositories → PostgreSQL/Supabase**. The clinical intelligence pipeline consists of 5 stages tracked by a pipeline state machine (pending → running → completed / failed). Each stage is independently retriable. The aggregation engine uses deterministic heuristic scoring with dual-gate confidence suppression (minimum 2 data sources + minimum 3.0 max condition score). A two-layer clinical reasoning service separates facts (Layer 1) from conclusions (Layer 2), ensuring the LLM only generates narrative text and never computes clinical values. The system uses validated clinical scoring calculators (NEWS2, qSOFA, CURB-65, HEART, Wells PE) and a 13-condition YAML knowledge base for evidence ranking.

### Clinical-Workflow Description
A nurse registers a patient at the triage desk or en route by ambulance, entering demographics, vital signs, symptoms, and a free-text emergency description. The system automatically triggers NLP extraction, risk scoring, and investigation recommendations. The case transitions to "Awaiting Doctor Approval." A physician reviews the recommended investigations, approves or rejects them, and may add custom tests. Once evidence (X-rays, lab reports) is uploaded and analyzed, the system aggregates all findings into a clinical intelligence report. The doctor reviews the report, which includes condition probabilities, evidence trees, clinical scores, monitoring priorities, and precautions — all with full provenance tracing.

### Product Category
**Emergency Clinical Intelligence Platform** — combining clinical evidence aggregation, operational risk assessment, investigation coordination, and explainable AI-driven clinical decision support.

---

## 3. Vision

> Enable emergency care teams to make faster, better-informed clinical decisions by automatically organizing fragmented patient evidence into structured, explainable clinical intelligence — while ensuring that human clinicians remain the sole decision-makers.

### Long-Term Vision
Evolve PRATHAM into a **plugin-extensible clinical intelligence platform** where new analysis modules (e.g., sepsis detection, toxicology screening) can be added without restructuring the core pipeline, serving multiple hospital systems with interoperable standards.

---

## 4. Problem Statement

### Problems PRATHAM Currently Solves — `CURRENT`

| Problem | How PRATHAM Addresses It |
|---|---|
| **Fragmented emergency patient data** | Unified intake captures demographics, vitals, symptoms, free text, and evidence in a single workflow |
| **Manual clinical signal extraction** | Automated NLP extracts structured risk flags (cardiac, respiratory, neurological, trauma) from free-text descriptions |
| **Delayed risk assessment** | Real-time rule-based risk scoring across 4 categories immediately at intake |
| **Ad-hoc investigation ordering** | Pathway-specific rule engine recommends targeted investigations based on symptoms, vitals, NLP flags, and risk scores |
| **Disconnected evidence interpretation** | Aggregation pipeline synthesizes NLP, risk, lab, and imaging evidence into a unified probability distribution |
| **Lack of clinical explainability** | Evidence trees, subsystem agreement matrices, confidence explanations, and decision path traces accompany every conclusion |
| **No workflow coordination** | 11-state workflow machine tracks patient cases from intake through clinical report to case closure |
| **Information overload** | Structured reports with condition rankings, supporting/conflicting evidence, and clinical scores distill complex data |
| **Equipment/preparation readiness** | Automated preparation alerts (ICU standby, oxygen prep, trauma team, CT scanner, blood bank) triggered by risk thresholds |

### Problems PRATHAM is Intended to Solve in the Future — `FUTURE`

| Problem | Planned Approach |
|---|---|
| **Longitudinal patient intelligence** | Multi-visit trajectory analysis with physiological delta detection (partial implementation exists) |
| **Hospital interoperability** | FHIR/HL7 integration for standards-based data exchange |
| **Real-time vital monitoring** | Continuous data feeds from bedside monitors |
| **Multi-hospital deployment** | Multi-tenant architecture with hospital-specific configurations |
| **Regulatory compliance** | Full audit trails compliant with healthcare data regulations |

---

## 5. Product Goals

### Primary Goals

1. **Reduce time-to-clinical-context** — From patient arrival to a complete risk assessment and investigation recommendation set.
2. **Ensure clinical safety** — Never replace physician judgment; always provide explainability and uncertainty visibility.
3. **Automate evidence aggregation** — Synthesize heterogeneous evidence sources into actionable intelligence without requiring manual correlation.
4. **Enable investigation coordination** — Bridge the gap between nurse evidence collection and doctor investigation approval.
5. **Provide operational preparation intelligence** — Alert hospital teams about resource needs (ICU, equipment, blood bank) based on risk assessment.

### Secondary Goals

6. **Support in-transit triage** — Enable pre-arrival intake for ambulance patients with ETA tracking and auto-arrival transitions.
7. **Maintain architectural evolvability** — Support addition of new intelligence modules without restructuring the core platform.
8. **Enable clinical audit** — Full audit trail of status transitions, evidence provenance, and pipeline execution.

---

## 6. Non-Goals

PRATHAM explicitly **does NOT**:

1. ❌ **Diagnose patients** — PRATHAM computes operational risk probabilities and evidence-based condition rankings, not definitive diagnoses.
2. ❌ **Prescribe treatment** — The system recommends investigations and generates monitoring priorities, never medications or treatment plans.
3. ❌ **Replace clinicians** — All clinical decisions require physician approval. The system is a decision-support tool.
4. ❌ **Process real-time vital streams** — Vitals are entered as point-in-time observations during intake.
5. ❌ **Handle billing or administrative workflows** — No insurance, billing, or administrative module exists.
6. ❌ **Provide patient-facing interfaces** — All interfaces are designed for clinical staff.
7. ❌ **Enforce regulatory compliance** — The system has not been validated against healthcare regulations (HIPAA, GDPR, MDR).
8. ❌ **Operate autonomously** — Every critical pathway requires human oversight and approval.

---

## 7. Target Users

### Nurse — `CURRENT`

**Role:** Emergency triage nurse / intake nurse  
**Status:** Fully supported with dedicated frontend routes

| Responsibility | Implementation |
|---|---|
| Patient registration | Multi-step intake form with demographics, vitals, symptoms, free-text |
| Vitals entry | Validated fields (HR 20-250, SpO₂ 50-100, BP, temp, RR) |
| Symptom entry | 6 boolean symptom flags (chest pain, breathlessness, trauma, bleeding, unconsciousness, neurological) |
| Free-text entry | Emergency description and chief complaint fields |
| Evidence upload | File upload to Supabase Storage (JPEG/PNG/PDF/TXT, ≤10MB) |
| Investigation-evidence mapping | Upload evidence linked to specific approved investigations |
| Patient queue monitoring | Real-time queue with pipeline status, severity badges, workflow progress |
| Patient workspace | Detailed view of individual patient with timeline, vitals, investigations, evidence |
| Pipeline status visibility | Visual pipeline status indicators (pending/running/completed/failed) for all 5 stages |

**Frontend Routes:**
- `/nurse/intake` — Full intake form
- `/nurse/queue` — Patient queue list
- `/nurse/dashboard` — Dashboard overview
- `/nurse/registry` — Patient registry

### Doctor — `CURRENT`

**Role:** Emergency physician / attending doctor  
**Status:** Fully supported with dedicated frontend routes

| Responsibility | Implementation |
|---|---|
| Investigation review | Approve, reject, or request more info on recommended investigations |
| Custom investigation requests | Add investigations not in the system's recommendations |
| Clinical report review | Full clinical intelligence report with 17+ sections |
| Evidence interpretation | View lab results, imaging results, and aggregation outcomes |
| Risk interpretation | Review 4-category risk scores and clinical scoring (NEWS2, qSOFA, etc.) |
| Feedback | Doctor review notes and investigation annotations |
| PDF export | Download clinical reports as structured PDFs |

**Frontend Routes:**
- `/doctor/review` — Investigation approval worklist
- `/doctor/dashboard` — Doctor dashboard
- `/doctor/reports` — Report listing
- `/doctor/report/{intakeId}` — Individual clinical report
- `/doctor/approvals` — Pending approvals

### Administrator — `PARTIAL`

**Status:** Basic telemetry exists but no dedicated admin role/authentication.

| Capability | Implementation |
|---|---|
| Platform metrics | `/api/platform-metrics` endpoint with repository scan data |
| Admin dashboard | Basic admin dashboard component exists |
| System health | `/health`, `/ready`, `/metrics` endpoints |
| Pipeline telemetry | Average latencies per pipeline stage |

### Future Roles — `FUTURE`

- **Technician** — Lab/imaging technician for evidence upload and result entry
- **Hospital Administrator** — Capacity management, resource allocation
- **Clinical Auditor** — Compliance review and audit trail inspection

---

## 8. User Personas

### Persona 1: Triage Nurse Priya

**Context:** Works the evening shift in a busy urban emergency department. Receives 15–25 patients per shift, ranging from walk-ins with minor complaints to ambulance arrivals with multi-system trauma.

**Needs:**
- Register patients quickly without navigating multiple systems
- See at-a-glance which patients need attention
- Upload evidence files and track which investigations are pending
- Know when the AI pipeline has completed analysis

**PRATHAM provides:** A single intake form → automatic risk assessment → investigation recommendations → evidence upload workflow → pipeline status visibility.

### Persona 2: Emergency Physician Dr. Rajan

**Context:** Responsible for clinical decisions for all patients in the ED. Needs to review cases rapidly, understand risk profiles, and order appropriate investigations.

**Needs:**
- See a worklist of patients awaiting review
- Understand the risk profile before seeing the patient
- Approve/reject/modify investigation recommendations efficiently
- Review aggregated evidence with full explainability
- Trust that the system's intelligence is grounded in real evidence

**PRATHAM provides:** Doctor review worklist → investigation approval workflow → clinical intelligence report → explainability trees → clinical scores → evidence provenance.

---

## 9. Current Product Capabilities

### Capability Status Matrix

| Capability | Status | Evidence |
|---|---|---|
| Emergency Intake (Walk-in / Ambulance / Referral) | `CURRENT` | `api/intake.py`, `_app.nurse.intake.tsx` |
| Demographics, Vitals, Symptoms Collection | `CURRENT` | Pydantic models, 3 DB tables |
| Free-text Emergency Description | `CURRENT` | `emergency_description` field in intake |
| NLP Clinical Signal Extraction (Groq/LLaMA) | `CURRENT` | `nlp_service.py`, `nlp_extractions` table |
| NLP Mock/Deterministic Fallback | `CURRENT` | `USE_MOCK_LLM` environment variable |
| Rule-Based Operational Risk Scoring | `CURRENT` | `risk_service.py`, `risk_scores` table |
| Preparation Alerts Generation | `CURRENT` | `generate_preparation_alerts()`, `preparation_alerts` table |
| Investigation Recommendations (Pathway-Based) | `CURRENT` | `investigation_service.py`, 4 pathways + safety net |
| Visit Type Classification (Emergency vs. Routine) | `CURRENT` | `visit_classifier.py` |
| Doctor Investigation Approval/Rejection | `CURRENT` | `investigation_approval_service.py` |
| Evidence Upload (Supabase Storage) | `CURRENT` | `api/evidence.py`, `evidence` table |
| Lab Analysis (XGBoost Cardiac Risk + SHAP) | `CURRENT` | `lab_model.py`, `lab_analysis_service.py`, `lab_results` table |
| Imaging Analysis (EfficientNetB0 Pneumonia) | `CURRENT` | `imaging_model.py`, `imaging_results` table |
| Grad-CAM Heatmap Generation | `CURRENT` | `generate_gradcam()` in `imaging_model.py` |
| Evidence Aggregation (7-Step Heuristic) | `CURRENT` | `aggregation_service.py`, `aggregation_results` table |
| Confidence Suppression (Dual-Gate) | `CURRENT` | MIN_SOURCES_REQUIRED=2, MIN_MAX_SCORE=3.0 |
| Pipeline State Machine (5 stages × 4 states) | `CURRENT` | `pipeline_status_service.py`, `pipeline_status` table |
| 11-State Workflow State Machine | `CURRENT` | `workflow_service.py`, `workflow_logs` table |
| Clinical Reasoning (2-Layer: Facts + Conclusions) | `CURRENT` | `clinical_reasoning_service.py` |
| Clinical Scoring (NEWS2, qSOFA, CURB-65, HEART, Wells) | `CURRENT` | `clinical_scoring_service.py` |
| Clinical Pattern Engine | `CURRENT` | `clinical_pattern_engine.py` |
| Evidence Ranking (13-Condition YAML KB) | `CURRENT` | `evidence_ranking_engine.py`, `knowledge_base/*.yaml` |
| LLM Clinical Interpretation (Groq + Fallback) | `CURRENT` | `interpretation_service.py` |
| Clinical Report (17-Section JSON) | `CURRENT` | `report_service.py` |
| PDF Report Generation | `CURRENT` | `pdf_generator.py` |
| Explainability Trees & Agreement Matrix | `CURRENT` | `explainability_service.py` |
| Clinical Copilot (4-Tier Chat) | `CURRENT` | `copilot/copilot_orchestrator.py`, 13 copilot modules |
| Patient Timeline | `CURRENT` | `build_patient_timeline()` in `workflow_service.py` |
| Patient Queue (Nurse) | `CURRENT` | `patient_queue_service.py` |
| Doctor Review Worklist | `CURRENT` | `doctor_review_service.py` |
| Command Center | `CURRENT` | `command_center_service.py`, `command-center-view.tsx` |
| Clinical Search | `CURRENT` | `clinical_search_service.py` |
| System Atlas / Architecture Explorer | `CURRENT` | `system-atlas/` (Next.js app) |
| Structured Logging | `CURRENT` | `logging_service.py` with JSON telemetry |
| Startup Configuration Validation | `CURRENT` | `config_validator.py` |
| CORS Configuration | `CURRENT` | Multi-origin CORS in `main.py` |
| Global Error Handling | `CURRENT` | Exception handlers in `main.py` |
| Health/Readiness/Metrics Probes | `CURRENT` | `/health`, `/ready`, `/metrics` endpoints |
| Demo Patient Management | `CURRENT` | `api/demo.py`, demo library component |
| Demographic Reference Ranges | `CURRENT` | `reference_range_service.py` |
| Longitudinal Trend Analysis | `PARTIAL` | `trend_analysis_service.py`, `longitudinal_history_service.py` |
| Case Comparison Explorer | `PARTIAL` | `case-comparison-explorer.tsx` |
| Authentication / Authorization | `FUTURE` | No user authentication implemented |
| Role-Based Access Control | `FUTURE` | No RBAC enforcement |
| FHIR/HL7 Interoperability | `FUTURE` | Not implemented |
| Real-Time Vital Monitoring | `FUTURE` | Not implemented |

---

## 10. Product Architecture

### Layered Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     FRONTEND                              │
│  React + TanStack Router + TanStack Query + Tailwind     │
│  Routes: Nurse (intake/queue/dashboard/registry)          │
│          Doctor (review/dashboard/reports/report)          │
│          System (copilot/explainability/command-center)    │
└───────────────────────┬──────────────────────────────────┘
                        │ HTTP / JSON
┌───────────────────────▼──────────────────────────────────┐
│                      API LAYER                            │
│  FastAPI Routers (21 route modules)                       │
│  Request validation · HTTP contracts · Orchestration      │
│  Pydantic models · Error handling · CORS                  │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│                   SERVICE LAYER                           │
│  Business logic · Domain operations · Business rules      │
│  NLP · Risk · Lab Analysis · Imaging Analysis             │
│  Aggregation · Clinical Reasoning · Report · Copilot      │
│  Investigation Approval · Pipeline Status                 │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│                WORKFLOW SERVICE                            │
│  Stateful multi-step workflows                            │
│  11-state machine · Status transitions · Audit logging    │
│  Pipeline coordination · Patient lifecycle                │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│                REPOSITORY LAYER                           │
│  Domains: AI · Evidence · Investigation · Patient ·       │
│           Pipeline · Report · Triage · Workflow            │
│  Persistence · Query encapsulation · DB ownership         │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│             PostgreSQL (Supabase)                          │
│  14 tables · RLS enabled · Service-role policies          │
│  UUID primary keys · Timestamped · Audit trail            │
└──────────────────────────────────────────────────────────┘
```

### Architectural Principles

> **One responsibility → one owner → one location.**

| Principle | Implementation |
|---|---|
| API layer handles HTTP only | API routers validate, route, return HTTP responses; no business logic |
| Services own business logic | All calculations, rules, and orchestration live in services |
| Workflow service owns state transitions | All status changes go through `workflow_service.py` |
| Repositories own persistence | All database access is encapsulated in domain repositories |
| Pipeline service owns pipeline state | All pipeline status updates go through `pipeline_status_service.py` |

### Domain Ownership Map

| Domain | Repository | Tables |
|---|---|---|
| Patient | `triage/repository.py` | `patients`, `emergency_intake`, `vitals`, `symptoms` |
| AI | `ai/repository.py` | `nlp_extractions`, `risk_scores`, `lab_results`, `imaging_results`, `aggregation_results` |
| Investigation | `investigation/repository.py` | `investigation_recommendations` |
| Evidence | `evidence/repository.py` | `evidence` |
| Pipeline | `pipeline/repository.py` | `pipeline_status` |
| Notification | `triage/repository.py` | `preparation_alerts` |
| Workflow | `workflow/repository.py` | `workflow_logs` |

---

## 11. End-to-End Clinical Workflow

### Patient Journey (Verified from Code)

```
Patient Arrival
     │
     ├─ Walk-in ──→ Status: arrived → awaiting_doctor_approval
     ├─ Ambulance ─→ Status: en_route → [ETA elapsed] → arrived → awaiting_doctor_approval
     └─ Referral ──→ Status: intake_submitted → [manual] → awaiting_doctor_approval
     │
     ▼
┌─ INTAKE (Synchronous, POST /api/intake) ─────────────────────┐
│  1. Create Patient record                                      │
│  2. Create Emergency Intake (with case_id PRA-2026-XXXXXX)     │
│  3. Insert Vitals                                              │
│  4. Insert Symptoms                                            │
│  5. Initialize Pipeline (5 stages × pending)                   │
│  6. NLP Extraction → nlp_extractions (async-tolerant)          │
│  7. Risk Scoring → risk_scores                                 │
│  8. Preparation Alerts → preparation_alerts                    │
│  9. Investigation Recommendations → investigation_recommendations│
│  Rollback: compensating deletion on any step failure            │
└───────────────┬──────────────────────────────────────────────────┘
                │
                ▼
    Doctor Reviews Investigations
    (Status: awaiting_doctor_approval)
                │
     ┌──────────┼──────────┐
     ▼          ▼          ▼
  Approve    Reject    Needs Info
     │                     │
     ▼                     ▼
  Status: investigations_approved    Status: needs_info
     │
     ▼
  Nurse Uploads Evidence
  (Status: evidence_upload_pending → analysis_running)
     │
     ├── Lab Report → POST /api/lab-analysis/{intake_id}
     │   XGBoost inference → lab_results (+ SHAP values)
     │
     ├── X-ray → POST /api/imaging-analysis/{intake_id}
     │   EfficientNetB0 inference → imaging_results (+ Grad-CAM)
     │
     ▼
  Evidence Aggregation
  (POST /api/aggregation/{intake_id})
  7-step heuristic pipeline → aggregation_results
     │
     ▼
  Status: clinical_report_ready
     │
     ▼
  Doctor Reviews Report
  (GET /api/report/{intake_id})
  17-section clinical intelligence report
     │
     ▼
  Status: under_doctor_review → case_closed
```

### Processing Model

| Operation | Type | Failure Handling |
|---|---|---|
| Intake creation | Synchronous | Compensating rollback |
| NLP extraction | Synchronous (graceful degradation) | Fallback to symptom-derived flags; pipeline marked failed |
| Risk scoring | Synchronous | Pipeline marked failed; exception re-raised |
| Investigation recommendations | Synchronous | Part of intake transaction |
| Lab analysis | On-demand (doctor triggers) | Pipeline marked failed; HTTP 500 |
| Imaging analysis | On-demand (nurse uploads evidence) | Pipeline marked failed; HTTP 500 |
| Aggregation | On-demand | Pipeline marked failed; HTTP 500 |
| Report generation | On-demand (async DB fetches) | Partial data displayed |

---

## 12. Nurse Workflow

### Journey: Patient Arrival → Evidence Submission

| Step | User Action | System Response | State Change | UI Surface |
|---|---|---|---|---|
| 1 | Nurse opens intake form | Form renders with demographics, vitals, symptoms sections | — | `/nurse/intake` |
| 2 | Nurse enters patient data | Client-side validation (vitals ranges, required fields) | — | Intake form |
| 3 | Nurse submits intake | POST /api/intake triggers full pipeline | `intake_submitted → arrived → awaiting_doctor_approval` (walk-in) | Toast notification |
| 4 | Nurse monitors queue | GET /api/investigations/queue returns all active cases | — | `/nurse/queue` |
| 5 | Nurse sees doctor approved investigations | Investigation status changes visible in queue | `investigations_approved` | Queue item |
| 6 | Nurse uploads evidence | POST /api/evidence/upload → Supabase Storage | `evidence_upload_pending` or `analysis_running` | Evidence upload row |
| 7 | Nurse monitors pipeline | Pipeline status polling shows stage completion | Per-stage transitions | Pipeline status pills |
| 8 | Report ready notification | Pipeline completion triggers status change | `clinical_report_ready` | Status badge update |

---

## 13. Doctor Workflow

### Journey: Patient Selection → Clinical Decision

| Step | User Action | System Response | State Change | UI Surface |
|---|---|---|---|---|
| 1 | Doctor opens review | GET doctor review list | — | `/doctor/review` |
| 2 | Doctor selects patient | Recommended investigations loaded | — | Investigation review panel |
| 3 | Doctor approves/rejects tests | POST approve/reject/needs-info mutations | `investigations_approved` | Approval buttons |
| 4 | Doctor adds custom tests | POST add investigation | Investigation created | Add test form |
| 5 | Doctor opens report | GET /api/report/{intakeId} | `under_doctor_review` | `/doctor/report/{intakeId}` |
| 6 | Doctor reviews clinical intelligence | Full 17-section report renders | — | Clinical report page |
| 7 | Doctor explores explainability | Explainability tree, agreement matrix, decision path | — | Explainability explorer |
| 8 | Doctor exports PDF | GET /api/report/{intakeId}/pdf | — | PDF download |
| 9 | Doctor closes case | Status transition to case_closed | `case_closed` | Status controls |

---

## 14. Evidence Lifecycle

### Evidence Types (Verified from DB schema)

| Type | Description | AI Analysis |
|---|---|---|
| `xray` | Chest X-ray images | EfficientNetB0 pneumonia classification + Grad-CAM |
| `lab_report` | Laboratory reports | XGBoost cardiac risk prediction + SHAP |
| `ecg` | Electrocardiogram | No automated analysis — `FUTURE` |
| `clinical_notes` | Free-text clinical notes | No automated analysis — `FUTURE` |
| `ct_scan` | CT scan images | No automated analysis — `FUTURE` |
| `mri` | MRI images | No automated analysis — `FUTURE` |
| `blood_work` | Blood work results | No automated analysis — `FUTURE` |
| `ultrasound` | Ultrasound images | No automated analysis — `FUTURE` |

### Evidence Flow

```
Nurse uploads file
     │
     ▼
Supabase Storage (private bucket "evidence")
     │  ← 7-day signed URL generated
     ▼
evidence table (intake_id, investigation_id, file metadata)
     │
     ▼
Workflow status update (upload_pending → analysis_running)
     │
     ├── If xray → imaging_analysis → imaging_results
     ├── If lab_report → lab_analysis → lab_results
     └── Other types → stored but not auto-analyzed
     │
     ▼
Downstream: aggregation uses latest lab/imaging results
```

### Evidence Deletion Effects

When evidence is deleted:
1. Related `lab_results` or `imaging_results` rows are deleted
2. `aggregation_results` for the intake are deleted
3. Pipeline stages (`lab`, `imaging`, `aggregation`) are reset to `pending`
4. Workflow status may be reset to `evidence_upload_pending`

---

## 15. Clinical Intelligence Pipeline

### Pipeline Architecture (5 Stages)

```
Stage 1: NLP      ─→ Clinical signal extraction from free text
Stage 2: Risk     ─→ Rule-based operational risk scoring
Stage 3: Lab      ─→ XGBoost cardiac risk prediction
Stage 4: Imaging  ─→ EfficientNetB0 pneumonia classification
Stage 5: Aggregation ─→ Heuristic evidence synthesis
```

### Pipeline Execution Model

- **Stages 1-2** (NLP, Risk): Execute **synchronously during intake** as part of POST /api/intake
- **Stages 3-4** (Lab, Imaging): Execute **on-demand** when nurse uploads evidence and triggers analysis
- **Stage 5** (Aggregation): Execute **on-demand** when requested via POST /api/aggregation/{intake_id}
- All stages are tracked via `pipeline_status` table
- Failed stages can be retried (failed → running transition is allowed)
- `attempt_count` preserves retry history

---

## 16. NLP Intelligence

### Implementation: `nlp_service.py`

| Attribute | Value |
|---|---|
| **Model** | LLaMA 3.3-70B Versatile (via Groq API) |
| **Framework** | Groq Python SDK |
| **Input** | Emergency description + symptoms dict + vitals dict |
| **Output** | 7 boolean flags + extracted keywords + clinical summary |
| **Temperature** | 0.1 (near-deterministic) |
| **Timeout** | 8 seconds |
| **Fallback** | Deterministic derivation from symptom booleans |
| **Mock Mode** | `USE_MOCK_LLM=true` → pure deterministic extraction |
| **Persistence** | `nlp_extractions` table |

### Extracted Flags

| Flag | Description |
|---|---|
| `head_trauma` | Head injury detected |
| `loss_of_consciousness` | LOC indicated |
| `neurological_risk_flag` | Neurological risk present |
| `respiratory_distress` | Breathing difficulty detected |
| `cardiac_risk_flag` | Cardiac risk indicated |
| `trauma_present` | Physical trauma detected |
| `hemorrhage_risk` | Bleeding/hemorrhage risk |

### Failure Behavior

1. Groq API call fails → **Non-fatal**: system falls back to symptom-derived flags
2. JSON parsing fails → **Non-fatal**: falls back to symptom-derived flags
3. Pipeline stage marked `failed` but intake continues
4. NLP failure does NOT block risk scoring or investigation recommendations

> **Clinical Safety Note:** NLP extraction uses graceful degradation. The system never halts patient care because of an NLP failure.

---

## 17. Risk Intelligence

### Implementation: `risk_service.py`

| Attribute | Value |
|---|---|
| **Type** | Deterministic rule-based weighted scoring |
| **Framework** | Pure Python (no ML/LLM) |
| **Input** | Vitals dict + symptoms dict + NLP flags dict |
| **Output** | 4 risk scores (0-100) + overall severity |

### Scoring Rules (Verified)

**Cardiac Risk** (max 100):
- Chest pain: +30
- Cardiac risk flag (NLP): +20
- Heart rate >120: +20, >100: +10
- BP systolic >160: +15, >140: +8
- BP systolic <90: +25

**Respiratory Risk** (max 100):
- Breathlessness: +25
- Respiratory distress (NLP): +20
- SpO₂ <90: +30, <94: +15
- Respiratory rate >25: +15, >20: +8

**Trauma Risk** (max 100):
- Trauma: +35
- Bleeding: +25
- Trauma present (NLP): +20
- Hemorrhage risk (NLP): +20

**Neurological Risk** (max 100):
- Unconsciousness: +40
- Neurological symptoms: +25
- Head trauma (NLP): +20
- LOC (NLP): +20
- Neurological risk flag (NLP): +15

### Overall Severity

| Max Score | Severity |
|---|---|
| ≥70 | `critical` |
| ≥50 | `high` |
| ≥30 | `moderate` |
| <30 | `low` |

### Preparation Alerts

| Condition | Alert |
|---|---|
| Cardiac risk ≥50 | `icu_standby` |
| Respiratory risk ≥40 | `oxygen_prep` |
| Trauma risk ≥40 | `trauma_team` |
| Neurological ≥50 OR Trauma ≥50 | `ct_scanner` |
| Severity high/critical | `emergency_bed` |
| Trauma risk ≥60 | `blood_bank` |

> **Critical Distinction:** These are **operational risk scores**, not clinical diagnoses. They quantify the *urgency and resource requirements* of the emergency case.

---

## 18. Investigation Intelligence

### Implementation: `investigation_service.py`

| Attribute | Value |
|---|---|
| **Type** | Rule-based pathway-specific recommendation engine |
| **Input** | Symptoms + vitals + NLP flags + risk scores |
| **Output** | Sorted list of investigation names |
| **Design** | No "universal" tests; each pathway has strict symptom gates |

### Pathways (Verified)

**Cardiac Pathway** — Gates: `chest_pain` OR `cardiac_risk_flag`
- Always: ECG, Troponin, CBC
- If cardiac_risk ≥60: + Echocardiogram, Cardiac Enzymes

**Respiratory Pathway** — Gates: `breathlessness` OR SpO₂ <94
- Always: Chest X-ray
- If SpO₂ <90: + ABG
- If respiratory_risk ≥70: + CT Chest, D-Dimer

**Trauma Pathway** — Gates: `trauma` OR `bleeding`
- Always: CBC, Coagulation Profile, Blood Group & Cross-match
- If trauma_risk ≥60: + FAST Ultrasound

**Neurological Pathway** — Gates: `unconsciousness` OR `neurological_symptoms`
- Always: CT Brain, Blood Glucose, Electrolytes
- If head_trauma (NLP): + CT Cervical Spine

**Minimum Safety Net** — Only fires if NO pathway triggered AND severity is `critical` AND vitals are present:
- CBC, Blood Glucose, ECG

### Investigation Approval Workflow

Doctors can:
1. **Approve** selected investigations → status: `approved`
2. **Reject** investigations → status: `rejected`
3. **Request more info** → status: `needs_info`
4. **Add custom** investigations not in the recommendation set
5. **Recommend** additional investigations

> **Principle:** PRATHAM recommends and organizes clinical investigations; authorized clinicians remain responsible for all clinical decisions.

---

## 19. Laboratory Workflow

### XGBoost Cardiac Risk Model

| Attribute | Value |
|---|---|
| **Model** | `task9_xgboost_heart_model.json` (XGBClassifier) |
| **Dataset** | UCI Heart Disease dataset |
| **Features** | 15 (Age, RestingBP, Cholesterol, FastingBS, MaxHR, Oldpeak, + one-hot encoded categoricals) |
| **Output** | Binary: `high_risk` (probability ≥0.5) / `low_risk` |
| **Explainability** | SHAP TreeExplainer (top-5 feature contributions) |
| **Persistence** | `lab_results` table (prediction, risk_probability, shap_values, input_features) |

### Max Heart Rate Handling — Clinical Safety

The `max_hr` feature refers to **maximum heart rate achieved during exercise stress testing** (UCI dataset definition). PRATHAM resolves this via a fallback chain:

1. Clinician-provided override (most accurate)
2. Resting heart rate from vitals (proxy fallback)
3. Default: 100 bpm

> **Clinical Safety Note:** Using resting HR as a proxy for exercise max HR is a known limitation documented in the code. The lab analysis service explicitly comments on this: "NOTE: this is a resting HR proxy; it was the original fallback."

---

## 20. Imaging Workflow

### EfficientNetB0 Pneumonia Model

| Attribute | Value |
|---|---|
| **Model** | `task10_efficientnetb0_pneumonia.keras` (19MB) |
| **Architecture** | EfficientNetB0 with built-in preprocessing layers |
| **Input** | 224×224 chest X-ray image (raw pixels — no manual normalization) |
| **Output** | Binary: `pneumonia` (probability ≥0.5) / `normal` |
| **Confidence** | max(probability, 1-probability) |
| **Grad-CAM** | TensorFlow GradientTape on last Conv2D layer → heatmap overlay |
| **Persistence** | `imaging_results` table (prediction, pneumonia_probability, confidence, gradcam_url) |

### Imaging Pipeline

1. Evidence uploaded to Supabase Storage
2. Image downloaded to temp directory
3. EfficientNetB0 inference runs
4. Grad-CAM heatmap generated (if cv2 available)
5. Grad-CAM overlay uploaded to Supabase Storage
6. Results persisted to `imaging_results`
7. Pipeline stage marked completed

---

## 21. Aggregation Workflow

### 7-Step Heuristic Pipeline

| Step | Description |
|---|---|
| 1 | **Verify** intake exists |
| 2 | **Gather** evidence (NLP, risk, lab, imaging) — each source is optional |
| 3 | **Score** — deterministic heuristic weight table across 5 conditions |
| 4 | **Suppress** — dual-gate confidence check |
| 5 | **Normalize** — linear normalization to probability distribution summing to 1.0 |
| 6 | **Persist** — insert into `aggregation_results` with full audit payload |
| 7 | Return structured result |

### Conditions Scored

| Condition | Key |
|---|---|
| Acute Coronary Syndrome | `ACS` |
| Pulmonary Embolism | `PE` |
| Pneumonia | `Pneumonia` |
| Arrhythmia | `Arrhythmia` |
| Other / Non-specific | `Other` |

### Evidence Weight Table (Partial — Verified from Code)

| Source | Signal | ACS | PE | Pneumonia | Arrhythmia |
|---|---|---|---|---|---|
| NLP: chest_pain | +3.0 | +1.0 | — | — |
| NLP: breathlessness | +1.0 | +3.0 | +2.0 | — |
| NLP: palpitations | — | — | — | +3.0 |
| Risk: cardiac ≥50 | +4.0 | — | — | — |
| Risk: respiratory ≥50 | — | +3.0 | +4.0 | — |
| Lab: high_risk | +prob×5.0 | — | — | — |
| Imaging: pneumonia | — | — | +prob×5.0 | — |

### Confidence Suppression (Dual-Gate)

| Gate | Threshold | Effect |
|---|---|---|
| Source count | <2 subsystems available | Probabilities suppressed (set to null) |
| Signal strength | max(scores) <3.0 | Probabilities suppressed (set to null) |

> **Design Constraint:** NO LLM calls. NO ML model inference. All aggregation logic is deterministic and fully explainable via the `evidence_breakdown_json` audit trail.

---

## 22. Pipeline State Machine

### State Transitions (per stage)

```
pending ──→ running ──→ completed
                    ──→ failed ──→ running (retry)
```

### Pipeline Status Table Schema

| Column | Type | Description |
|---|---|---|
| `intake_id` | UUID FK | Links to emergency_intake |
| `stage` | TEXT | `nlp` / `risk` / `lab` / `imaging` / `aggregation` |
| `status` | TEXT | `pending` / `running` / `completed` / `failed` |
| `started_at` | TIMESTAMPTZ | When stage began execution |
| `completed_at` | TIMESTAMPTZ | When stage finished |
| `duration_ms` | INTEGER | Auto-computed execution time |
| `error_message` | TEXT | Stored on failure |
| `attempt_count` | INTEGER | Preserves retry history (never reset) |

### Key Behaviors

| Behavior | Implementation |
|---|---|
| Initialization | 5 rows inserted (all `pending`) immediately after intake creation |
| Mark running | Sets `started_at`, increments `attempt_count`, clears previous error |
| Mark completed | Computes `duration_ms` from `started_at`; auto-transitions workflow to `analysis_running` |
| Mark failed | Stores `error_message`, then **re-raises** the original exception |
| Reset stage | On evidence deletion — resets to `pending`, preserves `attempt_count` |
| Aggregation completion | Auto-transitions workflow to `clinical_report_ready` |
| Batch status | Efficient batch query for queue display |

---

## 23. Product Modules

### Module 1: Patient Management

| Attribute | Value |
|---|---|
| **Purpose** | Register and manage patient demographics |
| **User** | Nurse |
| **Status** | `CURRENT` |
| **DB Entity** | `patients` |
| **API** | POST /api/intake (creates patient as part of intake) |

### Module 2: Emergency Intake

| Attribute | Value |
|---|---|
| **Purpose** | Full emergency patient registration with vitals, symptoms, free-text |
| **User** | Nurse |
| **Status** | `CURRENT` |
| **DB Entities** | `emergency_intake`, `vitals`, `symptoms` |
| **API** | POST /api/intake, GET /api/intake/{id} |
| **AI Components** | Triggers NLP → Risk → Investigation recommendations |
| **UI** | `_app.nurse.intake.tsx` (multi-step form) |

### Module 3: Clinical NLP Extraction

| Attribute | Value |
|---|---|
| **Purpose** | Extract structured clinical risk flags from free-text |
| **User** | System (automated) |
| **Status** | `CURRENT` |
| **DB Entity** | `nlp_extractions` |
| **API** | POST /nlp/extract (also triggered inline during intake) |
| **AI Component** | Groq/LLaMA 3.3-70B with deterministic fallback |

### Module 4: Operational Risk Engine

| Attribute | Value |
|---|---|
| **Purpose** | Compute 4-category operational risk scores |
| **User** | System (automated) |
| **Status** | `CURRENT` |
| **DB Entity** | `risk_scores` |
| **API** | POST /risk/calculate (also triggered inline during intake) |
| **AI Component** | Deterministic rule-based (no ML/LLM) |

### Module 5: Investigation Recommendation Engine

| Attribute | Value |
|---|---|
| **Purpose** | Recommend targeted investigations based on clinical evidence |
| **User** | System → Doctor review |
| **Status** | `CURRENT` |
| **DB Entity** | `investigation_recommendations` |
| **AI Component** | Rule-based pathway engine |

### Module 6: Doctor Investigation Approval

| Attribute | Value |
|---|---|
| **Purpose** | Enable doctors to approve/reject/modify investigation recommendations |
| **User** | Doctor |
| **Status** | `CURRENT` |
| **API** | POST /api/investigations/approve, reject, needs-info, add |
| **UI** | `_app.doctor.review.tsx` |

### Module 7: Evidence Management

| Attribute | Value |
|---|---|
| **Purpose** | Upload, store, and link clinical evidence files |
| **User** | Nurse |
| **Status** | `CURRENT` |
| **DB Entity** | `evidence` |
| **API** | POST /api/evidence/upload, GET /api/evidence/{intake_id}, DELETE |
| **Storage** | Supabase Storage (private bucket) |

### Module 8: Lab Analysis (XGBoost)

| Attribute | Value |
|---|---|
| **Purpose** | Cardiac risk prediction from clinical features |
| **User** | System (triggered by nurse/doctor) |
| **Status** | `CURRENT` |
| **DB Entity** | `lab_results` |
| **API** | POST /api/lab-analysis/{intake_id} |
| **AI Component** | XGBoost + SHAP TreeExplainer |

### Module 9: Imaging Analysis (EfficientNetB0)

| Attribute | Value |
|---|---|
| **Purpose** | Pneumonia classification from chest X-rays |
| **User** | System (triggered by evidence upload) |
| **Status** | `CURRENT` |
| **DB Entity** | `imaging_results` |
| **API** | POST /api/imaging-analysis/{intake_id} |
| **AI Component** | TensorFlow EfficientNetB0 + Grad-CAM |

### Module 10: Evidence Aggregation

| Attribute | Value |
|---|---|
| **Purpose** | Synthesize all evidence sources into condition probabilities |
| **User** | System (on-demand) |
| **Status** | `CURRENT` |
| **DB Entity** | `aggregation_results` |
| **API** | POST /api/aggregation/{intake_id} |
| **AI Component** | Deterministic heuristic scoring (no ML/LLM) |

### Module 11: Clinical Report

| Attribute | Value |
|---|---|
| **Purpose** | Generate comprehensive clinical intelligence reports |
| **User** | Doctor |
| **Status** | `CURRENT` |
| **API** | GET /api/report/{intake_id}, GET /api/report/{intake_id}/pdf |
| **Components** | Clinical reasoning (2-layer) + LLM interpretation + clinical scores |
| **UI** | `_app.doctor.report.$intakeId.tsx`, `clinical-report.tsx` |

### Module 12: Clinical Copilot

| Attribute | Value |
|---|---|
| **Purpose** | Conversational Q&A over clinical evidence and system state |
| **User** | Doctor |
| **Status** | `CURRENT` |
| **API** | POST /api/copilot/query |
| **Components** | 4-tier pipeline: Intent Router → Execution Planner → Context Retrieval → Tool Registry |
| **UI** | `copilot-assistant-drawer.tsx` |

### Module 13: Explainability Explorer

| Attribute | Value |
|---|---|
| **Purpose** | Interactive evidence tree, agreement matrix, and decision path |
| **User** | Doctor |
| **Status** | `CURRENT` |
| **API** | GET /api/explainability/{intake_id} |
| **UI** | `explainability-explorer.tsx` |

### Module 14: Command Center

| Attribute | Value |
|---|---|
| **Purpose** | ED-wide operational view of active cases |
| **User** | Doctor / Nurse |
| **Status** | `CURRENT` |
| **API** | GET /api/command-center |
| **UI** | `command-center-view.tsx` |

### Module 15: System Atlas

| Attribute | Value |
|---|---|
| **Purpose** | Interactive architecture visualization |
| **User** | Developer / Recruiter |
| **Status** | `CURRENT` |
| **Implementation** | Separate Next.js application in `system-atlas/` |

---

## 24. Functional Requirements

### Patient Management

#### PRATHAM-FR-001: Emergency Intake Creation

| Field | Value |
|---|---|
| **Requirement** | The system must accept a complete emergency intake payload containing patient demographics, vitals, symptoms, arrival type, and emergency description, and persist all data atomically. |
| **Actor** | Nurse |
| **Preconditions** | At least `heart_rate` and `spo2` must be provided in vitals |
| **Main Flow** | 1. Validate input (Pydantic) → 2. Create patient → 3. Create intake (with generated case_id) → 4. Insert vitals → 5. Insert symptoms → 6. Initialize pipeline → 7. Run NLP → 8. Run risk scoring → 9. Generate alerts → 10. Recommend investigations → 11. Return enriched response |
| **Failure Conditions** | Any step failure triggers compensating rollback of all previously created records |
| **Acceptance Criteria** | Given a valid intake payload, when submitted, then a patient, intake, vitals, symptoms, 5 pipeline rows, NLP extraction, risk scores, and investigation recommendations must all be created |
| **Priority** | P0 |
| **Status** | `CURRENT` |

#### PRATHAM-FR-002: Arrival Type Handling

| Field | Value |
|---|---|
| **Requirement** | The system must set the initial workflow status based on arrival type: walk_in → arrived, ambulance → en_route, referral → intake_submitted |
| **Actor** | System |
| **Acceptance Criteria** | Given a walk-in patient, initial status is `arrived` and auto-transitions to `awaiting_doctor_approval`. Given an ambulance patient, initial status is `en_route` |
| **Priority** | P0 |
| **Status** | `CURRENT` |

#### PRATHAM-FR-003: Ambulance ETA Auto-Arrival

| Field | Value |
|---|---|
| **Requirement** | When ETA time elapses for an en_route patient, the system must automatically transition status to arrived → awaiting_doctor_approval |
| **Actor** | System (Automated ETA Engine) |
| **Acceptance Criteria** | Given an en_route patient with ETA=15 minutes, when 15 minutes have elapsed, then status must be awaiting_doctor_approval |
| **Priority** | P1 |
| **Status** | `CURRENT` |

#### PRATHAM-FR-004: 48-Hour Automatic Cleanup

| Field | Value |
|---|---|
| **Requirement** | Active cases exceeding 48 hours must be automatically transitioned to offline_care |
| **Actor** | System (Automated Cleanup Engine) |
| **Acceptance Criteria** | Given an active case older than 48 hours, when lifecycle check runs, then status must be offline_care. Cases in report_ready, under_doctor_review, or case_closed are excluded. |
| **Priority** | P2 |
| **Status** | `CURRENT` |

### NLP

#### PRATHAM-FR-005: Clinical Signal Extraction

| Field | Value |
|---|---|
| **Requirement** | The system must extract 7 structured clinical risk flags from emergency description text using LLM |
| **Actor** | System |
| **Acceptance Criteria** | Given an emergency description containing "chest pain and difficulty breathing", when NLP runs, then `cardiac_risk_flag` and `respiratory_distress` must be `true` |
| **Priority** | P0 |
| **Status** | `CURRENT` |

#### PRATHAM-FR-006: NLP Graceful Degradation

| Field | Value |
|---|---|
| **Requirement** | When NLP extraction fails, the system must fall back to deterministic symptom-derived flags without blocking the intake pipeline |
| **Actor** | System |
| **Acceptance Criteria** | Given Groq API is unavailable, when intake is submitted, then risk scoring and investigation recommendations must still execute using fallback flags |
| **Priority** | P0 |
| **Status** | `CURRENT` |

### Risk Scoring

#### PRATHAM-FR-007: Operational Risk Calculation

| Field | Value |
|---|---|
| **Requirement** | The system must compute cardiac, respiratory, trauma, and neurological risk scores (0-100) and overall severity using rule-based weighted scoring |
| **Actor** | System |
| **Acceptance Criteria** | Given vitals with HR=130, SpO₂=88, and symptoms with chest_pain=true, when risk scoring runs, then cardiac_risk ≥50 and respiratory_risk ≥30 |
| **Priority** | P0 |
| **Status** | `CURRENT` |

#### PRATHAM-FR-008: Preparation Alert Generation

| Field | Value |
|---|---|
| **Requirement** | The system must generate hospital preparation alerts based on risk score thresholds |
| **Actor** | System |
| **Acceptance Criteria** | Given cardiac_risk=60, when alerts are generated, then `icu_standby` alert must be present |
| **Priority** | P1 |
| **Status** | `CURRENT` |

### Investigations

#### PRATHAM-FR-009: Pathway-Based Investigation Recommendations

| Field | Value |
|---|---|
| **Requirement** | The system must recommend investigations based on symptom pathway gates with risk-threshold escalation |
| **Actor** | System |
| **Acceptance Criteria** | Given chest_pain=true and cardiac_risk=65, when investigations are recommended, then ECG, Troponin, CBC, Echocardiogram, and Cardiac Enzymes must be in the list |
| **Priority** | P0 |
| **Status** | `CURRENT` |

#### PRATHAM-FR-010: Doctor Investigation Approval

| Field | Value |
|---|---|
| **Requirement** | Doctors must be able to approve, reject, or request more information on recommended investigations |
| **Actor** | Doctor |
| **Acceptance Criteria** | Given an investigation with status=pending_approval, when doctor approves it, then status=approved and approved_at and approved_by are set |
| **Priority** | P0 |
| **Status** | `CURRENT` |

### Evidence

#### PRATHAM-FR-011: Evidence File Upload

| Field | Value |
|---|---|
| **Requirement** | Nurses must be able to upload evidence files (JPEG/PNG/PDF/TXT) linked to intakes and optionally to specific investigations |
| **Actor** | Nurse |
| **Acceptance Criteria** | Given a valid intake_id and a JPEG file, when uploaded, then the file is stored in Supabase Storage, a signed URL is generated, and an evidence row is created |
| **Priority** | P0 |
| **Status** | `CURRENT` |

### Lab Analysis

#### PRATHAM-FR-012: XGBoost Cardiac Risk Analysis

| Field | Value |
|---|---|
| **Requirement** | The system must run XGBoost cardiac risk prediction with SHAP explainability on-demand for any intake |
| **Actor** | Doctor/Nurse (triggers) |
| **Acceptance Criteria** | Given a valid intake with vitals, when lab analysis runs, then a lab_results row is created with prediction, risk_probability, shap_values, and input_features |
| **Priority** | P0 |
| **Status** | `CURRENT` |

### Imaging Analysis

#### PRATHAM-FR-013: EfficientNetB0 Pneumonia Classification

| Field | Value |
|---|---|
| **Requirement** | The system must classify chest X-ray images as pneumonia/normal with Grad-CAM visualization |
| **Actor** | System (triggered by evidence upload) |
| **Acceptance Criteria** | Given a chest X-ray evidence file, when imaging analysis runs, then an imaging_results row is created with prediction, pneumonia_probability, confidence, and gradcam_url |
| **Priority** | P0 |
| **Status** | `CURRENT` |

### Aggregation

#### PRATHAM-FR-014: Evidence Aggregation with Suppression

| Field | Value |
|---|---|
| **Requirement** | The system must aggregate all available evidence sources into condition probabilities using deterministic heuristic scoring with confidence suppression |
| **Actor** | System |
| **Acceptance Criteria** | Given only 1 evidence source available, when aggregation runs, then confidence_suppressed must be true and probabilities must be null |
| **Priority** | P0 |
| **Status** | `CURRENT` |

### Workflow

#### PRATHAM-FR-015: State Machine Enforcement

| Field | Value |
|---|---|
| **Requirement** | All status transitions must be validated against the defined state machine; invalid transitions must be rejected |
| **Actor** | System |
| **Acceptance Criteria** | Given a patient in status=case_closed, when a transition to analysis_running is attempted, then the transition must be rejected |
| **Priority** | P0 |
| **Status** | `CURRENT` |

#### PRATHAM-FR-016: Audit Trail

| Field | Value |
|---|---|
| **Requirement** | Every status transition must be recorded in the workflow_logs table with actor type, actor name, timestamp, and reason |
| **Actor** | System |
| **Acceptance Criteria** | Given any status transition, then a workflow_logs row must be created with old_status, new_status, actor_type, actor_name, and reason |
| **Priority** | P0 |
| **Status** | `CURRENT` |

### Clinical Report

#### PRATHAM-FR-017: Clinical Intelligence Report Generation

| Field | Value |
|---|---|
| **Requirement** | The system must generate a comprehensive clinical intelligence report assembling all evidence, clinical reasoning, scores, and interpretation |
| **Actor** | System (on doctor request) |
| **Acceptance Criteria** | Given a completed pipeline, when report is requested, then a 17-section JSON report is returned with patient summary, vitals, symptoms, risk scores, NLP findings, lab intelligence, imaging intelligence, aggregation, clinical conclusions, interpretation, and explainability |
| **Priority** | P0 |
| **Status** | `CURRENT` |

---

## 25. User Stories

### Nurse Stories

> As a **triage nurse**, I want to **register a walk-in emergency patient with their vitals, symptoms, and emergency description in a single form**, so that **the clinical team receives an immediate risk assessment and investigation recommendations**.

> As a **triage nurse**, I want to **register an ambulance patient en route with an ETA**, so that **the hospital can prepare resources before the patient arrives**.

> As a **nurse**, I want to **see a real-time queue of all active patients with their pipeline status and severity level**, so that **I can prioritize evidence collection for the most critical cases**.

> As a **nurse**, I want to **upload evidence files (X-rays, lab reports) linked to specific approved investigations**, so that **the AI pipeline can analyze them and the doctor can review results**.

> As a **nurse**, I want to **see when the AI pipeline has completed all stages**, so that **I can notify the attending physician that the clinical report is ready**.

### Doctor Stories

> As an **emergency physician**, I want to **see a worklist of patients awaiting my investigation approval**, so that **I can review and approve recommended tests efficiently**.

> As a **doctor**, I want to **approve, reject, or request more information on each recommended investigation**, so that **I can exercise clinical judgment over the testing plan**.

> As a **doctor**, I want to **add custom investigations not in the system's recommendations**, so that **I can order tests based on my clinical assessment**.

> As a **doctor**, I want to **review a clinical intelligence report with condition probabilities, evidence trees, and clinical scores**, so that **I can make informed clinical decisions with full explainability**.

> As a **doctor**, I want to **understand exactly which evidence supports or conflicts with each condition probability**, so that **I can evaluate the reliability of the system's intelligence**.

> As a **doctor**, I want to **export a clinical report as a structured PDF**, so that **I have a printable record for the patient file**.

> As a **doctor**, I want to **ask the clinical copilot questions about a patient's case**, so that **I can quickly access specific evidence, reasoning, or clinical context**.

### System Stories

> As the **system**, I want to **automatically transition ambulance patients to 'arrived' when their ETA elapses**, so that **the workflow state reflects reality without manual intervention**.

> As the **system**, I want to **suppress probability outputs when evidence is insufficient** (fewer than 2 sources or max score below 3.0), so that **clinicians are never presented with unreliable conclusions**.

> As the **system**, I want to **record every status transition in an append-only audit log**, so that **the complete patient journey is traceable for clinical governance**.

---

## 26. Acceptance Criteria

### AC-001: Intake Pipeline Completeness
> Given a valid emergency intake submission, when the response is returned, then: a patient record exists, an emergency_intake record exists with a generated case_id, a vitals record exists, a symptoms record exists, 5 pipeline_status rows exist (all pending or NLP/risk completed), an NLP extraction exists (or fallback), a risk_scores record exists, preparation alerts exist (if thresholds met), and investigation recommendations exist.

### AC-002: Pipeline Status Tracking
> Given a completed evidence pipeline, when the pipeline status endpoint is queried, then every stage that has completed must report status=`completed` with non-null `duration_ms` and `completed_at`.

### AC-003: Confidence Suppression
> Given an intake with only NLP extraction available (1 source), when aggregation runs, then `confidence_suppressed` must be `true` and all condition probabilities must be `null`.

### AC-004: Workflow State Machine Integrity
> Given any workflow status transition, when the transition is validated, then only transitions defined in `VALID_TRANSITIONS` are permitted. Self-transitions are always allowed. Terminal states (`case_closed`, `offline_care`) permit no outgoing transitions.

### AC-005: Evidence Deletion Cascading
> Given an evidence file deletion, when the deletion completes, then related lab_results or imaging_results must be deleted, aggregation_results must be deleted, and affected pipeline stages must be reset to `pending`.

### AC-006: NLP Fallback
> Given the Groq API is unavailable, when an intake is submitted, then the system must complete successfully using symptom-derived fallback flags, and the pipeline NLP stage must be marked `failed`.

### AC-007: Report Completeness
> Given a completed pipeline with all 5 stages, when a clinical report is requested, then the report must contain all 17 sections including patient summary, vitals, symptoms, risk engine, NLP findings, lab intelligence, imaging intelligence, aggregation, clinical conclusions, interpretation, explainability, clinical scores, monitoring priorities, precautions, and pipeline status.

---

## 27. API Requirements

### API Inventory

| Endpoint | Method | Purpose | Actor | Status |
|---|---|---|---|---|
| `/api/intake` | POST | Create emergency intake | Nurse | `CURRENT` |
| `/api/intake/{id}` | GET | Fetch intake details | Nurse/Doctor | `CURRENT` |
| `/nlp/extract` | POST | Run NLP extraction | System | `CURRENT` |
| `/risk/calculate` | POST | Calculate risk scores | System | `CURRENT` |
| `/investigation/recommend` | POST | Generate recommendations | System | `CURRENT` |
| `/api/investigations/queue` | GET | Nurse patient queue | Nurse | `CURRENT` |
| `/api/investigations/approve` | POST | Approve investigations | Doctor | `CURRENT` |
| `/api/investigations/reject` | POST | Reject investigations | Doctor | `CURRENT` |
| `/api/investigations/needs-info` | POST | Request more info | Doctor | `CURRENT` |
| `/api/investigations/add` | POST | Add custom investigation | Doctor | `CURRENT` |
| `/api/investigations/doctor-review` | GET | Doctor review worklist | Doctor | `CURRENT` |
| `/api/evidence/upload` | POST | Upload evidence file | Nurse | `CURRENT` |
| `/api/evidence/{intake_id}` | GET | List evidence for intake | Nurse/Doctor | `CURRENT` |
| `/api/lab-analysis/{intake_id}` | POST | Run XGBoost inference | Doctor/Nurse | `CURRENT` |
| `/api/imaging-analysis/{intake_id}` | POST | Run imaging inference | System | `CURRENT` |
| `/api/aggregation/{intake_id}` | POST | Run aggregation pipeline | System | `CURRENT` |
| `/api/pipeline/status/{intake_id}` | GET | Pipeline status | Nurse/Doctor | `CURRENT` |
| `/api/report/{intake_id}` | GET | Clinical intelligence report | Doctor | `CURRENT` |
| `/api/report/{intake_id}/pdf` | GET | PDF export | Doctor | `CURRENT` |
| `/api/explainability/{intake_id}` | GET | Explainability tree | Doctor | `CURRENT` |
| `/api/copilot/query` | POST | Copilot query | Doctor | `CURRENT` |
| `/api/command-center` | GET | ED command center data | Doctor/Nurse | `CURRENT` |
| `/api/search` | GET | Clinical search | Doctor | `CURRENT` |
| `/api/demo/*` | Various | Demo management | System | `CURRENT` |
| `/api/platform-metrics/*` | GET | Platform telemetry | Admin | `CURRENT` |
| `/api/version` | GET | Version info | System | `CURRENT` |
| `/health` | GET | Liveness probe | Infrastructure | `CURRENT` |
| `/ready` | GET | Readiness probe | Infrastructure | `CURRENT` |
| `/metrics` | GET | Observability telemetry | Infrastructure | `CURRENT` |

---

## 28. Data Requirements

### Entity Relationship Summary

```
patients ←──┐
             │ 1:M
emergency_intake ←──┬── vitals (1:M)
             │      ├── symptoms (1:M)
             │      ├── nlp_extractions (1:M, latest is current)
             │      ├── risk_scores (1:M, latest is current)
             │      ├── preparation_alerts (1:M)
             │      ├── investigation_recommendations (1:M)
             │      │        └── evidence (M:1 optional FK)
             │      ├── evidence (1:M)
             │      ├── lab_results (1:M)
             │      ├── imaging_results (1:M)
             │      ├── aggregation_results (1:M, latest is current)
             │      ├── pipeline_status (1:5, one per stage)
             │      └── workflow_logs (1:M, append-only audit)
```

### Table Summary (14 Tables)

| Table | Domain | Type | Rows per Intake |
|---|---|---|---|
| `patients` | Patient | Current state | 1 |
| `emergency_intake` | Triage | Current state | 1 |
| `vitals` | Triage | Current state | 1 (per visit) |
| `symptoms` | Triage | Current state | 1 (per visit) |
| `nlp_extractions` | AI | Current state (latest) | 1+ |
| `risk_scores` | AI | Current state (latest) | 1+ |
| `preparation_alerts` | Notification | Current state | 0–6 |
| `investigation_recommendations` | Investigation | Current state | 0–10+ |
| `pipeline_status` | Pipeline | Current state | 5 (fixed) |
| `evidence` | Evidence | Current state | 0–N |
| `lab_results` | AI | Current state (latest) | 0–1+ |
| `imaging_results` | AI | Current state (latest) | 0–1+ |
| `aggregation_results` | AI | Current state (latest) | 0–1+ |
| `workflow_logs` | Workflow | Historical (append-only) | 1–20+ |

---

## 29. AI/ML Requirements

### AI Component Inventory

| Component | Type | Model | Framework | Purpose | Fallback | Status |
|---|---|---|---|---|---|---|
| NLP Extraction | LLM | LLaMA 3.3-70B | Groq API | Extract clinical risk flags from text | Deterministic symptom derivation | `CURRENT` |
| Risk Scoring | Deterministic Rules | N/A | Pure Python | Compute operational risk scores | None needed | `CURRENT` |
| Lab Analysis | ML Model | XGBoost | xgboost + shap | Cardiac risk prediction | N/A (model required) | `CURRENT` |
| Imaging Analysis | ML Model | EfficientNetB0 | TensorFlow/Keras | Pneumonia classification | N/A (model required) | `CURRENT` |
| Grad-CAM | Visualization | N/A | TensorFlow + OpenCV | X-ray heatmap overlay | Skipped if cv2 unavailable | `CURRENT` |
| Aggregation | Deterministic Rules | N/A | Pure Python | Evidence synthesis | N/A | `CURRENT` |
| Clinical Reasoning | Deterministic Rules | N/A | Pure Python | Facts → Conclusions | N/A | `CURRENT` |
| Clinical Scoring | Deterministic Rules | N/A | Pure Python | NEWS2, qSOFA, etc. | N/A | `CURRENT` |
| Evidence Ranking | Rule + YAML KB | N/A | Python + YAML | Condition ranking | N/A | `CURRENT` |
| LLM Interpretation | LLM | Via Groq | Groq API | Narrative generation | Rule-based fallback | `CURRENT` |
| Clinical Copilot | Deterministic + LLM | N/A | Python | Conversational Q&A | Tool registry handlers | `CURRENT` |

### Critical Distinction

| Category | Components |
|---|---|
| **Deterministic Rules** | Risk scoring, aggregation, clinical reasoning, clinical scoring, investigation recommendations, evidence ranking |
| **ML Models** | XGBoost (lab), EfficientNetB0 (imaging) |
| **LLM Components** | NLP extraction (Groq/LLaMA), clinical interpretation (Groq), copilot orchestration |
| **Human Decisions** | Investigation approval, clinical report review, treatment decisions |

---

## 30. Explainability Requirements

### Current Explainability Features

| Output | Explainability Mechanism | Status |
|---|---|---|
| Risk scores | Rule weights visible in code; scores are sum of additive contributions | `CURRENT` |
| Investigation recommendations | Pathway-specific gates documented | `CURRENT` |
| Lab analysis (XGBoost) | SHAP values per feature; top-5 feature contributions | `CURRENT` |
| Imaging analysis | Grad-CAM heatmap overlay on X-ray | `CURRENT` |
| Aggregation | `evidence_breakdown_json` traces every score contribution to source | `CURRENT` |
| Aggregation suppression | `suppression_reason` explains why probabilities were withheld | `CURRENT` |
| Clinical reasoning | Supporting/conflicting/missing evidence lists per condition | `CURRENT` |
| Explainability tree | Hierarchical evidence tree with subsystem agreement matrix | `CURRENT` |
| Decision path | Step-by-step decision trace through pipeline | `CURRENT` |
| Confidence factors | List of factors contributing to confidence level | `CURRENT` |
| Uncertainty reasons | Explicit reasons for uncertainty in conclusions | `CURRENT` |

### Explainability Gaps

| Gap | Impact | Priority |
|---|---|---|
| NLP extraction rationale not exposed to user | Doctor cannot see why specific flags were set | P2 |
| Risk score contribution breakdown not shown in UI | Nurse/doctor cannot see which inputs drove each risk score | P2 |
| No model version tracking in results | Cannot trace results to specific model versions | P3 |

---

## 31. Clinical Safety Requirements

### PRATHAM IS NOT:

- ❌ An autonomous doctor
- ❌ A replacement for clinical judgment
- ❌ A treatment-prescription engine
- ❌ A definitive diagnostic authority
- ❌ A regulatory-approved medical device

### Implemented Safety Mechanisms

| Mechanism | Implementation | Status |
|---|---|---|
| **Confidence suppression** | Dual-gate: min 2 sources + min 3.0 max score | `CURRENT` |
| **NLP graceful degradation** | Falls back to symptom-derived flags on LLM failure | `CURRENT` |
| **Pipeline failure isolation** | NLP failure does not block risk scoring or intake | `CURRENT` |
| **State machine enforcement** | Invalid transitions are rejected by validate_status_transition() | `CURRENT` |
| **Input validation** | Pydantic models with clinical ranges (HR 20-250, SpO₂ 50-100) | `CURRENT` |
| **Max HR safeguard** | Documented distinction between resting HR and exercise max HR | `CURRENT` |
| **Deterministic scoring** | Clinical scores (NEWS2, qSOFA) use pure Python, no LLM arithmetic | `CURRENT` |
| **LLM grounding** | LLM generates narrative ONLY from pre-computed clinical facts/conclusions | `CURRENT` |
| **7-layer separation** | Clinical calculations are isolated from generative synthesis | `CURRENT` |
| **No prescriptive language** | System recommends monitoring/investigations, never medications | `CURRENT` |
| **Audit trail** | Every status transition logged with actor, timestamp, reason | `CURRENT` |
| **Evidence provenance** | All aggregation results include source_summary and evidence_breakdown | `CURRENT` |
| **Error re-raising** | `mark_failed()` always re-raises the original exception | `CURRENT` |
| **Uncertainty visibility** | Missing evidence, uncertainty reasons exposed in clinical conclusions | `CURRENT` |

### Missing Safety Mechanisms — Gaps

| Gap | Impact | Priority |
|---|---|---|
| No authentication — any user can perform any action | Critical security risk | P0 |
| No RBAC — nurses could approve investigations via API | Role boundary violation | P0 |
| No data validation on direct Supabase access | Bypasses API validation | P1 |
| No model drift detection | Model accuracy may degrade over time | P2 |
| No clinical validation framework | No systematic clinical accuracy testing | P1 |
| No stale data warnings | Old evidence may be used without recency checks | P2 |

---

## 32. Security & Privacy

### Currently Implemented

| Feature | Implementation |
|---|---|
| Database RLS | All 14 tables have Row Level Security enabled |
| Service-role access | Backend uses `SUPABASE_SERVICE_ROLE_KEY` (bypasses RLS) |
| CORS | Configured for specific frontend origins |
| Environment validation | Startup blocks if required env vars are missing |
| Signed URLs | Evidence files accessed via 7-day signed URLs |
| Private storage bucket | Evidence files stored in private Supabase bucket |
| Structured logging | JSON telemetry with request IDs, pipeline stages |
| Error sanitization | Global exception handler returns generic error messages |

### Required for Production — `FUTURE`

| Requirement | Priority |
|---|---|
| User authentication (JWT/OAuth) | P0 |
| Role-based access control (RBAC) | P0 |
| API rate limiting | P1 |
| Data encryption at rest | P1 |
| Audit logging for data access | P1 |
| Patient data anonymization for development | P1 |
| HTTPS enforcement | P0 |
| Secret rotation | P2 |
| Input sanitization (SQL injection, XSS) | P1 |
| HIPAA/GDPR compliance review | P0 |
| Penetration testing | P1 |
| Data retention policies | P2 |

---

## 33. Non-Functional Requirements

| Requirement | Target | Status |
|---|---|---|
| **Intake response time** | <3 seconds (including NLP, risk, recommendations) | Proposed target |
| **Report generation time** | <5 seconds | Proposed target |
| **Pipeline stage latency** | Tracked via `duration_ms` in pipeline_status | `CURRENT` (measurement) |
| **Imaging inference time** | <10 seconds per X-ray | Proposed target |
| **API availability** | 99.5% uptime | Proposed target |
| **Concurrent intakes** | Support 50 simultaneous intakes | Proposed target |
| **Data integrity** | UUID primary keys, FK constraints, CHECK constraints | `CURRENT` |
| **Error recovery** | Failed pipeline stages retriable; compensating rollback on intake failure | `CURRENT` |
| **Logging** | Structured JSON logging with request ID, patient ID, stage, latency | `CURRENT` |
| **Health monitoring** | `/health`, `/ready`, `/metrics` endpoints | `CURRENT` |
| **Testability** | `USE_MOCK_LLM` flag for deterministic testing | `CURRENT` |

---

## 34. Observability

### Currently Observable

| Category | Implementation |
|---|---|
| Request logs | Structured middleware with method, path, status code, duration |
| Pipeline states | `pipeline_status` table with stage, status, duration_ms, attempt_count |
| Workflow audit | `workflow_logs` table (append-only) |
| Stage latency | Average latencies per stage via `/metrics` endpoint |
| System status | `/health` (liveness), `/ready` (DB + Groq connectivity) |
| Error tracking | Global exception handler with request_id |
| Startup validation | Config validator blocks startup on missing env vars |

### Missing Observability — Gaps

| Gap | Priority |
|---|---|
| No application performance monitoring (APM) | P2 |
| No alerting on pipeline failures | P1 |
| No dashboard for pipeline success/failure rates | P2 |
| No user action audit logging | P1 |
| No model inference latency tracking (per-model) | P3 |

---

## 35. Error Handling & Recovery

### Pipeline Failure Behavior

| Stage | Failure Effect | Recovery |
|---|---|---|
| NLP | Graceful degradation → fallback flags used | Intake continues; stage marked `failed` |
| Risk | Exception re-raised → HTTP 500 | Retry by re-running intake |
| Lab | Exception re-raised → HTTP 500 | Manual retry via re-triggering lab analysis |
| Imaging | Exception re-raised → HTTP 500 | Manual retry via re-triggering imaging analysis |
| Aggregation | Exception re-raised → HTTP 500 | Manual retry via re-triggering aggregation |

### Evidence Deletion Recovery

When evidence is deleted, the system:
1. Deletes related ML results (lab_results, imaging_results)
2. Deletes aggregation results
3. Resets pipeline stages to `pending`
4. Preserves attempt_count history

### Intake Failure Recovery

When any step of intake creation fails:
1. Compensating rollback deletes all previously created records
2. Patient, intake, vitals, symptoms, and pipeline rows are cleaned up
3. HTTP 500 returned with error detail

---

## 36. Product Metrics

### Currently Measurable

| Metric | Source | Status |
|---|---|---|
| Average pipeline stage latency (per stage) | `pipeline_status.duration_ms` via `/metrics` | `CURRENT` |
| Pipeline execution count (per stage) | `pipeline_status` via `/metrics` | `CURRENT` |
| Active case count | `emergency_intake` with active statuses | `CURRENT` |
| Investigation approval rate | `investigation_recommendations.status` | `CURRENT` |
| Evidence upload count | `evidence` table count | `CURRENT` |
| Pipeline completion status | `pipeline_status.status` per intake | `CURRENT` |

### Require Future Instrumentation

| Metric | Priority |
|---|---|
| Time from intake to first doctor review | P1 |
| Time from investigation approval to evidence upload | P2 |
| NLP extraction accuracy vs. manual review | P1 |
| Investigation recommendation acceptance rate | P1 |
| Lab model prediction calibration | P2 |
| Imaging model sensitivity/specificity | P2 |
| Aggregation condition prediction accuracy | P1 |
| User task completion time | P3 |
| Copilot query response time | P3 |

---

## 37. Current Limitations

1. **No authentication/authorization** — The system has no user login, session management, or role enforcement. Any HTTP client can call any endpoint.

2. **Single-condition imaging model** — The EfficientNetB0 model only classifies pneumonia vs. normal. Other chest X-ray pathologies are not detected.

3. **Single-condition lab model** — The XGBoost model only predicts cardiac risk. Other lab analysis types are not supported.

4. **Max HR proxy** — Resting heart rate from vitals is used as a proxy for exercise maximum heart rate in the lab model, which is clinically imprecise.

5. **Limited evidence types** — Only X-rays and lab reports have automated AI analysis. ECG, CT, MRI, ultrasound, and blood work are stored but not analyzed.

6. **5-condition aggregation** — The aggregation engine only scores ACS, PE, Pneumonia, Arrhythmia, and Other. The 13-condition knowledge base is used for ranking but not for probability scoring.

7. **No real-time data** — Vitals are point-in-time entries, not continuous streams.

8. **Copilot uses hardcoded demo data** — The copilot orchestrator defaults to static patient data when no real data is provided.

9. **No offline capability** — System requires network connectivity to Supabase and Groq API.

10. **No multi-tenancy** — Single database schema with no hospital/organization isolation.

---

## 38. Product & Technical Gaps

### Architecture Gaps

| Gap | Evidence | Impact | Priority | Recommended Action |
|---|---|---|---|---|
| Some API routes access Supabase directly (bypass repository pattern) | `api/intake.py` line 300-304: `supabase.table("investigation_recommendations").insert(...)` | Breaks architectural boundary | P2 | Move to investigation_repository |
| Duplicate WorkflowStatus enum | Defined in both `models/workflow.py` and `domains/shared/enums.py` | Potential inconsistency | P3 | Consolidate to single definition |
| `to_db_status()` mapping suggests schema mismatch | Maps 11 workflow states to fewer DB CHECK values | Schema evolution debt | P2 | Align DB CHECK constraint with full 11-state model |

### Clinical Safety Gaps

| Gap | Evidence | Impact | Priority | Recommended Action |
|---|---|---|---|---|
| No authentication | No auth middleware in main.py | Any user can perform any action | P0 | Implement JWT + RBAC |
| NLP `logger` undefined in one path | `nlp_service.py` line 78 uses `logger` but only imports `logging` at top level | Runtime NameError on NLP failure path | P1 | Add `logger = logging.getLogger(__name__)` |
| Signed URLs expire after 7 days | Evidence file_url becomes inaccessible | Broken links in old reports | P2 | Regenerate URLs on access |

### Testing Gaps

| Gap | Evidence | Impact | Priority | Recommended Action |
|---|---|---|---|---|
| No automated test suite in CI | Test files exist but no CI configuration | Regressions undetected | P1 | Add GitHub Actions CI |
| No integration tests for pipeline state machine | Tests focus on E2E but not state transition edge cases | Invalid states possible | P2 | Add state machine unit tests |

### Production-Readiness Gaps

| Gap | Impact | Priority |
|---|---|---|
| No HTTPS configuration | Data transmitted in plaintext | P0 |
| No database migration runner in CI | Schema changes require manual execution | P1 |
| No container health checks in Docker Compose | Unhealthy containers not restarted | P2 |
| No backup strategy | Data loss risk | P1 |
| CORS allows `*` methods and headers | Overly permissive | P2 |

---

## 39. Future Product Roadmap

### Phase 1: Security & Production Readiness — `FUTURE`

| Feature | Description | Priority |
|---|---|---|
| Authentication (JWT) | User login with secure token-based auth | P0 |
| Role-Based Access Control | Enforce nurse/doctor role boundaries | P0 |
| HTTPS enforcement | TLS for all connections | P0 |
| Database backup strategy | Automated backups with point-in-time recovery | P1 |
| CI/CD pipeline | Automated testing and deployment | P1 |

### Phase 2: Clinical Intelligence Expansion — `FUTURE`

| Feature | Description | Priority |
|---|---|---|
| Multi-condition imaging | Extend imaging model to detect multiple pathologies | P1 |
| ECG analysis | Automated ECG interpretation | P2 |
| Additional lab panels | Beyond cardiac risk to comprehensive metabolic panels | P2 |
| Expanded condition set | Score more than 5 conditions in aggregation | P2 |
| Sepsis detection module | Dedicated sepsis screening pipeline | P1 |

### Phase 3: Hospital Integration — `FUTURE`

| Feature | Description | Priority |
|---|---|---|
| FHIR R4 integration | Standards-based data exchange | P2 |
| HL7 message processing | Receive orders and results from hospital systems | P2 |
| Real-time vital feeds | Continuous monitoring integration | P3 |
| Multi-hospital tenancy | Organization-level data isolation | P3 |

### Phase 4: Advanced Intelligence — `FUTURE`

| Feature | Description | Priority |
|---|---|---|
| Longitudinal intelligence | Full multi-visit trajectory analysis with decompensation detection | P2 |
| Clinical decision support alerts | Proactive alerts for deteriorating patients | P2 |
| Advanced NLP | Domain-specific medical NLP beyond risk flag extraction | P3 |
| Federated learning | Train models across hospitals without sharing data | P3 |

---

## 40. Extensibility / Plugin Architecture

### Current Extension Points

The codebase already exhibits patterns that support future plugin architecture:

1. **Knowledge Base YAML** — 13 condition files (`knowledge_base/*.yaml`) define supporting/conflicting findings, monitoring priorities, and clinical precautions per condition. New conditions can be added by creating new YAML files.

2. **Pipeline Stages** — The `STAGES` tuple in `pipeline_status_service.py` and the DB CHECK constraint define the current 5 stages. Adding a new stage requires:
   - Adding the stage name to the CHECK constraint
   - Registering it in `STAGES`
   - Implementing the stage service
   - Updating `initialize_pipeline()` to create the new row

3. **Evidence Types** — The `evidence_type` CHECK constraint in the evidence table defines supported types. New types require:
   - Adding to the CHECK constraint
   - Creating an analysis service
   - Registering the analysis endpoint

### Future Plugin Architecture — `FUTURE`

> New clinical intelligence capabilities should be addable without restructuring the core platform.

A future module should be able to plug into:

```
Input → Processing → Evidence → Result → Explanation → Persistence → Workflow → UI
```

without forcing unrelated modules to change.

**Requirements:**
- Module registration mechanism
- Standard input/output contracts
- Pipeline integration hooks
- UI component registry
- Knowledge base extension points

---

## 41. Traceability Matrix

| Requirement | User | UI | API | Service | Repository | DB Entity | Test | Status |
|---|---|---|---|---|---|---|---|---|
| FR-001: Intake | Nurse | `nurse.intake.tsx` | POST /api/intake | `intake.py` (API) | `triage/repository.py` | `patients`, `emergency_intake`, `vitals`, `symptoms` | `test_phase1.py` | `CURRENT` |
| FR-005: NLP | System | Report view | POST /nlp/extract | `nlp_service.py` | `ai/repository.py` | `nlp_extractions` | `test_e2e.py` | `CURRENT` |
| FR-007: Risk | System | Report view | POST /risk/calculate | `risk_service.py` | `ai/repository.py` | `risk_scores` | `test_e2e.py` | `CURRENT` |
| FR-009: Investigations | System | Doctor review | N/A (inline) | `investigation_service.py` | `investigation/repository.py` | `investigation_recommendations` | `test_e2e.py` | `CURRENT` |
| FR-010: Approval | Doctor | `doctor.review.tsx` | POST /api/investigations/approve | `investigation_approval_service.py` | `investigation/repository.py` | `investigation_recommendations` | `test_scenarios_phase2.py` | `CURRENT` |
| FR-011: Evidence Upload | Nurse | Upload row | POST /api/evidence/upload | `evidence.py` (API) | `evidence/repository.py` | `evidence` | `test_phase2_snapshots.py` | `CURRENT` |
| FR-012: Lab Analysis | Doctor | Report view | POST /api/lab-analysis/{id} | `lab_analysis_service.py` | `ai/repository.py` | `lab_results` | `test_e2e.py` | `CURRENT` |
| FR-013: Imaging | System | Report view | POST /api/imaging-analysis/{id} | `imaging_model.py` | `ai/repository.py` | `imaging_results` | — | `CURRENT` |
| FR-014: Aggregation | System | Report view | POST /api/aggregation/{id} | `aggregation_service.py` | `ai/repository.py` | `aggregation_results` | `test_phase2_snapshots.py` | `CURRENT` |
| FR-015: State Machine | System | Status badges | N/A (internal) | `workflow_service.py` | `workflow/repository.py` | `workflow_logs` | — | `CURRENT` |
| FR-017: Report | Doctor | `doctor.report.tsx` | GET /api/report/{id} | `report_service.py` | Multiple | Multiple | `verify_report.py` | `CURRENT` |

---

## 42. Source-of-Truth Matrix

| Area | Source of Truth | Verified? | Notes |
|---|---|---|---|
| Database Schema | `backend/schema_v7.sql` (14 tables) | ✅ Yes | Consolidated DDL; matches migrations |
| API Routes | `backend/app/main.py` (21 routers) | ✅ Yes | All routers registered with prefixes |
| Workflow States | `domains/shared/enums.py::WorkflowStatus` (11 states) | ✅ Yes | Duplicate in `models/workflow.py` |
| Pipeline Stages | `pipeline_status_service.py::STAGES` (5 stages) | ✅ Yes | Matches DB CHECK constraint |
| Risk Scoring Rules | `risk_service.py` | ✅ Yes | Pure Python, fully auditable |
| Investigation Rules | `investigation_service.py` | ✅ Yes | 4 pathways + safety net |
| Aggregation Logic | `aggregation_service.py` | ✅ Yes | Deterministic, no ML/LLM |
| Clinical Reasoning | `clinical_reasoning_service.py` | ✅ Yes | 2-layer: facts + conclusions |
| ML Models | `ml_models/` (2 files: XGBoost + EfficientNetB0) | ✅ Yes | Both loaded at startup |
| Knowledge Base | `knowledge_base/*.yaml` (13 conditions) | ✅ Yes | ACS, PE, Pneumonia, etc. |
| Frontend Routes | `frontend/src/routes/` (29 route files) | ✅ Yes | TanStack Router file-based routing |
| Tests | `backend/test_*.py` (12+ test files) | ✅ Yes | E2E, regression, stress, phase tests |
| Documentation | `docs/` (7 docs) + root-level markdown files | ✅ Yes | Architecture, API, deployment, FAQ |

---

## 43. Architecture Diagrams

### System Architecture

```
                           ┌─────────────────────┐
                           │    Clinical Users     │
                           │  (Nurse / Doctor)     │
                           └──────────┬────────────┘
                                      │
                           ┌──────────▼────────────┐
                           │     React Frontend     │
                           │  TanStack Router/Query │
                           │  Nurse: intake/queue   │
                           │  Doctor: review/report │
                           │  System: copilot/atlas │
                           └──────────┬────────────┘
                                      │ HTTP/JSON
                           ┌──────────▼────────────┐
                           │  FastAPI Backend       │
                           │  21 API Routers        │
                           │  Pydantic Validation   │
                           │  Structured Logging    │
                           │  CORS / Error Handling │
                           └──────────┬────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                   │
         ┌──────────▼──────┐  ┌──────▼──────┐  ┌───────▼────────┐
         │ Service Layer   │  │ Workflow    │  │ ML Models      │
         │ NLP · Risk ·    │  │ Service     │  │ XGBoost (Lab)  │
         │ Aggregation ·   │  │ 11-state    │  │ EfficientNetB0 │
         │ Clinical        │  │ machine     │  │ (Imaging)      │
         │ Reasoning ·     │  │ Audit trail │  │ SHAP/Grad-CAM  │
         │ Report ·        │  │ Pipeline    │  │                │
         │ Copilot         │  │ coordination│  │                │
         └────────┬────────┘  └──────┬──────┘  └───────┬────────┘
                  │                  │                   │
         ┌────────▼──────────────────▼───────────────────▼──────┐
         │                  Repository Layer                     │
         │  Domains: AI · Evidence · Investigation · Patient ·   │
         │           Pipeline · Triage · Workflow                │
         └──────────────────────────┬───────────────────────────┘
                                    │
         ┌──────────────────────────▼───────────────────────────┐
         │              PostgreSQL (Supabase)                    │
         │  14 tables · RLS · Service-role policies              │
         │  UUID PKs · TIMESTAMPTZ · JSONB audit payloads       │
         └──────────────────────────┬───────────────────────────┘
                                    │
                     ┌──────────────▼──────────────┐
                     │    Supabase Storage          │
                     │  Evidence files (private)    │
                     │  Grad-CAM overlays           │
                     │  7-day signed URLs           │
                     └─────────────────────────────┘

         External Services:
         ┌────────────────┐
         │  Groq API      │  ← NLP extraction (LLaMA 3.3-70B)
         │  (Cloud LLM)   │  ← Clinical interpretation narrative
         └────────────────┘
```

### Clinical Intelligence Pipeline

```
Patient Intake
     │
     ▼
┌─── Stage 1: NLP ─────────────────────────────────────┐
│  Input: emergency_description + symptoms + vitals     │
│  Model: Groq/LLaMA 3.3-70B (or deterministic fallback)│
│  Output: 7 boolean flags + keywords + clinical summary│
│  Persistence: nlp_extractions                         │
└───────────────────────┬───────────────────────────────┘
                        │
                        ▼
┌─── Stage 2: Risk ─────────────────────────────────────┐
│  Input: vitals + symptoms + NLP flags                  │
│  Model: Rule-based weighted scoring (pure Python)      │
│  Output: 4 scores (0-100) + overall severity           │
│  Side effect: preparation_alerts generated             │
│  Persistence: risk_scores                              │
└───────────────────────┬───────────────────────────────┘
                        │
     [Doctor approves investigations · Nurse uploads evidence]
                        │
        ┌───────────────┼───────────────┐
        ▼                               ▼
┌─── Stage 3: Lab ──────────┐  ┌─── Stage 4: Imaging ──────────┐
│  Input: patient features   │  │  Input: chest X-ray image      │
│  Model: XGBoost classifier │  │  Model: EfficientNetB0 (Keras) │
│  Output: high/low risk     │  │  Output: pneumonia/normal      │
│  Explainability: SHAP      │  │  Explainability: Grad-CAM      │
│  Persistence: lab_results  │  │  Persistence: imaging_results  │
└───────────────┬────────────┘  └───────────────┬────────────────┘
                │                               │
                └───────────────┬───────────────┘
                                ▼
┌─── Stage 5: Aggregation ──────────────────────────────┐
│  Input: NLP + Risk + Lab + Imaging (all optional)      │
│  Model: Deterministic heuristic scoring (no ML/LLM)    │
│  Steps: Score → Suppress → Normalize → Persist         │
│  Output: 5-condition probability distribution           │
│  Safety: Dual-gate confidence suppression              │
│  Explainability: evidence_breakdown_json                │
│  Persistence: aggregation_results                      │
└───────────────────────┬───────────────────────────────┘
                        │
                        ▼
┌─── Clinical Reasoning Layer ──────────────────────────┐
│  Layer 1: Clinical Facts (raw structured observations) │
│  Layer 2: Clinical Conclusions (deterministic rules)   │
│  + Clinical Scoring (NEWS2, qSOFA, CURB-65, HEART,     │
│    Wells PE)                                           │
│  + Clinical Pattern Engine (syndrome detection)        │
│  + Evidence Ranking (13-condition YAML KB)             │
│  + LLM Interpretation (narrative only, grounded)       │
└───────────────────────┬───────────────────────────────┘
                        │
                        ▼
              Clinical Intelligence Report
              (17-section JSON + PDF export)
```

---

## 44. Product Maturity Assessment

| Dimension | Rating | Rationale |
|---|---|---|
| **Core Pipeline** | ██████████ 90% | Full E2E pipeline from intake to report. All 5 stages functional. |
| **Clinical Intelligence** | ████████░░ 80% | Aggregation, reasoning, scoring, and explainability are comprehensive. Limited to 5 conditions. |
| **Workflow Management** | █████████░ 85% | 11-state machine with audit trail, auto-transitions, lifecycle management. |
| **Frontend UX** | ████████░░ 80% | Full nurse and doctor workflows. Rich components. Some areas incomplete. |
| **Security** | ██░░░░░░░░ 20% | RLS enabled, CORS configured, but NO authentication or authorization. |
| **Production Readiness** | ███░░░░░░░ 30% | Runs locally; Docker Compose exists. Not hardened for production. |
| **Testing** | █████░░░░░ 50% | E2E tests, regression scripts, stress tests exist. No CI/CD. |
| **Observability** | █████░░░░░ 50% | Structured logging, health probes, metrics endpoint. No APM. |
| **Clinical Validation** | ████░░░░░░ 40% | Score validation reports exist. No external clinical validation. |
| **Documentation** | ███████░░░ 70% | Architecture, API, deployment docs. This PRD is the first comprehensive specification. |

---

## 45. Final Product Definition

### What Exactly Is PRATHAM?

PRATHAM is an **emergency clinical intelligence platform** that transforms the chaotic, fragmented process of emergency patient assessment into a structured, explainable, and auditable workflow.

**Who uses PRATHAM:** Emergency triage nurses and attending physicians in hospital emergency departments.

**What they provide:** Patient demographics, vital signs (heart rate, SpO₂, blood pressure, temperature, respiratory rate), six structured symptom indicators, free-text emergency descriptions, and clinical evidence files (X-rays, lab reports).

**What PRATHAM processes:** Five automated pipeline stages — NLP extraction (LLM-powered with deterministic fallback), rule-based operational risk scoring (4 categories, 0-100), pathway-specific investigation recommendations, XGBoost cardiac risk prediction (with SHAP explainability), and EfficientNetB0 pneumonia classification (with Grad-CAM visualization) — followed by a deterministic 7-step heuristic aggregation that synthesizes all evidence into a 5-condition probability distribution.

**What intelligence it generates:** Condition probability distributions (ACS, PE, Pneumonia, Arrhythmia, Other), clinical risk scores (NEWS2, qSOFA, CURB-65, HEART, Wells PE), evidence-based condition rankings from a 13-condition knowledge base, supporting/conflicting/missing evidence matrices, subsystem agreement analysis, confidence-calibrated conclusions, and grounded clinical narrative.

**What decisions it supports:** Investigation ordering, resource preparation (ICU, oxygen, trauma team, CT scanner, blood bank), clinical priority assessment, and differential consideration — all presented as decision-support intelligence, never as directives.

**Where humans remain in control:** Doctors explicitly approve every investigation. All treatment decisions are made by clinicians. The system presents intelligence; humans act on it. The workflow state machine requires physician-initiated transitions for all clinical-decision states.

**How the system safely handles uncertainty:** Dual-gate confidence suppression withholds probability outputs when evidence is insufficient (fewer than 2 data sources or maximum condition score below 3.0). The two-layer clinical reasoning engine explicitly separates facts from conclusions. The LLM generates narrative text but never computes clinical values. Every output includes uncertainty reasons and missing evidence indicators. NLP failures gracefully degrade to deterministic extraction rather than blocking patient care.

**Why the architecture can evolve without being rebuilt:** The layered architecture (API → Services → Workflow → Repositories → Database) with domain-bounded repositories, the YAML-driven knowledge base, the modular pipeline stage design, and the clear separation between deterministic rules, ML models, and LLM components create natural extension points for new clinical intelligence modules without requiring core platform restructuring.

---

> **Document Classification:** This PRD was generated by comprehensive reverse-engineering of the PRATHAM repository at `d:\pratham`. Every capability marked `CURRENT` was verified from actual source code. Where implementation could not be verified, it is explicitly marked `PARTIAL` or `FUTURE`. The repository is the authoritative source of truth; where this document and the repository diverge, the repository wins.
