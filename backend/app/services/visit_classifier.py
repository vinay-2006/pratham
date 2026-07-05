"""
Visit Classifier Service — Classifies emergency intakes into 'routine' or 'emergency'.
"""

from __future__ import annotations

ROUTINE_PHRASES = [
    "routine checkup",
    "annual checkup",
    "annual health examination",
    "preventive health screening",
    "routine evaluation",
    "medical fitness examination",
    "pre-employment medical examination",
    "no complaints",
    "asymptomatic",
    "general checkup",
    "routine screening",
    "periodic health",
    "wellness check",
    "checkup",
    "check-up",
]

def classify_visit(symptoms: dict, vitals: dict, severity: str, description: str | None, chief_complaint: str | None = None) -> str:
    """
    Classifies a patient intake. Returns 'routine' or 'emergency'.
    A visit is classified as 'routine' only if:
    1. Vital signs are within normal limits.
    2. No significant symptoms are present (all symptom values are False or None).
    3. Overall severity is LOW.
    4. Chief complaint or emergency description clearly indicates a routine evaluation.
    """
    # 1. Check symptoms
    if any(symptoms.get(k) is True for k in symptoms):
        return "emergency"

    # 2. Check overall severity
    if severity.lower() != "low":
        return "emergency"

    # 3. Check vitals (normal limits)
    hr = vitals.get("heart_rate")
    if hr is not None and hr != 0:
        if hr < 50 or hr > 100:
            return "emergency"

    spo2 = vitals.get("spo2")
    if spo2 is not None and spo2 != 0:
        if spo2 < 95:
            return "emergency"

    bp_sys = vitals.get("bp_systolic")
    if bp_sys is not None and bp_sys != 0:
        if bp_sys < 90 or bp_sys >= 140:
            return "emergency"

    bp_dia = vitals.get("bp_diastolic")
    if bp_dia is not None and bp_dia != 0:
        if bp_dia < 50 or bp_dia >= 90:
            return "emergency"

    rr = vitals.get("respiratory_rate")
    if rr is not None and rr != 0:
        if rr < 12 or rr > 20:
            return "emergency"

    temp = vitals.get("temperature")
    if temp is not None and temp != 0:
        if temp > 45: # Fahrenheit
            if temp > 100.0:
                return "emergency"
        else: # Celsius
            if temp > 37.8:
                return "emergency"

    # 4. Check description and chief complaint
    desc = f"{chief_complaint or ''} {description or ''}".strip().lower()
    if not desc:
        return "emergency"

    # Check for routine intent
    keywords = ["routine", "checkup", "check-up", "check up", "annual", "health check", "screening", "medical examination", "fitness", "wellness", "asymptomatic", "no complaints"]
    has_routine_keyword = any(kw in desc for kw in keywords)

    if has_routine_keyword or any(phrase in desc for phrase in ROUTINE_PHRASES):
        return "routine"

    return "emergency"

def get_routine_investigations() -> list[str]:
    """Return the baseline panel for routine checkups."""
    return [
        "CBC",
        "Basic Metabolic Panel",
        "Urinalysis",
        "Blood Glucose",
    ]
