"""
clinical_scoring_service.py — Deterministic Clinical Scoring Engine

Computes validated clinical risk scores:
- NEWS2 (National Early Warning Score 2)
- qSOFA (Quick Sequential Organ Failure Assessment)
- CURB-65 (Pneumonia Severity Score)
- HEART Score (Cardiac Risk)
- Wells Score for PE (Pulmonary Embolism Risk)
"""

from __future__ import annotations
from typing import Any, Dict
from app.services.clinical_context_service import ClinicalContext


def calculate_clinical_scores(
    vitals: Dict[str, Any],
    symptoms: Dict[str, Any] | list[str],
    patient_data: Dict[str, Any],
    lab_evaluations: list[Dict[str, Any]] | None = None,
    context: ClinicalContext | None = None,
) -> Dict[str, Any]:
    """
    Calculates deterministic clinical risk scores.
    Returns a dictionary of all computed scores.
    """
    sym_dict = symptoms if isinstance(symptoms, dict) else {s: True for s in symptoms}
    labs = {item["analyte_key"]: item for item in (lab_evaluations or []) if "analyte_key" in item}

    hr = vitals.get("heart_rate") or 0
    rr = vitals.get("respiratory_rate") or 0
    spo2 = vitals.get("spo2") or 0
    bp_sys = vitals.get("bp_systolic") or 0
    temp = vitals.get("temperature") or 0
    age = (context.age if context else 0) or patient_data.get("age") or 0

    # 1. NEWS2 CALCULATOR
    news2_score = 0
    # Respiration Rate
    if rr > 0:
        if rr <= 8 or rr >= 25: news2_score += 3
        elif 21 <= rr <= 24: news2_score += 2
        elif 9 <= rr <= 11: news2_score += 1
    # SpO2
    if spo2 > 0:
        if spo2 <= 91: news2_score += 3
        elif 92 <= spo2 <= 93: news2_score += 2
        elif 94 <= spo2 <= 95: news2_score += 1
    # Systolic BP
    if bp_sys > 0:
        if bp_sys <= 90: news2_score += 3
        elif 91 <= bp_sys <= 100: news2_score += 2
        elif 101 <= bp_sys <= 110: news2_score += 1
        elif bp_sys >= 220: news2_score += 3
    # Heart Rate
    if hr > 0:
        if hr <= 40 or hr >= 131: news2_score += 3
        elif 111 <= hr <= 130: news2_score += 2
        elif 41 <= hr <= 50 or 91 <= hr <= 110: news2_score += 1

    news2_risk = "LOW"
    if news2_score >= 7: news2_risk = "HIGH"
    elif news2_score >= 5: news2_risk = "MEDIUM"

    # 2. qSOFA CALCULATOR
    qsofa_score = 0
    if rr >= 22: qsofa_score += 1
    if bp_sys > 0 and bp_sys <= 100: qsofa_score += 1
    if sym_dict.get("unconsciousness"): qsofa_score += 1

    # 3. CURB-65 CALCULATOR
    curb65_score = 0
    if sym_dict.get("unconsciousness"): curb65_score += 1
    if "bun" in labs and labs["bun"]["value"] > 19: curb65_score += 1
    if rr >= 30: curb65_score += 1
    if bp_sys > 0 and (bp_sys < 90 or vitals.get("bp_diastolic", 100) <= 60): curb65_score += 1
    if age >= 65: curb65_score += 1

    # 4. HEART SCORE (Cardiac Risk)
    heart_score = 0
    # History
    if sym_dict.get("chest_pain"): heart_score += 1
    # Age
    if age >= 65: heart_score += 2
    elif age >= 45: heart_score += 1
    # Troponin
    if "troponin" in labs:
        if labs["troponin"]["status"] == "HIGH": heart_score += 2

    # 5. WELLS SCORE (PE Risk)
    wells_score = 0.0
    if sym_dict.get("breathlessness") and not sym_dict.get("chest_pain"): wells_score += 3.0
    if hr > 100: wells_score += 1.5
    if "d_dimer" in labs and labs["d_dimer"]["status"] == "HIGH": wells_score += 3.0

    return {
        "news2": {
            "score": news2_score,
            "risk_category": news2_risk,
            "label": "NEWS2 Score",
        },
        "qsofa": {
            "score": qsofa_score,
            "high_risk": qsofa_score >= 2,
            "label": "qSOFA Score",
        },
        "curb65": {
            "score": curb65_score,
            "mortality_risk": "High" if curb65_score >= 3 else ("Moderate" if curb65_score >= 2 else "Low"),
            "label": "CURB-65 Pneumonia Score",
        },
        "heart_score": {
            "score": heart_score,
            "mace_risk": "High" if heart_score >= 7 else ("Moderate" if heart_score >= 4 else "Low"),
            "label": "HEART Score",
        },
        "wells_pe": {
            "score": wells_score,
            "pe_probability": "High" if wells_score > 6.0 else ("Moderate" if wells_score >= 2.0 else "Low"),
            "label": "Wells PE Score",
        },
    }
