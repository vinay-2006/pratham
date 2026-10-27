# PRATHAM — Product Requirements Document (PRD)

**Product Name**: PRATHAM — Predictive Risk Assessment & Triage for Healthcare AI Management
**Version**: v5.0.0
**Document Date**: July 8, 2026
**Classification**: Enterprise Clinical AI Platform — Emergency Department Decision Support

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Vision & Goals](#3-product-vision--goals)
4. [Target Users & Personas](#4-target-users--personas)
5. [System Architecture](#5-system-architecture)
6. [Core Features & Modules](#6-core-features--modules)
7. [Clinical Knowledge Base](#7-clinical-knowledge-base)
8. [AI/ML Engine Specifications](#8-aiml-engine-specifications)
9. [API Surface](#9-api-surface)
10. [Frontend Application](#10-frontend-application)
11. [System Atlas (Observability Portal)](#11-system-atlas-observability-portal)
12. [Clinical Validation & Regression Testing](#12-clinical-validation--regression-testing)
13. [Performance Benchmarks](#13-performance-benchmarks)
14. [Security & Compliance](#14-security--compliance)
15. [Deployment Architecture](#15-deployment-architecture)
16. [Technical Stack](#16-technical-stack)
17. [Technical Debt & Roadmap](#17-technical-debt--roadmap)
18. [Version History](#18-version-history)

---

## 1. Executive Summary

PRATHAM is an **enterprise-grade emergency department clinical AI platform** that provides:

- Real-time **in-transit ambulance intake** and patient triage
- **NLP entity extraction** from clinical free-text notes
- **Demographic-aware lab analytics** with dynamic age/sex/pregnancy reference ranges
- **Deterministic clinical scoring** (NEWS2, qSOFA, CURB-65, HEART, Wells PE)
- **Medical imaging AI** (EfficientNetB0 chest X-ray pneumonia detection with Grad-CAM)
- **13 emergency disease rule engine** with evidence ranking
- An interactive **Evidence-Aware Clinical & System Copilot** with conversational Q&A
- **Longitudinal patient trajectory tracking** with multi-visit delta analysis
- **Emergency Department Command Center** with real-time acuity dashboards

Over four development phases, PRATHAM evolved from a basic intake prototype into a modular, **7-layer hospital intelligence platform** evaluating 13 emergency conditions with **100% regression test accuracy** across 20 high-fidelity clinical scenarios.

> [!IMPORTANT]
> PRATHAM is a **clinical decision-support system** — it never prescribes medications, drug names, or dosages. All clinical calculations are deterministic (pure Python), and the LLM is only used for narrative synthesis backed by verified metrics.

---

## 2. Problem Statement

Emergency departments face critical challenges:

| Challenge | Impact |
|:---|:---|
| **Diagnostic uncertainty** during initial patient intake | Delayed triage and treatment |
| **LLM hallucination risk** in clinical AI systems | Incorrect risk scores and unsafe recommendations |
| **Static dashboards** that don't allow interactive clinical reasoning | Clinicians cannot interrogate the AI's reasoning |
| **Missing demographic context** in lab interpretation | Incorrect lab flagging across age/sex groups |
| **No longitudinal tracking** of patient decompensation | Missed clinical deterioration trends |

PRATHAM directly addresses each of these by isolating deterministic clinical logic from generative AI synthesis.

---

## 3. Product Vision & Goals

### Vision
Build a **safe, transparent, and high-performance** hospital AI platform that augments emergency clinicians with deterministic diagnostic intelligence — never replacing clinical judgment, always supporting it.

### Goals

| Goal | Metric |
|:---|:---|
| Zero LLM hallucination in clinical scores | 100% deterministic calculation accuracy |
| Sub-5-second end-to-end pipeline | < 4.5s average intake-to-report |
| Comprehensive emergency coverage | 13 emergency conditions covered |
| Full clinical regression suite | 20/20 scenarios passing (100%) |
| Interactive clinical reasoning | 8 copilot query intents supported |
| Demographic-aware diagnostics | Age/sex/pregnancy-adjusted reference ranges |

---

## 4. Target Users & Personas

| Persona | Role | Primary Touchpoints |
|:---|:---|:---|
| **Paramedic / Ambulance Nurse** | Enters in-transit intake data (demographics, vitals, symptoms) | Nurse Intake Form (`/nurse/intake`) |
| **Charge Nurse** | Monitors ER acuity and triage queue priorities | Command Center (`/command-center`) |
| **Attending Physician** | Reviews clinical reports, approves/adjusts AI recommendations | Doctor Workstation (`/doctor/review`, `/doctor/approvals`) |
| **Radiologist** | Reviews imaging AI overlay results (Grad-CAM heatmaps) | Imaging Analysis (`/imaging`) |
| **Hospital Administrator** | Monitors pipeline telemetry, system health, and platform metrics | Admin Dashboard (`/admin`), System Atlas |

---

## 5. System Architecture

### 7-Layer Modular Processing Pipeline

PRATHAM uses a modular 7-layer design to **prevent LLM hallucinations** by isolating clinical calculations from generative synthesis:

```text
              Patient Data (Vitals, Symptoms, Free-text Intake)
                                    │
                                    ▼
              Layer 1: Clinical Context & Demographic Engine
            (Pregnancy, Age, Chronic baseline creatinine status)
                                    │
                                    ▼
                Layer 2: Demographic Reference Range Engine
                (Analyte → Range → qualitative status: HIGH)
                                    │
                                    ▼
              Layer 3: Lab & Chest Radiograph Imaging Engine
              (Pneumonia probability, Lab analyte parsing)
                                    │
                                    ▼
                  Layer 4: Disease-Agnostic Syndrome Engine
           (Respiratory Distress, Shock, Myocardial Injury, etc.)
                                    │
                                    ▼
                  Layer 5: Deterministic Scoring Engine
             (NEWS2 · qSOFA · CURB-65 · HEART · Wells PE)
                                    │
                                    ▼
              Layer 6: 13 Emergency Disease Knowledge Base Engine
          (ACS, HF, PE, Sepsis, Pneumonia, Stroke, DKA, AKI, etc.)
                                    │
                                    ▼
                  Layer 7: Grounded Clinical LLM Synthesis
               (4-Tier Recommendations & Clinical Audit Logs)
                                    │
              ┌─────────────────────┴─────────────────────┐
              ▼                                           ▼
  Emergency Command Center                  Longitudinal Delta & Explorer
 (Active ER Cases, Resources)           (Visit Comparison, Explainability)
```

### Key Architecture Principles

1. **Deterministic-First**: All risk scores, confidence levels, and evidence summaries are calculated strictly by auditable Python engines. The LLM never computes clinical values.
2. **Grounded Synthesis**: The LLM receives pre-computed deterministic outputs and synthesizes narrative reports — it does not generate clinical data.
3. **Model Neutrality**: Uses neutral engine names (`Medical Imaging Engine`, `Laboratory Intelligence Engine`) rather than specific model names in patient-facing outputs.
4. **Audit Logging**: Every report logs `clinical_audit_log` metadata containing pipeline stage latencies, execution timestamps, and subsystem version tags.

---

## 6. Core Features & Modules

### 6.1 In-Transit Nurse Intake
- **Route**: `POST /api/intake`
- **Service**: [intake.py](file:///d:/pratham/backend/app/api/intake.py)
- **UI**: [nurse-intake.tsx](file:///d:/pratham/frontend/src/routes/_app.nurse.intake.tsx)
- **Capability**: Capture demographics, symptoms, vitals en route. Initial risk categorization, vital anomaly warnings, and preliminary triage level assignment.
- **Status**: ✅ Fully Implemented

### 6.2 Clinical NLP Entity Extraction
- **Route**: `POST /nlp/extract`
- **Service**: [nlp_service.py](file:///d:/pratham/backend/app/services/nlp_service.py)
- **Capability**: Groq API LLM-powered NLP entity extraction parsing unstructured clinical notes to detect head trauma, loss of consciousness, and cardiac/respiratory distress flags.
- **Status**: ✅ Fully Implemented

### 6.3 Demographic Reference Range Lab Engine
- **Route**: `POST /api/lab/analyze`
- **Services**: [reference_range_service.py](file:///d:/pratham/backend/app/services/reference_range_service.py), [lab_intelligence_service.py](file:///d:/pratham/backend/app/services/lab_intelligence_service.py)
- **Capability**: Demographic-aware lab panels (Troponin, WBC, Creatinine, D-Dimer, Glucose, Potassium, Hemoglobin) flagged dynamically based on age, sex, and pregnancy. Returns qualitative flags: `NORMAL`, `HIGH`, `LOW`, `CRITICAL_HIGH`, `CRITICAL_LOW`.
- **Supported Demographics**: Adult Male, Adult Female, Pediatric, Elderly, Pregnant
- **Status**: ✅ Fully Implemented (100% validation pass rate across 12 demographic combinations)

### 6.4 Medical Imaging AI Engine
- **Route**: `POST /api/imaging/analyze`
- **Services**: [imaging_model.py](file:///d:/pratham/backend/app/ml/imaging_model.py), [imaging_analysis.py](file:///d:/pratham/backend/app/api/imaging_analysis.py)
- **Capability**: EfficientNetB0 PyTorch classification for pneumonia on Chest X-Rays uploaded to Supabase Storage. Includes **Grad-CAM visualization** for interpretable heatmap overlays.
- **Status**: ✅ Fully Implemented

### 6.5 XGBoost Lab Intelligence Engine
- **Service**: [lab_model.py](file:///d:/pratham/backend/app/ml/lab_model.py)
- **Capability**: XGBoost-based lab value interpretation with SHAP explanations for clinical analyte evaluation.
- **Status**: ✅ Fully Implemented

### 6.6 Emergency Operational Risk Estimator
- **Service**: [risk_service.py](file:///d:/pratham/backend/app/services/risk_service.py)
- **Capability**: Cardiac, respiratory, trauma, and neurological risk metric evaluation. Risk bands: Low, Moderate, High, Critical.
- **Status**: ✅ Fully Implemented

### 6.7 Clinical Scoring Engine
- **Service**: [clinical_scoring_service.py](file:///d:/pratham/backend/app/services/clinical_scoring_service.py)
- **Capability**: Deterministic calculation of 5 validated clinical scores:

| Score | Purpose | Parameters |
|:---|:---|:---|
| **NEWS2** | National Early Warning Score 2 | RR, SpO₂, BP, HR, Temperature, Consciousness |
| **qSOFA** | Quick Sepsis Assessment | RR, BP, Mental Status |
| **CURB-65** | Pneumonia Severity | Confusion, BUN, RR, BP, Age ≥65 |
| **HEART** | Cardiac Risk (MACE) | History, ECG, Age, Risk Factors, Troponin |
| **Wells PE** | Pulmonary Embolism Probability | Clinical signs, HR, Immobilization, D-Dimer |

- **Status**: ✅ Fully Implemented (100% validation pass rate across 12 test vectors)

### 6.8 Clinical Pattern Engine
- **Service**: [clinical_pattern_engine.py](file:///d:/pratham/backend/app/services/clinical_pattern_engine.py)
- **Capability**: Detects 5 disease-agnostic physiological syndromes:
  - Respiratory Distress
  - Hemodynamic Instability (Shock)
  - Systemic Inflammation
  - Myocardial Injury
  - Acute Kidney Injury (AKI)
- **Status**: ✅ Fully Implemented

### 6.9 Evidence Ranking Engine
- **Service**: [evidence_ranking_engine.py](file:///d:/pratham/backend/app/services/evidence_ranking_engine.py)
- **Capability**: Parses 13 emergency condition YAML rules, mapping supportive vs. conflicting clinical evidence weights. Calculates rule match statuses across independent reasoning engines.
- **Status**: ✅ Fully Implemented

### 6.10 Clinical Reasoning Layer
- **Service**: [clinical_reasoning_service.py](file:///d:/pratham/backend/app/services/clinical_reasoning_service.py)
- **Capability**:
  - **Layer 1 (Facts)**: Pure extraction of structured data (Vitals, Symptoms, NLP flags, Lab, Imaging)
  - **Layer 2 (Conclusions)**: Deterministic derivations (Multi-factor clinical confidence, subsystem agreement, uncertainty reasons, ranking justifications, monitoring priorities, precautions, limitations)
- **Multi-Factor Confidence Scale**:
  - `≥ 95%`: `VERY HIGH`
  - `85% – 94%`: `HIGH`
  - `65% – 84%`: `MODERATE`
  - `< 65%`: `LOW`
- **Status**: ✅ Fully Implemented

### 6.11 Grounded Clinical Reports & PDF Export
- **Services**: [report_service.py](file:///d:/pratham/backend/app/services/report_service.py), [pdf_generator.py](file:///d:/pratham/backend/app/services/pdf_generator.py)
- **Routes**: `GET /api/report/{intake_id}` (JSON), `GET /api/report/{intake_id}/pdf` (PDF stream)
- **Capability**: Structured 17-section clinical intelligence report with 4-tier recommendation categories. ReportLab-based PDF generation using in-memory byte buffers. ML model names restricted to Section 17 (System Information & Disclaimer).
- **Status**: ✅ Fully Implemented

### 6.12 ED Command Center
- **Service**: [command_center_service.py](file:///d:/pratham/backend/app/services/command_center_service.py)
- **Route**: `GET /api/command-center/telemetry`
- **UI**: [command-center-view.tsx](file:///d:/pratham/frontend/src/components/command-center-view.tsx)
- **Capability**: Real-time active ER case counts, acuity distribution, smart triage queue rankings, and operational facility recommendations (ICU bed, Cath lab, 12-lead ECG, blood crossmatch) — without prescribing medications.
- **Status**: ✅ Fully Implemented

### 6.13 Longitudinal Trajectory Explorer
- **Services**: [trend_analysis_service.py](file:///d:/pratham/backend/app/services/trend_analysis_service.py), [longitudinal_history_service.py](file:///d:/pratham/backend/app/services/longitudinal_history_service.py)
- **UI**: [case-comparison-explorer.tsx](file:///d:/pratham/frontend/src/components/case-comparison-explorer.tsx), [patient-timeline.tsx](file:///d:/pratham/frontend/src/components/patient-timeline.tsx)
- **Capability**: Comparative physiological deltas between historical visits (e.g., SpO₂ 88% → 96% Improved, Creatinine 0.9 → 1.4 mg/dL AKI Stage 1). Side-by-side multi-visit comparison views.
- **Status**: ✅ Fully Implemented

### 6.14 Explainability Explorer
- **Service**: [explainability_service.py](file:///d:/pratham/backend/app/services/explainability_service.py)
- **UI**: [explainability-explorer.tsx](file:///d:/pratham/frontend/src/components/explainability-explorer.tsx)
- **Capability**: Diagnostic evidence tree with supportive vs. conflicting evidence weights and rule agreement matrices across independent reasoning engines.
- **Status**: ✅ Fully Implemented

### 6.15 Investigation Workflow
- **Services**: [investigation_service.py](file:///d:/pratham/backend/app/services/investigation_service.py), [investigation_registry.py](file:///d:/pratham/backend/app/services/investigation_registry.py)
- **Routes**: `GET /api/investigations/queue`, `POST /api/investigations/approve`, `POST /api/investigations/reject`, `POST /api/investigations/needs-info`
- **Capability**: Pathway-gated investigation recommendations (Cardiac, Respiratory, Trauma, Neurological). Approve/reject/needs-info workflow for physicians. Normalizes raw investigation queries to canonical names via alias mapping.
- **Status**: ✅ Fully Implemented

### 6.16 Visit Classifier
- **Service**: [visit_classifier.py](file:///d:/pratham/backend/app/services/visit_classifier.py)
- **Capability**: Distinguishes routine health checkups from acute emergency intakes. Routine panel automatically recommends CBC, Basic Metabolic Panel, Blood Glucose, and Urinalysis.
- **Status**: ✅ Fully Implemented

### 6.17 Clinical Search Engine
- **Service**: [clinical_search_service.py](file:///d:/pratham/backend/app/services/clinical_search_service.py)
- **UI**: [clinical-search-view.tsx](file:///d:/pratham/frontend/src/components/clinical-search-view.tsx)
- **Capability**: Structured keyword and regex query matching across intake chief complaints, clinical findings, and intake IDs.
- **Status**: ✅ Fully Implemented

### 6.18 Demo Mode
- **Routes**: `GET /api/demo/cases`, `POST /api/demo/load/{case_id}`, `POST /api/demo/reset`
- **Capability**: Library of 10 pre-built clinical demonstration cases. Locked behind `ENABLE_DEMO_MODE=true` to prevent accidental data deletion in production.
- **Status**: ✅ Fully Implemented

---

## 7. Clinical Knowledge Base

### 7.1 Disease Rule Repository

The knowledge base is a **declarative, versioned repository** of 13 emergency condition rules stored as YAML files in [knowledge_base/](file:///d:/pratham/backend/app/knowledge_base):

| # | Condition | YAML File | Key Scoring Dependencies |
|:-:|:---|:---|:---|
| 1 | Acute Coronary Syndrome (ACS) | `acs.yaml` | HEART Score, Troponin, ECG |
| 2 | Acute Kidney Injury (AKI) | `aki.yaml` | Creatinine, BUN, eGFR |
| 3 | Arrhythmia | `arrhythmia.yaml` | HR, ECG, Potassium |
| 4 | Asthma Exacerbation | `asthma.yaml` | SpO₂, RR, Wheezing |
| 5 | COPD Exacerbation | `copd.yaml` | SpO₂, RR, CO₂ Retention |
| 6 | Diabetic Ketoacidosis (DKA) | `dka.yaml` | Glucose, pH, Ketones |
| 7 | Heart Failure | `heart_failure.yaml` | BNP, SpO₂, JVD |
| 8 | Hemorrhagic Shock | `hemorrhagic_shock.yaml` | BP, HR, Hemoglobin |
| 9 | Pulmonary Embolism (PE) | `pe.yaml` | Wells Score, D-Dimer |
| 10 | Pneumonia | `pneumonia.yaml` | CURB-65, CXR, WBC |
| 11 | Seizure | `seizure.yaml` | GCS, Glucose, Neurology |
| 12 | Sepsis | `sepsis.yaml` | qSOFA, NEWS2, Lactate |
| 13 | Stroke | `stroke.yaml` | NIHSS, CT Head, Deficits |

### 7.2 Rule Schema Structure

Each YAML rule contains:
- `condition_key`: Canonical identifier (e.g., `acs`, `pneumonia`)
- `condition_name`: Human-readable clinical title
- `version`: Knowledge Base version (e.g., `2.0`)
- `supporting_patterns`: Disease-agnostic clinical patterns matched by the pattern engine
- `supporting_findings`: Specific vitals, labs, symptoms, and imaging findings supporting diagnosis
- `conflicting_findings`: Findings that conflict with or lower the probability of the diagnosis
- `monitoring_priorities`: Key physiological parameters to track
- `clinical_precautions`: Immediate safety precautions
- `suggested_investigations`: Recommended diagnostic procedures
- `limitations`: Diagnostic caveats and limitations

---

## 8. AI/ML Engine Specifications

### 8.1 NLP Clinical Extraction Engine
- **Provider**: Groq API (Llama-3, JSON Mode)
- **Latency**: ~1.40s per extraction
- **Purpose**: Parse unstructured clinical notes into structured boolean indicators

### 8.2 EfficientNetB0 Imaging Engine
- **Framework**: PyTorch
- **Model**: EfficientNetB0 (fine-tuned for Pneumonia detection)
- **Interpretability**: Grad-CAM heatmap overlay visualization
- **Latency**: ~1.20s per inference
- **Optimization**: Weights loaded once at startup (lifespan context)

### 8.3 XGBoost Lab Intelligence Engine
- **Framework**: XGBoost (≥2.0.0) with SHAP (≥0.44.0)
- **Purpose**: Lab value interpretation with feature importance explanations
- **Optimization**: Estimators loaded once at startup (lifespan context)

### 8.4 Grounded LLM Report Generator
- **Provider**: Groq API
- **Purpose**: Narrative synthesis of structured clinical reports (4-tier recommendations)
- **Safeguard**: Receives only pre-computed deterministic outputs; never generates clinical data independently

---

## 9. API Surface

### Complete REST API Catalog (v5.0.0)

#### Intake & NLP
| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/intake` | Create emergency patient record |
| `POST` | `/nlp/extract` | Trigger NLP entity extraction |

#### Diagnostics & Scoring
| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/lab/analyze` | Demographic-aware lab analysis |
| `POST` | `/api/imaging/analyze` | Chest X-ray EfficientNetB0 classification |
| `GET` | `/api/pipeline/status/{intake_id}` | Live pipeline progress (5 stages) |

#### Evidence & Reports
| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/evidence/upload` | Upload evidence files (X-ray, ECG, labs) |
| `GET` | `/api/evidence/{intake_id}` | List evidence for an intake |
| `GET` | `/api/report/{intake_id}` | Full clinical report (JSON) |
| `GET` | `/api/report/{intake_id}/pdf` | Clinical report (PDF stream) |

#### Investigations Workflow
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/investigations/queue` | All pending investigation requests |
| `GET` | `/api/investigations/patient/{intake_id}` | Investigation recommendations for intake |
| `POST` | `/api/investigations/approve` | Approve investigation |
| `POST` | `/api/investigations/reject` | Reject investigation |
| `POST` | `/api/investigations/needs-info` | Flag for additional info |

#### Evidence-Aware Copilot
| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/copilot/query` | Submit natural-language query (8 intents) |
| `GET` | `/api/copilot/history/{session_id}` | Retrieve conversation history |

#### Telemetry & Health
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe (Supabase + Groq check) |
| `GET` | `/metrics` | Observability telemetry (latencies, counts) |
| `GET` | `/api/version` | Release version metadata |
| `GET` | `/api/release` | Full release info (version, branch, commit) |

#### Admin & Command Center
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/admin/metrics` | System operational metrics |
| `GET` | `/api/command-center/telemetry` | Live ED queue with triage priorities |
| `GET` | `/api/platform-metrics/telemetry` | Platform codebase statistics |

#### Demo Mode
| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/demo/cases` | 10 pre-built clinical demo cases |
| `POST` | `/api/demo/load/{case_id}` | Load demo case into database |
| `POST` | `/api/demo/reset` | Reset all demo patient data |

#### Deprecated Endpoints

| Deprecated | Replacement |
|:---|:---|
| `POST /evidence/xray` | `POST /api/imaging/analyze` |
| `POST /evidence/labs` | `POST /api/lab/analyze` |
| `POST /investigation/recommend` | Full investigations workflow |

---

## 10. Frontend Application

### 10.1 Technology Stack
- **Framework**: React 19 + TanStack Router/Start + Vite 7
- **UI Library**: Radix UI primitives + shadcn/ui components
- **Styling**: Tailwind CSS 4
- **Charts**: Recharts 2
- **PDF Export**: jsPDF + html2canvas
- **State Management**: TanStack React Query

### 10.2 Page Routes & Components

| Route | Component | Purpose |
|:---|:---|:---|
| `/` | [landing.tsx](file:///d:/pratham/frontend/src/components/landing.tsx) | Platform landing page |
| `/nurse/intake` | [nurse-intake](file:///d:/pratham/frontend/src/routes/_app.nurse.intake.tsx) | Multi-step patient intake form |
| `/nurse/dashboard` | [nurse-dashboard](file:///d:/pratham/frontend/src/routes/_app.nurse.dashboard.tsx) | Nurse workstation dashboard |
| `/nurse/queue` | [nurse-queue](file:///d:/pratham/frontend/src/routes/_app.nurse.queue.tsx) | Patient queue management |
| `/command-center` | [command-center-view.tsx](file:///d:/pratham/frontend/src/components/command-center-view.tsx) | Real-time ED acuity dashboard |
| `/doctor/review` | [doctor-review](file:///d:/pratham/frontend/src/routes/_app.doctor.review.tsx) | Physician review workstation |
| `/doctor/approvals` | [doctor-approvals](file:///d:/pratham/frontend/src/routes/_app.doctor.approvals.tsx) | Investigation approval workflow |
| `/doctor/report/{id}` | [clinical-report.tsx](file:///d:/pratham/frontend/src/components/clinical-report.tsx) | 17-section clinical intelligence report |
| `/comparison` | [case-comparison-explorer.tsx](file:///d:/pratham/frontend/src/components/case-comparison-explorer.tsx) | Multi-visit trajectory comparison |
| `/explainability` | [explainability-explorer.tsx](file:///d:/pratham/frontend/src/components/explainability-explorer.tsx) | Diagnostic evidence tree |
| `/investigations` | [investigations](file:///d:/pratham/frontend/src/routes/_app.investigations.tsx) | Investigation management |
| `/imaging` | [imaging](file:///d:/pratham/frontend/src/routes/_app.imaging.tsx) | X-ray upload & Grad-CAM overlay |
| `/knowledge` | [knowledge-base-browser.tsx](file:///d:/pratham/frontend/src/components/knowledge-base-browser.tsx) | Disease rule YAML browser |
| `/admin` | [admin-dashboard.tsx](file:///d:/pratham/frontend/src/components/admin-dashboard.tsx) | System operational dashboard |
| `/search` | [clinical-search-view.tsx](file:///d:/pratham/frontend/src/components/clinical-search-view.tsx) | Clinical keyword search |
| `/architecture` | [architecture-explorer.tsx](file:///d:/pratham/frontend/src/components/architecture-explorer.tsx) | Interactive architecture diagram |

### 10.3 Key UI Components

| Component | Purpose |
|:---|:---|
| [copilot-assistant-drawer.tsx](file:///d:/pratham/frontend/src/components/copilot-assistant-drawer.tsx) | Slide-over Copilot chat with Clinical/System mode switcher |
| [patient-workspace.tsx](file:///d:/pratham/frontend/src/components/patient-workspace.tsx) | Unified patient workstation view |
| [pipeline-status.tsx](file:///d:/pratham/frontend/src/components/pipeline-status.tsx) | Real-time AI pipeline progress tracker |
| [notification-card.tsx](file:///d:/pratham/frontend/src/components/notification-card.tsx) | Clinical alert notification cards |
| [demo-library.tsx](file:///d:/pratham/frontend/src/components/demo-library.tsx) | Demo case library browser |
| [guided-tour.tsx](file:///d:/pratham/frontend/src/components/guided-tour.tsx) | Onboarding guided tour |
| [platform-dashboard.tsx](file:///d:/pratham/frontend/src/components/platform-dashboard.tsx) | Platform metrics dashboard |
| [recruiter-mode.tsx](file:///d:/pratham/frontend/src/components/recruiter-mode.tsx) | Portfolio/recruiter presentation mode |

---

## 11. System Atlas (Observability Portal)

A **separate Next.js application** ([system-atlas/](file:///d:/pratham/system-atlas)) providing deep system observability:

| Page | Purpose |
|:---|:---|
| AI Models | Visualize AI model configurations and performance |
| API Explorer | Interactive API endpoint testing |
| Data Flow | Trace data flow through the 7-layer pipeline |
| Database | Database schema and relationship explorer |
| Decision Explorer | Clinical decision tree visualization |
| State Machine | Pipeline state machine visualization |
| Trace | Request tracing and latency analysis |

---

## 12. Clinical Validation & Regression Testing

### 12.1 Clinical Score Validation (100% Pass Rate)

| Score Engine | Test Cases | Result |
|:---|:---:|:---:|
| NEWS2 | 3 vectors (Low → High severity) | ✅ 3/3 PASS |
| qSOFA | 3 vectors (0–3 range) | ✅ 3/3 PASS |
| CURB-65 | 2 vectors (Low → High mortality) | ✅ 2/2 PASS |
| HEART Score | 2 vectors (Moderate risk) | ✅ 2/2 PASS |
| Wells PE | 2 vectors (Moderate → High probability) | ✅ 2/2 PASS |
| **Total** | **12 vectors** | **✅ 100% PASS** |

### 12.2 Reference Range Demographic Validation (100% Pass Rate)

Validated across 12 demographic combinations including Adult Male, Adult Female, Pediatric, Elderly for analytes: Troponin, Hemoglobin, Creatinine, WBC, Glucose, Potassium.

### 12.3 20-Scenario Clinical Regression Suite (100% Pass Rate)

| ID | Clinical Profile | Top Condition | Status |
|:-:|:---|:---|:---:|
| 01 | Healthy Adult Baseline | No Acute Risk | ✅ |
| 02 | Routine Checkup | Baseline Routine | ✅ |
| 03 | Community Acquired Pneumonia | Pneumonia | ✅ |
| 04 | Acute Coronary Syndrome | ACS | ✅ |
| 05 | Heart Failure Exacerbation | Heart Failure | ✅ |
| 06 | Pulmonary Embolism | PE | ✅ |
| 07 | Acute Ischemic Stroke | Stroke | ✅ |
| 08 | Systemic Inflammatory Response | Sepsis | ✅ |
| 09 | Septic Shock Profile | Septic Shock | ✅ |
| 10 | Acute Asthma Exacerbation | Asthma | ✅ |
| 11 | COPD Exacerbation | COPD | ✅ |
| 12 | Hemorrhagic Shock / Trauma | Hemorrhagic Shock | ✅ |
| 13 | Diabetic Ketoacidosis (DKA) | DKA | ✅ |
| 14 | Severe Hypoglycemia | Neuroglycopenia | ✅ |
| 15 | Acute Kidney Injury (AKI) | AKI | ✅ |
| 16 | Electrolyte Disorder | Hyperkalemia | ✅ |
| 17 | Urinary Tract Infection (Urosepsis) | Sepsis | ✅ |
| 18 | Conflicting Evidence Profile | ACS (conflict flag) | ✅ |
| 19 | Sparse Data Profile | ACS / Low Confidence | ✅ |
| 20 | Missing Modalities Profile | ACS | ✅ |

### 12.4 Copilot System Validation

All 8 query intents validated with 100% pass rate:
- `EXPLAIN_CONDITION`, `COMPARE_CONDITIONS`, `INVESTIGATION_ASSISTANT`, `TIMELINE_QA`, `REPORT_SUMMARY`, `EXPLAINABILITY_MODE`, `KNOWLEDGE_BASE_SEARCH`, `PIPELINE_EXPLANATION`

### 12.5 Test Scripts

| Script | Coverage |
|:---|:---|
| [test_phase1.py](file:///d:/pratham/backend/test_phase1.py) | Phase 1 intake & NLP tests |
| [test_scenarios_phase2.py](file:///d:/pratham/backend/test_scenarios_phase2.py) | Phase 2 clinical scenario regression |
| [test_e2e.py](file:///d:/pratham/backend/test_e2e.py) | End-to-end pipeline tests |
| [test_copilot_system.py](file:///d:/pratham/backend/test_copilot_system.py) | Copilot 8-intent validation |
| [test_v510_stabilization.py](file:///d:/pratham/backend/test_v510_stabilization.py) | v5.1.0 stabilization tests |

---

## 13. Performance Benchmarks

### End-to-End Latency Breakdown

| Pipeline Stage | Avg. Latency | Execution Type | Engine |
|:---|:---:|:---|:---|
| In-Transit Patient Intake | < 150 ms | Write / DB | Supabase PostgreSQL |
| NLP Clinical Extraction | ~1.40 s | Async / LLM | Groq API Llama-3 |
| Demographic Lab Parser | ~0.80 s | CPU Bound | Reference Range Engine |
| Chest X-Ray Imaging AI | ~1.20 s | PyTorch Inference | EfficientNetB0 |
| Deterministic Risk Calculator | < 50 ms | CPU Bound | NEWS2, qSOFA, HEART |
| Evidence Aggregation & Rules | ~0.50 s | CPU Bound | 13 YAML Rule Matcher |
| PDF Clinical Report Export | ~0.60 s | PDF Rendering | ReportLab |
| Copilot Query (Deterministic) | < 30 ms | CPU Bound | Deterministic Engine |
| Copilot Query (Narrative) | ~1.80 s | LLM Bound | Copilot Orchestrator |

**Total End-to-End Pipeline**: ~4.1 seconds average (< 4.5s target)

### High-Impact Optimizations

1. **Model Cache**: PyTorch EfficientNetB0 weights and XGBoost estimators loaded once at startup during lifespan context
2. **Deterministic Bypassing**: Basic scoring, explainability cards, and spec retrieval bypass the LLM, dropping latency from **1.8s → < 30ms**
3. **Optimized PDF Buffers**: In-memory `io.BytesIO` buffers instead of temporary files

---

## 14. Security & Compliance

### 14.1 Secrets Management
- All sensitive keys (`SUPABASE_SERVICE_ROLE_KEY`, `GROQ_API_KEY`) stored in backend `.env`, never exposed to frontend
- `validate_startup_config()` checks env parameters on startup, preventing launch with placeholder values

### 14.2 SQL Injection Prevention
- All database operations via Supabase PostgREST Client SDK or parameterized SQLAlchemy queries
- No raw string interpolation for user-facing parameters

### 14.3 CORS Configuration
- Strictly controlled via `CORSMiddleware` in `main.py`
- Allowed origins limited to configured `FRONTEND_URL` and dev ports — no wildcards in production

### 14.4 Prompt Injection Safeguards
- User queries routed into categorized intent classifiers, not concatenated into system instructions
- Strictly forbidden from prescribing medication dosages or names
- Suppresses output when evidence is missing
- Defers to validated diagnostic rules over LLM diagnostics

### 14.5 File Upload Verification
- Evidence upload validates against medical/imaging MIME types (`image/jpeg`, `image/png`, `application/pdf`)
- File size bounds enforced to prevent DoS via disk exhaustion

### 14.6 Error Handling
- Global server exception handler intercepts unhandled errors
- Logs traceback internally with request ID
- Returns clean `500 Internal Server Error` to client (no path/schema leakage)
- Unique `X-Request-ID` tracing header on every request

### 14.7 Clinical Safety Guardrails

| Safeguard | Implementation |
|:---|:---|
| Zero Medication Prescriptions | System prompts explicitly forbid drug names/dosages |
| Model Neutral Terminology | Uses neutral engine names in patient-facing outputs |
| Missing Evidence Callouts | Explicit flagging of missing investigations in Explainability Cards |
| Deterministic Preference | Bypasses LLM for deterministic questions (zero hallucination) |
| No Prescriptive Language | Operational recommendations state equipment/facility needs only |

---

## 15. Deployment Architecture

### 15.1 Environment Variables

```
SUPABASE_URL           # Supabase project URL
SUPABASE_ANON_KEY      # Supabase anonymous key
SUPABASE_SERVICE_ROLE_KEY  # Supabase service role key
GROQ_API_KEY           # Groq API key for LLM access
FRONTEND_URL           # Frontend origin for CORS
ENABLE_DEMO_MODE       # Toggle demo data routes (default: false)
```

### 15.2 Docker Compose Stack

| Service | Container | Port | Base |
|:---|:---|:---:|:---|
| Backend (FastAPI) | `pratham-backend` | 8000 | Python + Uvicorn |
| Frontend (React + Vite) | `pratham-frontend` | 5173 | Node.js |

Health checks: `curl -f http://localhost:8000/health` (30s interval, 10s timeout, 3 retries)

### 15.3 Database Setup
- Schema: [schema.sql](file:///d:/pratham/backend/schema.sql) — PostgreSQL via Supabase
- Migrations: Sequential via [run_migration.py](file:///d:/pratham/backend/run_migration.py)
- Storage bucket: `evidence` (for uploaded X-rays, ECGs, lab reports)
- Referential integrity: All downstream tables cascade on patient/intake deletion
- Indexes: Composite index on `pipeline_status(intake_id, stage)`, index on `pipeline_status(intake_id)`

### 15.4 Production Checklist
- ✅ `.env` populated with active keys and validated at startup
- ✅ `.env` listed in `.gitignore`
- ✅ Docker healthchecks configured
- ✅ Schema migrations sequentially applied
- ✅ Supabase storage bucket configured with authenticated access
- ✅ Structured JSON logs routed to centralized logging
- ✅ Daily database backup schedule configured

---

## 16. Technical Stack

### Backend

| Technology | Version | Purpose |
|:---|:---|:---|
| Python | 3.x | Core runtime |
| FastAPI | 0.111.0 | REST API framework |
| Uvicorn | 0.30.1 | ASGI server |
| Pydantic | 2.7.1 | Data validation & serialization |
| Supabase | 2.5.0 | Database (PostgreSQL) & Storage |
| Groq | latest | LLM API (Llama-3) |
| XGBoost | ≥ 2.0.0 | Lab intelligence engine |
| SHAP | ≥ 0.44.0 | ML interpretability |
| TensorFlow | ≥ 2.15.0 | EfficientNetB0 imaging |
| Pillow | ≥ 10.0.0 | Image processing |
| NumPy | ≥ 1.24.0 | Numerical computation |
| ReportLab | — | PDF generation |

### Frontend

| Technology | Version | Purpose |
|:---|:---|:---|
| React | 19.2.0 | UI framework |
| TanStack Router | 1.168.25 | File-based routing |
| TanStack React Query | 5.83.0 | Server state management |
| Vite | 7.3.1 | Build tool & dev server |
| Tailwind CSS | 4.2.1 | Utility-first styling |
| Radix UI | latest | Accessible UI primitives |
| Recharts | 2.15.4 | Data visualization |
| Lucide React | 0.575.0 | Icon library |
| Axios | 1.16.1 | HTTP client |
| Zod | 3.24.2 | Schema validation |
| jsPDF | 4.2.1 | Client-side PDF export |
| html2canvas | 1.4.1 | HTML-to-canvas rendering |

### System Atlas

| Technology | Purpose |
|:---|:---|
| Next.js | Observability portal framework |
| Tailwind CSS | Styling |

### Infrastructure

| Technology | Purpose |
|:---|:---|
| Docker Compose | Multi-container orchestration |
| Supabase | PostgreSQL + Storage + Row-Level Security |
| Groq Cloud | LLM inference API |

---

## 17. Technical Debt & Roadmap

### Current Technical Debt

| Item | Status | Action |
|:---|:---|:---|
| Deprecated endpoint stubs (`imaging.py`, `labs.py`, `investigation.py`) | Retained with `@deprecated` flags | Keep for backwards compatibility with E2E tests |
| Missing index on `investigation_recommendations(intake_id)` | Open | Add index to speed up patient workstation loading |
| React 19 + TanStack configuration obsolete packages | Cleaned | Completed |

### Future Roadmap Considerations
- Authentication & RBAC (role-based access control) per persona
- Real-time WebSocket push for command center updates
- Multi-hospital federation support
- ECG waveform analysis engine
- Blood gas (ABG) interpretation engine
- Integration with HL7 FHIR standards

---

## 18. Version History

| Version | Phase | Key Additions |
|:---|:---|:---|
| **v1.0** | Prototype | Basic intake, NLP extraction, risk scoring, clinical reasoning layer, PDF generation |
| **v2.0** | Core Intelligence | 13-disease YAML knowledge base, demographic reference ranges, 5 clinical scoring engines, 20-scenario regression suite |
| **v3.0** | Hospital Platform | ED Command Center, clinical search, longitudinal trajectory analysis, multi-visit delta engine |
| **v4.0** | Intelligence Platform | Explainability explorer, evidence tree, investigation workflow, resource recommendation engine |
| **v5.0** | Copilot & Observability | Evidence-Aware Clinical & System Copilot (8 intents), System Atlas, demo mode, guided tour, recruiter mode, platform metrics |

---

> [!NOTE]
> **Source Documentation**: This PRD was compiled from the following project documents:
> - [README.md](file:///d:/pratham/README.md) — Main project README
> - [Architecture.md](file:///d:/pratham/docs/Architecture.md) — Platform architecture specification
> - [API_Reference.md](file:///d:/pratham/docs/API_Reference.md) — Complete API catalog
> - [PRATHAM_v4_Architecture.md](file:///d:/pratham/PRATHAM_v4_Architecture.md) — v4 architecture specification
> - [PRATHAM_Copilot_Architecture.md](file:///d:/pratham/PRATHAM_Copilot_Architecture.md) — Copilot architecture specification
> - [Production_Reality_Audit.md](file:///d:/pratham/Production_Reality_Audit.md) — Module implementation audit
> - [Performance_Report.md](file:///d:/pratham/Performance_Report.md) — Performance benchmarks
> - [Security_Audit_Report.md](file:///d:/pratham/Security_Audit_Report.md) — Security posture evaluation
> - [Clinical_Validation_Report.md](file:///d:/pratham/Clinical_Validation_Report.md) — Validation summary
> - [clinical_score_validation.md](file:///d:/pratham/clinical_score_validation.md) — Score engine validation
> - [PRATHAM_v2_Regression_Report.md](file:///d:/pratham/PRATHAM_v2_Regression_Report.md) — 20-scenario regression audit
> - [Production_Technical_Debt_Report.md](file:///d:/pratham/Production_Technical_Debt_Report.md) — Technical debt report
> - [Clinical_Workflow_Guide.md](file:///d:/pratham/Clinical_Workflow_Guide.md) — Emergency workflow guide
> - [Deployment_Checklist.md](file:///d:/pratham/Deployment_Checklist.md) — Production deployment checklist
> - [Interview_Guide.md](file:///d:/pratham/docs/Interview_Guide.md) — Technical interview guide
> - [FAQ.md](file:///d:/pratham/docs/FAQ.md) — Frequently asked questions
