"""
PRATHAM Copilot — Patient Context Builder
Extracts patient demographics, admission context, and baseline risk factors.
"""

from typing import Any, Dict


def build_patient_context(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract patient context and demographics."""
    demographics = patient_data.get("demographics", {})
    vitals = patient_data.get("vitals", {})

    age = demographics.get("age", 45)
    sex = demographics.get("sex", "male").lower()
    is_pregnant = demographics.get("is_pregnant", False)
    chronic_conditions = demographics.get("chronic_conditions", [])

    return {
        "patient_id": patient_data.get("patient_id", "P-100"),
        "intake_id": patient_data.get("intake_id", "INT-000"),
        "age": age,
        "sex": sex,
        "is_pregnant": is_pregnant,
        "chronic_conditions": chronic_conditions,
        "chief_complaint": patient_data.get("chief_complaint", "Not specified"),
        "arrival_time": patient_data.get("arrival_time", "2026-07-05 10:00"),
        "acuity_level": patient_data.get("acuity_level", "MODERATE"),
    }
