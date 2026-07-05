# PRATHAM v4 Architecture Specification: Intelligent Hospital Platform

## Overview
PRATHAM (Predictive Risk & Automated Triage Hospital Assistance Matrix) v4 transforms individual emergency intake processing into an emergency department-wide hospital intelligence platform.

---

## Architecture Blueprint

```text
                                Hospital Intake & Monitor Data
                                              │
                                              ▼
                        Layer 1: Clinical Context & Demographic Engine
                        (Baseline Creatinine, Age/Sex Adjustments)
                                              │
                                              ▼
                        Layer 2: Demographic Reference Range Engine
                        (Qualitative Findings: HIGH, LOW, CRITICAL)
                                              │
                                              ▼
                    Layer 3: Generic Lab & EfficientNetB0 Imaging Engine
                        (Image Infiltration, Multi-Panel Analytes)
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
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
       Emergency Command Center                            Longitudinal Delta & Explorer
    (Active ER Cases, Resource Recs)                    (Visit 1 vs 2, Explainability Tree)
```

---

## Subsystem Inventory

### 1. ED Command Center Telemetry Engine (`command_center_service.py`)
- Calculates real-time active ER case counts, acuity distribution, and smart triage queue rankings.
- Emits operational facility recommendations (e.g. ICU bed, Cath lab, 12-lead ECG, blood crossmatch) without prescribing medications.

### 2. Clinical Search & Filter Engine (`clinical_search_service.py`)
- Performs structured keyword and regex query matching across intake chief complaints, clinical findings, and intake IDs.

### 3. Diagnostic Evidence Tree & Rule Agreement Matrix (`explainability_service.py`)
- Maps supportive vs. conflicting clinical evidence weights and calculates rule match statuses across independent reasoning engines.

### 4. Longitudinal Trajectory & Analyte Delta Engine (`trend_analysis_service.py`)
- Computes comparative physiological deltas between historical visits (e.g., SpO₂ 88% → 96% Improved, Creatinine 0.9 → 1.4 mg/dL AKI Stage 1).

### 5. Multi-Visit Patient Trajectory Seeder (`seed_multivisit_patients.py`)
- Generates realistic multi-visit patient histories in Supabase/SQL for testing longitudinal decompensation detection.

---

## Compliance & Operational Safeguards
1. **No Prescriptive Language**: Operational recommendations state equipment and facility unit needs, avoiding specific medication names or treatment orders.
2. **Clinical Audit Logging**: Every generated report logs `clinical_audit_log` metadata containing pipeline stage latencies, execution timestamps, and subsystem version tags.
3. **Deterministic Score Integrity**: Clinical calculators (NEWS2, qSOFA, CURB-65, HEART, Wells) execute purely in Python without LLM arithmetic dependency.
