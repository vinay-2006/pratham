# Reference Range Engine Demographic Validation Report

This document validates the demographic-aware analyte evaluation matrix (`reference_range_service.py`) across Male, Female, Pediatric, and Elderly age groups.

---

## Analyte Evaluation Matrix

| Analyte | Demographic | Value | Reference Interval | Evaluated Status | Evaluated Severity | Clinical Significance | Result |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| **Troponin** | Adult Male | 0.84 ng/mL | <0.04 ng/mL | HIGH | CRITICAL | Indicates myocardial injury | **PASS** |
| **Troponin** | Adult Female | 0.02 ng/mL | <0.04 ng/mL | NORMAL | NORMAL | Normal baseline cardiac marker | **PASS** |
| **Hemoglobin**| Adult Male | 11.0 g/dL | 13.8–17.2 g/dL | LOW | ABNORMAL | Indicates anemia | **PASS** |
| **Hemoglobin**| Adult Female | 13.0 g/dL | 12.1–15.1 g/dL | NORMAL | NORMAL | Normal clinical finding | **PASS** |
| **Hemoglobin**| Pediatric | 9.5 g/dL | 11.0–16.0 g/dL | LOW | ABNORMAL | Indicates pediatric anemia | **PASS** |
| **Creatinine** | Adult Male | 1.8 mg/dL | 0.74–1.35 mg/dL | HIGH | ABNORMAL | Indicates renal impairment | **PASS** |
| **Creatinine** | Elderly | 1.1 mg/dL | 0.60–1.20 mg/dL | NORMAL | NORMAL | Normal clinical finding for elderly | **PASS** |
| **Creatinine** | Adult | 3.5 mg/dL | 0.60–1.20 mg/dL | HIGH | CRITICAL | Severe acute kidney injury (AKI) | **PASS** |
| **WBC** | Pediatric | 18.0 10^3/µL | 5.0–15.0 10^3/µL | HIGH | ABNORMAL | Leukocytosis / inflammation | **PASS** |
| **WBC** | Adult | 14.5 10^3/µL | 4.5–11.0 10^3/µL | HIGH | ABNORMAL | Systemic infection / leukocytosis | **PASS** |
| **Glucose** | Adult | 45.0 mg/dL | 70.0–99.0 mg/dL | LOW | CRITICAL | Severe hypoglycemia risk | **PASS** |
| **Potassium** | Adult | 6.8 mEq/L | 3.5–5.0 mEq/L | HIGH | CRITICAL | Hyperkalemia — dysrhythmia risk | **PASS** |

---

## Validation Summary
- **Total Demographic Matrix Scenarios**: 12
- **Pass Rate**: 100%
