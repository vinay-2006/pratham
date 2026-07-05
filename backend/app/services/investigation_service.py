"""
Investigation Service — Tightened rule-based investigation recommendations.

Key design decisions:
- Removed "universal for all emergencies" block entirely
- Each pathway has strict symptom gates
- Advanced tests only unlock at higher risk thresholds
- Minimum safety net only fires if nothing else triggered AND patient is critical
"""

from __future__ import annotations


from app.services.visit_classifier import get_routine_investigations


def recommend_investigations(
    symptoms: dict,
    vitals: dict,
    nlp_flags: dict,
    risk_scores: dict,
    is_routine: bool = False,
) -> list[str]:
    """
    Rule-based investigation recommendations.
    Returns a sorted list of investigation names.

    If is_routine is True (Routine Clinical Checkup):
    - Recommends baseline panel: CBC, Basic Metabolic Panel, Blood Glucose, Urinalysis
    - Recommends 0 imaging tests
    - Never triggers emergency pathways
    """
    if is_routine:
        return sorted(get_routine_investigations())

    investigations: set[str] = set()

    # Check whether vitals data actually exists
    _vitals_present = any(
        vitals.get(k) is not None and vitals.get(k) != 0
        for k in ("heart_rate", "spo2", "bp_systolic", "bp_diastolic", "temperature", "respiratory_rate")
    )

    spo2 = vitals.get("spo2")
    hr = vitals.get("heart_rate") or 0

    # ── CARDIAC PATHWAY ──────────────────────────────────────────────────
    # Trigger only if chest pain present or strong cardiac flag
    if symptoms.get("chest_pain") or nlp_flags.get("cardiac_risk_flag"):
        investigations.update(["ECG", "Troponin", "CBC"])
        if risk_scores["cardiac_risk"] >= 60:
            investigations.add("Echocardiogram")
            investigations.add("Cardiac Enzymes")

    # ── RESPIRATORY PATHWAY ──────────────────────────────────────────────
    # Trigger only if breathlessness or low SpO2 (only when spo2 is actually measured)
    if symptoms.get("breathlessness") or (spo2 is not None and spo2 < 94):
        investigations.add("Chest X-ray")
        if spo2 is not None and spo2 < 90:
            investigations.add("ABG")
        if risk_scores["respiratory_risk"] >= 70:
            investigations.add("CT Chest")
            investigations.add("D-Dimer")

    # ── TRAUMA PATHWAY ───────────────────────────────────────────────────
    # Trigger only if trauma or bleeding explicitly present
    if symptoms.get("trauma") or symptoms.get("bleeding"):
        investigations.update([
            "CBC",
            "Coagulation Profile",
            "Blood Group & Cross-match",
        ])
        if risk_scores["trauma_risk"] >= 60:
            investigations.add("FAST Ultrasound")

    # ── NEUROLOGICAL PATHWAY ─────────────────────────────────────────────
    # Trigger only if unconscious or neuro symptoms
    if symptoms.get("unconsciousness") or symptoms.get("neurological_symptoms"):
        investigations.update([
            "CT Brain",
            "Blood Glucose",
            "Electrolytes",
        ])
        if nlp_flags.get("head_trauma"):
            investigations.add("CT Cervical Spine")

    # ── MINIMUM SAFETY NET ───────────────────────────────────────────────
    # Only for truly critical patients with NO pathway triggered AND vitals present
    if not investigations and risk_scores["overall_severity"] == "critical" and _vitals_present:
        investigations.update(["CBC", "Blood Glucose", "ECG"])

    return sorted(investigations)
