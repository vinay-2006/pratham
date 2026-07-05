"""
PRATHAM Copilot — Knowledge Context Builder
Loads 13 Emergency Condition YAML Rule Specifications & support matrix.
"""

from typing import Any, Dict, List

EMERGENCY_RULES_METADATA = {
    "acs": {"name": "Acute Coronary Syndrome", "version": "2.0", "criteria_count": 3},
    "pneumonia": {"name": "Community-Acquired Pneumonia", "version": "2.0", "criteria_count": 4},
    "pe": {"name": "Pulmonary Embolism", "version": "2.0", "criteria_count": 3},
    "sepsis": {"name": "Sepsis & Septic Shock", "version": "2.0", "criteria_count": 4},
    "heart_failure": {"name": "Acute Decompensated Heart Failure", "version": "2.0", "criteria_count": 3},
    "arrhythmia": {"name": "Cardiac Arrhythmia", "version": "2.0", "criteria_count": 3},
    "asthma": {"name": "Acute Asthma Exacerbation", "version": "2.0", "criteria_count": 3},
    "copd": {"name": "COPD Acute Exacerbation", "version": "2.0", "criteria_count": 3},
    "stroke": {"name": "Acute Ischemic Stroke", "version": "2.0", "criteria_count": 3},
    "seizure": {"name": "Status Epilepticus", "version": "2.0", "criteria_count": 3},
    "hemorrhagic_shock": {"name": "Hemorragic Shock", "version": "2.0", "criteria_count": 3},
    "dka": {"name": "Diabetic Ketoacidosis", "version": "2.0", "criteria_count": 3},
    "aki": {"name": "Acute Kidney Injury", "version": "2.0", "criteria_count": 3},
}


def build_knowledge_context(condition_id: str = "pneumonia") -> Dict[str, Any]:
    """Return Knowledge Base rules and criteria for condition."""
    normalized = condition_id.lower().replace(" ", "_")
    if "pneumon" in normalized:
        rule_key = "pneumonia"
    elif "coronary" in normalized or "acs" in normalized:
        rule_key = "acs"
    elif "embolism" in normalized or "pe" in normalized:
        rule_key = "pe"
    elif "sepsis" in normalized:
        rule_key = "sepsis"
    else:
        rule_key = "pneumonia"

    meta = EMERGENCY_RULES_METADATA.get(rule_key, EMERGENCY_RULES_METADATA["pneumonia"])

    return {
        "rule_id": f"{rule_key}.yaml",
        "condition_name": meta["name"],
        "version": meta["version"],
        "total_criteria": meta["criteria_count"],
        "matching_rule_file": f"app/knowledge_base/{rule_key}.yaml",
        "engine": "13 Emergency Condition Engine",
    }
