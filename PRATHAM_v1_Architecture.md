# PRATHAM v1 Technical Architecture Specification

## 1. System Overview

PRATHAM (Predictive Risk & Automated Triage Hospital Assistance Matrix) v1 is a clinical decision-support system designed for emergency intake, triage, and multi-modal clinical intelligence.

```text
               Patient Intake Data (Vitals, Symptoms, Notes)
                                     │
                                     ▼
                          Visit Classifier Service
                    (Routine Checkup vs. Emergency)
                                     │
                                     ▼
                      Independent Subsystem AI Processing
                 ┌───────────────────┼───────────────────┐
                 ▼                   ▼                   ▼
            NLP Engine          Lab Engine        Imaging Engine
                 │                   │                   │
                 └───────────────────┼───────────────────┘
                                     │
                                     ▼
                          Clinical Reasoning Layer
                  (Facts Extraction → Auditable Derivations)
                                     │
                                     ▼
                        Grounded LLM Interpreter
                                     │
                                     ▼
                         Unified 17-Section Report DTO
```

---

## 2. Core Subsystems & Components

### 2.1 Visit Classifier (`visit_classifier.py`)
- Distinguishes routine health checkups from acute emergency intakes.
- **Routine Panel**: Automatically recommends CBC, Basic Metabolic Panel, Blood Glucose, and Urinalysis without ordering unnecessary emergency imaging.

### 2.2 Investigation Registry & Recommendation (`investigation_registry.py`, `investigation_service.py`)
- Normalizes raw investigation queries to canonical names via comprehensive alias mapping.
- Recommends pathway-gated investigations (Cardiac, Respiratory, Trauma, Neurological) based on symptom presence and risk thresholds.
- Enforces UI safety: hides `Run Analysis` for unsupported investigations and displays `"Analysis not available in this version"`.

### 2.3 Clinical Reasoning Layer (`clinical_reasoning_service.py`)
- **Layer 1 (Facts)**: Pure extraction of structured data (Vitals, Symptoms, NLP flags, Lab, Imaging).
- **Layer 2 (Conclusions)**: Deterministic derivations (Multi-factor clinical confidence, subsystem agreement, uncertainty reasons, ranking justifications, monitoring priorities, precautions, limitations).

### 2.4 Multi-Factor Clinical Confidence Scale
- `>= 95%`: `VERY HIGH`
- `85% - 94%`: `HIGH`
- `65% - 84%`: `MODERATE`
- `< 65%`: `LOW`
- Multi-factor caps are automatically applied when sparse data sources (< 3 active sources) or subsystem disagreements are present.

### 2.5 PDF Generator (`pdf_generator.py`)
- ReportLab-based PDF generation matching the 17-section structure of the web UI.
- Restricts ML model names strictly to **Section 17 (System Information & Disclaimer)**.

---

## 3. Data Integrity & Security Boundaries

1. **Deterministic Reasoning**: All risk scores, confidence levels, and evidence summaries are calculated strictly by auditable Python engines. The LLM never computes clinical values.
2. **Patient Data Privacy**: Intakes and patient records are stored with row-level security policies in Supabase.
