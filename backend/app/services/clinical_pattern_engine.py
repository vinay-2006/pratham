"""
clinical_pattern_engine.py — Disease-Agnostic Clinical Pattern Engine

Converts abnormal findings (vitals, lab analytes, symptoms) into reusable,
disease-agnostic clinical syndromes without making specific disease diagnoses.
"""

from __future__ import annotations
from typing import Any, Dict, List
from app.services.clinical_context_service import ClinicalContext


def extract_clinical_patterns(
    vitals: Dict[str, Any],
    symptoms: Dict[str, Any] | List[str],
    lab_evaluations: List[Dict[str, Any]] | None = None,
    nlp_flags: Dict[str, Any] | None = None,
    context: ClinicalContext | None = None,
) -> List[Dict[str, Any]]:
    """
    Evaluates patient findings to extract disease-agnostic clinical patterns/syndromes.
    Returns a list of pattern dicts.
    """
    patterns: List[Dict[str, Any]] = []

    # Helper helpers
    spo2 = vitals.get("spo2")
    rr = vitals.get("respiratory_rate")
    hr = vitals.get("heart_rate")
    bp_sys = vitals.get("bp_systolic")
    temp = vitals.get("temperature")

    sym_dict = symptoms if isinstance(symptoms, dict) else {s: True for s in symptoms}
    nlp = nlp_flags or {}
    labs = {item["analyte_key"]: item for item in (lab_evaluations or []) if "analyte_key" in item}

    # 1. RESPIRATORY DISTRESS PATTERN
    resp_ev = []
    if spo2 is not None and 0 < spo2 < 94:
        resp_ev.append(f"SpO₂ {spo2}% (hypoxemia)")
    if rr is not None and rr > 20:
        resp_ev.append(f"Respiratory rate {rr}/min (tachypnea)")
    if sym_dict.get("breathlessness") or nlp.get("respiratory_distress"):
        resp_ev.append("Symptom: dyspnea / breathlessness")

    if len(resp_ev) >= 2 or (spo2 is not None and 0 < spo2 < 90):
        patterns.append({
            "pattern_name": "Respiratory Distress",
            "pattern_key": "respiratory_distress",
            "severity": "CRITICAL" if (spo2 is not None and 0 < spo2 < 90) else "HIGH",
            "supporting_evidence": resp_ev,
        })

    # 2. HEMODYNAMIC INSTABILITY / SHOCK PATTERN
    hemo_ev = []
    if bp_sys is not None and 0 < bp_sys < 90:
        hemo_ev.append(f"Systolic BP {bp_sys} mmHg (hypotension)")
    if hr is not None and (hr > 100 or (0 < hr < 50)):
        hemo_ev.append(f"Heart rate {hr} bpm")
    if sym_dict.get("unconsciousness") or nlp.get("loss_of_consciousness"):
        hemo_ev.append("Altered mental status / unconsciousness")

    if len(hemo_ev) >= 2 or (bp_sys is not None and 0 < bp_sys < 85):
        patterns.append({
            "pattern_name": "Hemodynamic Instability / Shock",
            "pattern_key": "hemodynamic_instability",
            "severity": "CRITICAL" if (bp_sys is not None and 0 < bp_sys < 85) else "HIGH",
            "supporting_evidence": hemo_ev,
        })

    # 3. SYSTEMIC INFLAMMATION / SEPSIS PATTERN
    sepsis_ev = []
    if temp is not None and temp > 0:
        c_temp = temp if temp < 45 else (temp - 32) * 5 / 9
        if c_temp > 38.0 or c_temp < 36.0:
            sepsis_ev.append(f"Body temperature {c_temp:.1f}°C")
    if hr is not None and hr > 90:
        sepsis_ev.append(f"Heart rate {hr} bpm")
    if rr is not None and rr > 20:
        sepsis_ev.append(f"Respiratory rate {rr}/min")
    if "wbc" in labs and labs["wbc"]["status"] != "NORMAL":
        sepsis_ev.append(f"WBC {labs['wbc']['value']} {labs['wbc']['unit']} ({labs['wbc']['status']})")

    if len(sepsis_ev) >= 2:
        patterns.append({
            "pattern_name": "Systemic Inflammatory Response",
            "pattern_key": "systemic_inflammation",
            "severity": "HIGH" if len(sepsis_ev) >= 3 else "MODERATE",
            "supporting_evidence": sepsis_ev,
        })

    # 4. MYOCARDIAL INJURY PATTERN
    card_ev = []
    if "troponin" in labs and labs["troponin"]["status"] == "HIGH":
        card_ev.append(f"Troponin {labs['troponin']['value']} {labs['troponin']['unit']} (HIGH)")
    if sym_dict.get("chest_pain") or nlp.get("cardiac_risk_flag"):
        card_ev.append("Symptom: Chest pain / Cardiac risk flag")

    if len(card_ev) >= 1 and ("troponin" in labs and labs["troponin"]["status"] == "HIGH"):
        patterns.append({
            "pattern_name": "Myocardial Injury",
            "pattern_key": "myocardial_injury",
            "severity": "CRITICAL" if len(card_ev) >= 2 else "HIGH",
            "supporting_evidence": card_ev,
        })

    # 5. RENAL IMPAIRMENT PATTERN
    renal_ev = []
    if "creatinine" in labs and labs["creatinine"]["status"] == "HIGH":
        renal_ev.append(f"Serum Creatinine {labs['creatinine']['value']} {labs['creatinine']['unit']} (HIGH)")
    if "bun" in labs and labs["bun"]["status"] == "HIGH":
        renal_ev.append(f"BUN {labs['bun']['value']} {labs['bun']['unit']} (HIGH)")

    if len(renal_ev) >= 1:
        patterns.append({
            "pattern_name": "Renal Impairment",
            "pattern_key": "renal_impairment",
            "severity": "HIGH" if len(renal_ev) >= 2 else "MODERATE",
            "supporting_evidence": renal_ev,
        })

    return patterns
