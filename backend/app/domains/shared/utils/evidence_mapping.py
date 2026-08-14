"""
PRATHAM Shared Evidence Mapping Utility

Single source of truth for the investigation_type → evidence_type mapping.

Previously defined in app/api/evidence.py. Moved here so that both
api/evidence.py and api/investigations.py can import from a shared location
without creating an API-to-API dependency.

Domain Ownership: shared (cross-cutting)
Layer: domains/shared/utils  ← correct layer for pure mapping functions
No HTTP concerns, no database access, no side effects.
"""

from __future__ import annotations


# ── Investigation → Evidence type mapping ─────────────────────────────────────
# Backend is the single source of truth. Frontend receives evidence_type from
# the backend and never performs this mapping itself.

INVESTIGATION_EVIDENCE_MAP: dict[str, str] = {
    # ECG
    "ECG": "ecg",
    "EKG": "ecg",
    "Electrocardiogram": "ecg",
    "12-Lead ECG": "ecg",
    # Imaging
    "Chest X-ray": "xray",
    "Chest X Ray": "xray",
    "Chest Xray": "xray",
    "X-ray": "xray",
    "CT Brain": "xray",
    "CT Chest": "xray",
    "CT Scan": "xray",
    "CT Angiography": "xray",
    "CTPA": "xray",
    "MRI": "xray",
    "Ultrasound": "xray",
    "FAST scan": "xray",
    "FAST Scan": "xray",
    "Echo": "xray",
    "Echocardiogram": "xray",
    # Lab reports
    "Troponin": "lab_report",
    "CBC": "lab_report",
    "ABG": "lab_report",
    "D-Dimer": "lab_report",
    "BMP": "lab_report",
    "Basic Metabolic Panel": "lab_report",
    "CMP": "lab_report",
    "BNP": "lab_report",
    "NT-proBNP": "lab_report",
    "LFT": "lab_report",
    "RFT": "lab_report",
    "Serum Electrolytes": "lab_report",
    "Blood Glucose": "lab_report",
    "Blood Culture": "lab_report",
    "Urine Analysis": "lab_report",
    "Urinalysis": "lab_report",
    "Urine Culture": "lab_report",
    "Coagulation": "lab_report",
    "PT/INR": "lab_report",
    "Prothrombin Time": "lab_report",
    "CRP": "lab_report",
    "Procalcitonin": "lab_report",
    "Lactate": "lab_report",
    "Lipase": "lab_report",
    "Amylase": "lab_report",
    "Cortisol": "lab_report",
    "Thyroid Function": "lab_report",
    "TSH": "lab_report",
    "Blood Group": "lab_report",
    "Crossmatch": "lab_report",
    "Cardiac Enzymes": "lab_report",
}


def get_evidence_type(investigation_type: str) -> str:
    """
    Map an investigation_type string to a valid evidence_type.
    Falls back to keyword matching, then 'clinical_notes'.

    Pure function — no side effects, no database access.
    """
    if not investigation_type:
        return "clinical_notes"

    # Exact match
    mapped = INVESTIGATION_EVIDENCE_MAP.get(investigation_type)
    if mapped:
        return mapped

    # Fuzzy keyword matching
    lower = investigation_type.lower()
    if any(k in lower for k in ("x-ray", "xray", "ct", "mri", "scan", "imaging", "ultrasound", "echo", "angio")):
        return "xray"
    if any(k in lower for k in ("ecg", "ekg", "electrocardiogram")):
        return "ecg"
    if any(k in lower for k in ("blood", "lab", "serum", "urine", "culture", "level", "count", "troponin", "enzyme")):
        return "lab_report"

    return "clinical_notes"
