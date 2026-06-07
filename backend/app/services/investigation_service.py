"""
Investigation Service — Rule-based investigation recommendations.

Different patients get different tests based on their actual clinical
presentation (symptoms, vitals, NLP flags, risk scores).
"""

from __future__ import annotations


def recommend_investigations(
    symptoms: dict, vitals: dict, nlp_flags: dict, risk_scores: dict
) -> list[str]:
    """
    Rule-based investigation recommendations.
    Returns a sorted list of investigation names.
    """
    investigations: set[str] = set()

    # ── Cardiac pathway ───────────────────────────────────────────────────
    if (
        symptoms.get("chest_pain")
        or nlp_flags.get("cardiac_risk_flag")
        or risk_scores["cardiac_risk"] >= 40
    ):
        investigations.update(["ECG", "Troponin", "CBC"])
        if risk_scores["cardiac_risk"] >= 60:
            investigations.add("Echocardiogram")
            investigations.add("Cardiac Enzymes")

    # ── Respiratory pathway ───────────────────────────────────────────────
    if symptoms.get("breathlessness") or risk_scores["respiratory_risk"] >= 40:
        investigations.add("Chest X-ray")
        spo2 = vitals.get("spo2") or 100
        if spo2 < 94:
            investigations.add("ABG")
        if risk_scores["respiratory_risk"] >= 60:
            investigations.add("CT Chest")
            investigations.add("D-Dimer")

    # ── Trauma pathway ────────────────────────────────────────────────────
    if (
        symptoms.get("trauma")
        or symptoms.get("bleeding")
        or risk_scores["trauma_risk"] >= 40
    ):
        investigations.update(["CBC", "Coagulation Profile", "Blood Group & Cross-match"])
        if risk_scores["trauma_risk"] >= 60:
            investigations.add("FAST Ultrasound")

    # ── Neurological pathway ──────────────────────────────────────────────
    if (
        symptoms.get("unconsciousness")
        or symptoms.get("neurological_symptoms")
        or nlp_flags.get("neurological_risk_flag")
    ):
        investigations.update(["CT Brain", "Blood Glucose", "Electrolytes"])
        if nlp_flags.get("head_trauma"):
            investigations.add("CT Cervical Spine")

    # ── Universal for high/critical ───────────────────────────────────────
    if risk_scores["overall_severity"] in ("high", "critical"):
        investigations.add("CBC")
        investigations.add("Renal Function Tests")
        investigations.add("Blood Glucose")

    return sorted(investigations)
