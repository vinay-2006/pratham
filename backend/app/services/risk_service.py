"""
Risk Service — Rule-based weighted scoring for each clinical risk category.
"""

from __future__ import annotations


def calculate_risk_scores(vitals: dict, symptoms: dict, nlp_flags: dict) -> dict:
    """
    Rule-based weighted scoring for each risk category.
    Returns scores 0-100 and overall severity.
    """
    cardiac = 0
    respiratory = 0
    trauma = 0
    neurological = 0

    # ── Cardiac risk scoring ──────────────────────────────────────────────
    if symptoms.get("chest_pain"):
        cardiac += 30
    if nlp_flags.get("cardiac_risk_flag"):
        cardiac += 20
    hr = vitals.get("heart_rate") or 0
    if hr > 120:
        cardiac += 20
    elif hr > 100:
        cardiac += 10
    bp_sys = vitals.get("bp_systolic") or 0
    if bp_sys > 160:
        cardiac += 15
    elif bp_sys > 140:
        cardiac += 8
    if bp_sys < 90 and bp_sys > 0:
        cardiac += 25

    # ── Respiratory risk scoring ──────────────────────────────────────────
    if symptoms.get("breathlessness"):
        respiratory += 25
    if nlp_flags.get("respiratory_distress"):
        respiratory += 20
    spo2 = vitals.get("spo2") or 100
    if spo2 < 90:
        respiratory += 30
    elif spo2 < 94:
        respiratory += 15
    rr = vitals.get("respiratory_rate") or 0
    if rr > 25:
        respiratory += 15
    elif rr > 20:
        respiratory += 8

    # ── Trauma risk scoring ───────────────────────────────────────────────
    if symptoms.get("trauma"):
        trauma += 35
    if symptoms.get("bleeding"):
        trauma += 25
    if nlp_flags.get("trauma_present"):
        trauma += 20
    if nlp_flags.get("hemorrhage_risk"):
        trauma += 20

    # ── Neurological risk scoring ─────────────────────────────────────────
    if symptoms.get("unconsciousness"):
        neurological += 40
    if symptoms.get("neurological_symptoms"):
        neurological += 25
    if nlp_flags.get("head_trauma"):
        neurological += 20
    if nlp_flags.get("loss_of_consciousness"):
        neurological += 20
    if nlp_flags.get("neurological_risk_flag"):
        neurological += 15

    # Cap at 100
    cardiac = min(cardiac, 100)
    respiratory = min(respiratory, 100)
    trauma = min(trauma, 100)
    neurological = min(neurological, 100)

    # Overall severity based on highest risk
    max_score = max(cardiac, respiratory, trauma, neurological)
    if max_score >= 70:
        severity = "critical"
    elif max_score >= 50:
        severity = "high"
    elif max_score >= 30:
        severity = "moderate"
    else:
        severity = "low"

    return {
        "cardiac_risk": cardiac,
        "respiratory_risk": respiratory,
        "trauma_risk": trauma,
        "neurological_risk": neurological,
        "overall_severity": severity,
    }


def generate_preparation_alerts(risk_scores: dict) -> list[str]:
    """
    Generate hospital preparation alerts based on risk scores.
    """
    alerts: list[str] = []
    if risk_scores["cardiac_risk"] >= 50:
        alerts.append("icu_standby")
    if risk_scores["respiratory_risk"] >= 40:
        alerts.append("oxygen_prep")
    if risk_scores["trauma_risk"] >= 40:
        alerts.append("trauma_team")
    if risk_scores["neurological_risk"] >= 50 or risk_scores["trauma_risk"] >= 50:
        alerts.append("ct_scanner")
    if risk_scores["overall_severity"] in ("high", "critical"):
        alerts.append("emergency_bed")
    if risk_scores["trauma_risk"] >= 60:
        alerts.append("blood_bank")
    return alerts
