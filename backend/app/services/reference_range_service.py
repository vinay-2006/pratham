"""
reference_range_service.py — Demographic-Aware Reference Range Engine

Evaluates lab analytes against age- and sex-adjusted reference intervals.
Produces structured outputs: analyte, value, unit, reference_interval, status, severity, clinical_significance.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
from app.services.clinical_context_service import ClinicalContext

# Standard Reference Intervals (analyte -> demographic -> interval & severity boundaries)
REFERENCE_DATABASE: Dict[str, Dict[str, Any]] = {
    "troponin": {
        "unit": "ng/mL",
        "default": {"low": 0.0, "high": 0.04, "critical_high": 0.1},
        "display": "Troponin I / T",
        "significance_high": "Indicates myocardial injury or acute coronary necrosis",
        "significance_low": "Normal baseline cardiac marker",
    },
    "wbc": {
        "unit": "10^3/µL",
        "default": {"low": 4.5, "high": 11.0, "critical_high": 20.0, "critical_low": 2.0},
        "pediatric": {"low": 5.0, "high": 15.0, "critical_high": 25.0, "critical_low": 3.0},
        "display": "White Blood Cell Count",
        "significance_high": "Indicates systemic infection, inflammation, or leukocytosis",
        "significance_low": "Indicates leukopenia or bone marrow suppression",
    },
    "hemoglobin": {
        "unit": "g/dL",
        "male": {"low": 13.8, "high": 17.2, "critical_low": 7.0},
        "female": {"low": 12.1, "high": 15.1, "critical_low": 7.0},
        "pediatric": {"low": 11.0, "high": 16.0, "critical_low": 8.0},
        "default": {"low": 12.0, "high": 16.0, "critical_low": 7.0},
        "display": "Hemoglobin",
        "significance_low": "Indicates anemia or acute acute hemorrhage",
        "significance_high": "Indicates polycythemia or hemoconcentration",
    },
    "platelets": {
        "unit": "10^3/µL",
        "default": {"low": 150, "high": 450, "critical_low": 50, "critical_high": 1000},
        "display": "Platelet Count",
        "significance_low": "Thrombocytopenia — elevated bleeding risk",
        "significance_high": "Thrombocytosis — reactive or myeloproliferative state",
    },
    "creatinine": {
        "unit": "mg/dL",
        "male": {"low": 0.74, "high": 1.35, "critical_high": 3.0},
        "female": {"low": 0.59, "high": 1.04, "critical_high": 3.0},
        "elderly": {"low": 0.60, "high": 1.20, "critical_high": 3.5},
        "default": {"low": 0.60, "high": 1.20, "critical_high": 3.0},
        "display": "Serum Creatinine",
        "significance_high": "Indicates renal impairment or acute kidney injury (AKI)",
        "significance_low": "Low muscle mass or hyperfiltration",
    },
    "bun": {
        "unit": "mg/dL",
        "default": {"low": 7.0, "high": 20.0, "critical_high": 50.0},
        "elderly": {"low": 8.0, "high": 23.0, "critical_high": 60.0},
        "display": "Blood Urea Nitrogen (BUN)",
        "significance_high": "Indicates azotemia, renal dysfunction, or dehydration",
        "significance_low": "Malnutrition or severe liver dysfunction",
    },
    "glucose": {
        "unit": "mg/dL",
        "default": {"low": 70.0, "high": 99.0, "critical_low": 50.0, "critical_high": 300.0},
        "display": "Fasting / Blood Glucose",
        "significance_high": "Hyperglycemia — diabetes or acute stress response",
        "significance_low": "Hypoglycemia — severe risk of neuroglycopenia",
    },
    "sodium": {
        "unit": "mEq/L",
        "default": {"low": 135.0, "high": 145.0, "critical_low": 120.0, "critical_high": 160.0},
        "display": "Serum Sodium",
        "significance_low": "Hyponatremia — cerebral edema risk",
        "significance_high": "Hypernatremia — dehydration or diabetes insipidus",
    },
    "potassium": {
        "unit": "mEq/L",
        "default": {"low": 3.5, "high": 5.0, "critical_low": 2.8, "critical_high": 6.5},
        "display": "Serum Potassium",
        "significance_high": "Hyperkalemia — high risk of cardiac dysrhythmias",
        "significance_low": "Hypokalemia — risk of cardiac irritability and weakness",
    },
    "d_dimer": {
        "unit": "µg/mL FEU",
        "default": {"low": 0.0, "high": 0.5, "critical_high": 2.0},
        "elderly": {"low": 0.0, "high": 0.7, "critical_high": 2.5},
        "display": "D-Dimer",
        "significance_high": "Elevated fibrin degradation — supports thrombosis (PE/DVT/DIC)",
        "significance_low": "Normal — rules out significant active thromboembolism",
    },
}

CANONICAL_ANALYTES: Dict[str, str] = {
    "troponin": "troponin", "trop": "troponin", "tnt": "troponin", "tni": "troponin",
    "wbc": "wbc", "white blood count": "wbc", "leukocytes": "wbc",
    "hb": "hemoglobin", "hemoglobin": "hemoglobin", "hgb": "hemoglobin",
    "plt": "platelets", "platelets": "platelets", "platelet count": "platelets",
    "creatinine": "creatinine", "creat": "creatinine", "serum creatinine": "creatinine",
    "bun": "bun", "blood urea nitrogen": "bun", "urea": "bun",
    "glucose": "glucose", "blood sugar": "glucose", "rbs": "glucose", "fbs": "glucose",
    "sodium": "sodium", "na": "sodium",
    "potassium": "potassium", "k": "potassium",
    "d-dimer": "d_dimer", "ddimer": "d_dimer", "d dimer": "d_dimer",
}


def evaluate_analyte(
    analyte_name: str,
    value: float,
    context: ClinicalContext | None = None,
) -> Dict[str, Any]:
    """
    Evaluates a numeric lab analyte against reference intervals based on clinical context.
    """
    key = CANONICAL_ANALYTES.get(analyte_name.lower().strip(), analyte_name.lower().strip())
    db_entry = REFERENCE_DATABASE.get(key)

    if not db_entry:
        return {
            "analyte": analyte_name,
            "value": value,
            "unit": "",
            "reference_interval": "N/A",
            "status": "NORMAL",
            "severity": "NORMAL",
            "clinical_significance": "Value within unmapped range",
        }

    # Select interval tier based on context
    interval = db_entry.get("default", {})
    if context:
        if context.age_group == "pediatric" and "pediatric" in db_entry:
            interval = db_entry["pediatric"]
        elif context.age_group == "elderly" and "elderly" in db_entry:
            interval = db_entry["elderly"]
        elif context.sex in ("male", "female") and context.sex in db_entry:
            interval = db_entry[context.sex]

    low = interval.get("low", 0.0)
    high = interval.get("high", 9999.0)
    crit_high = interval.get("critical_high")
    crit_low = interval.get("critical_low")

    unit = db_entry["unit"]
    display_name = db_entry.get("display", analyte_name)

    ref_str = f"<{high} {unit}" if low == 0.0 else f"{low}–{high} {unit}"

    status = "NORMAL"
    severity = "NORMAL"
    significance = "Normal clinical finding"

    if crit_high is not None and value >= crit_high:
        status = "HIGH"
        severity = "CRITICAL"
        significance = db_entry.get("significance_high", "Critically elevated value")
    elif crit_low is not None and value <= crit_low:
        status = "LOW"
        severity = "CRITICAL"
        significance = db_entry.get("significance_low", "Critically low value")
    elif value > high:
        status = "HIGH"
        severity = "ABNORMAL"
        significance = db_entry.get("significance_high", "Elevated value")
    elif value < low:
        status = "LOW"
        severity = "ABNORMAL"
        significance = db_entry.get("significance_low", "Low value")

    return {
        "analyte": display_name,
        "analyte_key": key,
        "value": value,
        "unit": unit,
        "reference_interval": ref_str,
        "status": status,
        "severity": severity,
        "clinical_significance": significance,
    }
