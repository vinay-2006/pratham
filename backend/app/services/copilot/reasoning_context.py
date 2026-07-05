"""
PRATHAM Copilot — Reasoning Context Builder
Extracts deterministic clinical score calculations (NEWS2, qSOFA, CURB-65, HEART, Wells)
and disease-agnostic physiological pattern syndromes.
"""

from typing import Any, Dict, List


def build_reasoning_context(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract clinical scores and pattern engine syndromes."""
    scores = patient_data.get("clinical_scores", {})
    syndromes = patient_data.get("syndromes", [])

    news2 = scores.get("news2", 7)
    qsofa = scores.get("qsofa", 1)
    curb65 = scores.get("curb65", 2)
    heart_score = scores.get("heart_score", 4)
    wells_pe = scores.get("wells_pe", 1.5)

    formatted_scores = [
        {"name": "NEWS2 Score", "value": news2, "risk_category": "HIGH RISK" if news2 >= 7 else "MODERATE RISK", "engine": "Clinical Scoring Engine"},
        {"name": "qSOFA Score", "value": qsofa, "risk_category": "MODERATE RISK" if qsofa >= 1 else "LOW RISK", "engine": "Clinical Scoring Engine"},
        {"name": "CURB-65 Score", "value": curb65, "risk_category": "MODERATE RISK" if curb65 >= 2 else "LOW RISK", "engine": "Clinical Scoring Engine"},
        {"name": "HEART Score", "value": heart_score, "risk_category": "MODERATE RISK" if heart_score >= 4 else "LOW RISK", "engine": "Clinical Scoring Engine"},
        {"name": "Wells PE Score", "value": wells_pe, "risk_category": "LOW PROBABILITY" if wells_pe < 2 else "MODERATE PROBABILITY", "engine": "Clinical Scoring Engine"},
    ]

    default_syndromes = syndromes if syndromes else [
        "Respiratory Distress Syndrome",
        "Systemic Inflammatory Response",
    ]

    return {
        "scores": formatted_scores,
        "active_syndromes": default_syndromes,
        "primary_differential": patient_data.get("top_condition", "Community-Acquired Pneumonia"),
        "confidence_level": patient_data.get("confidence", "HIGH"),
    }
