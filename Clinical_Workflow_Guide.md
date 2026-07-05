# PRATHAM Emergency Clinical Workflow Guide

## Operational Overview
PRATHAM provides end-to-end decision support across four primary clinical touchpoints in the emergency department workflow.

---

## Workflow Touchpoints

### 1. In-Transit Nurse Intake (`/nurse/intake`)
- **Action**: Nurse enters incoming patient demographics, vitals, symptoms, and chief complaint.
- **Output**: Initial risk categorization, vital anomaly warnings, and preliminary triage level assignment.

### 2. Smart Triage & Operational Command Center (`/command-center`)
- **Action**: Charge nurse monitors real-time ER acuity distribution and active patient load.
- **Output**: Prioritized triage queue, recommended facility units (e.g., Cath Lab, ICU Bed Standby), and equipment callouts.

### 3. Physician Workstation & Approvals (`/doctor/review`, `/doctor/approvals`)
- **Action**: Attending physician reviews intake findings, imaging overlays (EfficientNetB0 Grad-CAM), lab analytes, and clinical scores.
- **Output**: Doctor approves or adjusts AI recommendations, generating a finalized grounded clinical report.

### 4. Longitudinal Trajectory & Case Comparison (`/comparison`, `/explainability`)
- **Action**: Clinician inspects patient's historical visit deltas (e.g. Visit 1 Pneumonia vs Visit 2 PE) and reviews the diagnostic evidence tree.
- **Output**: Clear visibility into physiological trends, rule agreement matrices, and missing evidence callouts.

---

## Standard Emergency Protocols Handled
- **Acute Coronary Syndrome (ACS)**: Stat ECG within 10 min, serial troponin tracking, HEART score evaluation.
- **Sepsis & Septic Shock**: qSOFA and NEWS2 scoring, lactate elevation warnings, blood culture reminders.
- **Community-Acquired Pneumonia**: CURB-65 calculation, CXR consolidation detection, severity stratification.
- **Pulmonary Embolism**: Wells PE score calculation, D-Dimer interpretation, CTPA recommendation.
- **Acute Ischemic Stroke**: NIHSS deficit mapping, non-contrast head CT protocol, thrombolytic window alert.
