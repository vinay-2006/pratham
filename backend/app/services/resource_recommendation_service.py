"""
resource_recommendation_service.py — Operational Facility Resource Engine

Recommends non-treatment operational facility resources (equipment, monitoring setups, isolation rooms)
using observational clinical language.
"""

from __future__ import annotations
from typing import Any, Dict, List


def recommend_operational_resources(
    vitals: Dict[str, Any],
    symptoms: Dict[str, Any] | List[str],
    risk_scores: Dict[str, Any] | None = None,
) -> List[Dict[str, str]]:
    """
    Evaluates clinical parameters to suggest operational facility equipment and monitoring setups.
    """
    resources: List[Dict[str, str]] = []
    sym_dict = symptoms if isinstance(symptoms, dict) else {s: True for s in symptoms}

    spo2 = vitals.get("spo2")
    hr = vitals.get("heart_rate")
    temp = vitals.get("temperature")

    # 1. Supplemental Oxygen Setup
    if (spo2 is not None and 0 < spo2 < 94) or sym_dict.get("breathlessness"):
        resources.append({
            "resource_name": "Supplemental Oxygen Setup",
            "category": "equipment",
            "rationale": "Indicated for hypoxemia (SpO₂ <94%) or dyspnea presentation",
        })

    # 2. Cardiac Telemetry / ECG Setup
    if (hr is not None and (hr > 100 or hr < 50)) or sym_dict.get("chest_pain"):
        resources.append({
            "resource_name": "Cardiac Telemetry Setup",
            "category": "monitoring",
            "rationale": "Indicated for chest pain or heart rate deviation",
        })

    # 3. Isolation Room / Infection Control Setup
    if temp is not None and (temp > 38.5 or (temp > 45 and (temp - 32) * 5 / 9 > 38.5)):
        resources.append({
            "resource_name": "Infection Control / Isolation Setup",
            "category": "facility",
            "rationale": "Indicated for high fever presentation",
        })

    # 4. Portable Imaging Unit
    if sym_dict.get("trauma") or (spo2 is not None and 0 < spo2 < 90):
        resources.append({
            "resource_name": "Portable Imaging Unit",
            "category": "equipment",
            "rationale": "Indicated for bedside assessment in severe distress or trauma",
        })

    # 5. High-Acuity Evaluation
    if (risk_scores and risk_scores.get("overall_severity") == "critical") or (spo2 is not None and 0 < spo2 < 90):
        resources.append({
            "resource_name": "High-Acuity Critical Care Evaluation",
            "category": "facility",
            "rationale": "Critical care resources may be required based on risk scores",
        })

    return resources
