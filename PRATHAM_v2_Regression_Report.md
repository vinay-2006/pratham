# PRATHAM v2 Core Clinical Intelligence — Regression Audit Report

This report documents the end-to-end regression validation performed across 20 distinct clinical profiles following the expansion of the Declarative Knowledge Base to 13 emergency condition YAMLs.

---

## Scenario Verification Matrix

| ID | Clinical Profile | Top Calculated Condition | Status | Evidence Completeness | Subsystem Agreement |
| :-: | :--- | :--- | :-: | :-: | :-: |
| **01** | Healthy Adult Baseline | Baseline / No Acute Risk | **PASS** | 100% | HIGH |
| **02** | Routine Checkup Baseline | Baseline Routine Panel | **PASS** | 100% | HIGH |
| **03** | Community Acquired Pneumonia | Pneumonia | **PASS** | 100% | HIGH |
| **04** | Acute Coronary Syndrome | Acute Coronary Syndrome | **PASS** | 100% | HIGH |
| **05** | Heart Failure Exacerbation | Heart Failure Exacerbation | **PASS** | 100% | HIGH |
| **06** | Pulmonary Embolism | Pulmonary Embolism | **PASS** | 100% | HIGH |
| **07** | Acute Ischemic Stroke | Stroke | **PASS** | 100% | HIGH |
| **08** | Systemic Inflammatory Response | Sepsis | **PASS** | 100% | HIGH |
| **09** | Septic Shock Profile | Septic Shock / Sepsis | **PASS** | 100% | HIGH |
| **10** | Acute Asthma Exacerbation | Asthma / Resp Distress | **PASS** | 100% | HIGH |
| **11** | COPD Exacerbation | COPD / Resp Distress | **PASS** | 100% | HIGH |
| **12** | Hemorrhagic Shock / Trauma | Hemorrhagic Shock | **PASS** | 100% | HIGH |
| **13** | Diabetic Ketoacidosis (DKA) | DKA | **PASS** | 100% | HIGH |
| **14** | Severe Hypoglycemia | Neuroglycopenia / Seizure | **PASS** | 100% | HIGH |
| **15** | Acute Kidney Injury (AKI) | AKI | **PASS** | 100% | HIGH |
| **16** | Electrolyte Disorder (Hyperkalemia) | Hyperkalemia / AKI | **PASS** | 100% | HIGH |
| **17** | Urinary Tract Infection (Urosepsis) | Sepsis | **PASS** | 100% | HIGH |
| **18** | Conflicting Evidence Profile | ACS (with conflict flag) | **PASS** | 100% | MODERATE |
| **19** | Sparse Data Profile | ACS / Low Confidence | **PASS** | 40% | INSUFFICIENT DATA |
| **20** | Missing Modalities Profile | ACS | **PASS** | 60% | MODERATE |

---

## Regression Summary
- **Total Test Cases**: 20
- **Passed**: 20
- **Regression Rate**: **0.0%**
- **System Integrity**: **PASS (100%)**
