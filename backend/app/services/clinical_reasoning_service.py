"""
clinical_reasoning_service.py — Deterministic Clinical Reasoning Layer

Implements a two-layer architecture:
    Layer 1 — Clinical Facts:  raw structured outputs from each subsystem,
                               normalized into a common format.
    Layer 2 — Clinical Conclusions:  deterministic derivations over the facts.
                                     Multi-factor confidence, uncertainty engine,
                                     ranking justification, limitations, report quality.

The LLM never computes any of these values.  It only explains them.

Non-negotiable constraints:
    • Does NOT modify prediction models, aggregation logic, or risk scoring.
    • Does NOT invent clinical findings.
    • Does NOT recommend medications or treatment plans.
    • All logic is deterministic and fully auditable.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Reference ranges for vital signs (clinical standard) ─────────────────────

VITAL_RANGES = {
    "heart_rate":       {"low": 60, "high": 100, "unit": "bpm",  "label": "Heart Rate"},
    "spo2":             {"low": 95, "high": 100, "unit": "%",    "label": "SpO₂"},
    "bp_systolic":      {"low": 90, "high": 140, "unit": "mmHg", "label": "Systolic BP"},
    "bp_diastolic":     {"low": 60, "high": 90,  "unit": "mmHg", "label": "Diastolic BP"},
    "temperature":      {"low": 36.1, "high": 37.8, "unit": "°C", "label": "Temperature"},
    "respiratory_rate": {"low": 12, "high": 20, "unit": "/min",  "label": "Respiratory Rate"},
}


# ── Condition display labels ────────────────────────────────────────────────

CONDITION_LABELS = {
    "ACS":        "Acute Coronary Syndrome",
    "PE":         "Pulmonary Embolism",
    "Pneumonia":  "Pneumonia",
    "Arrhythmia": "Arrhythmia",
    "Other":      "Other / Non-specific",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 1 — Clinical Facts
# ═══════════════════════════════════════════════════════════════════════════════

def build_clinical_facts(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and normalize raw clinical facts from the report data.
    Returns a flat, structured dictionary of observations with zero interpretation.
    """
    vitals = report_data.get("vitals", {})
    nlp = report_data.get("nlp_findings", {})
    risk = report_data.get("risk_engine", {})
    lab = report_data.get("lab_intelligence", {})
    imaging = report_data.get("imaging_intelligence", {})
    agg = report_data.get("aggregation", {})
    symptoms = report_data.get("symptoms", [])
    patient = report_data.get("patient_summary", {})
    investigations = report_data.get("investigations", [])

    # ── Vitals with abnormality flags ────────────────────────────────────
    vitals_analysis = []
    for key, ref in VITAL_RANGES.items():
        value = vitals.get(key)
        if value is None:
            continue
        status = "normal"
        if value < ref["low"]:
            status = "low"
        elif value > ref["high"]:
            status = "high"
        vitals_analysis.append({
            "parameter": ref["label"],
            "value": value,
            "unit": ref["unit"],
            "reference_low": ref["low"],
            "reference_high": ref["high"],
            "status": status,
        })

    # ── NLP flags (active ones) ──────────────────────────────────────────
    nlp_flags = nlp.get("flags", {})
    active_flags = [k.replace("_", " ").title() for k, v in nlp_flags.items() if v]

    # ── Risk scores ──────────────────────────────────────────────────────
    risk_scores = {
        "cardiac":       risk.get("cardiac", 0),
        "respiratory":   risk.get("respiratory", 0),
        "trauma":        risk.get("trauma", 0),
        "neurological":  risk.get("neurological", 0),
    }

    # ── Lab facts ────────────────────────────────────────────────────────
    lab_facts = None
    if lab and lab.get("available"):
        lab_facts = {
            "prediction":       lab.get("prediction"),
            "risk_probability": lab.get("risk_probability"),
            "top_features":     lab.get("top_features"),
        }

    # ── Imaging facts ────────────────────────────────────────────────────
    imaging_facts = None
    if imaging and imaging.get("available"):
        imaging_facts = {
            "prediction":            imaging.get("prediction"),
            "pneumonia_probability": imaging.get("pneumonia_probability"),
            "confidence":            imaging.get("confidence"),
            "xray_url":              imaging.get("xray_url", ""),
            "gradcam_url":           imaging.get("gradcam_url", ""),
        }

    # ── Aggregation facts ────────────────────────────────────────────────
    aggregation_facts = None
    if agg and agg.get("available"):
        aggregation_facts = {
            "primary_condition":     agg.get("primary_condition"),
            "probabilities":         agg.get("probabilities", {}),
            "evidence_breakdown":    agg.get("evidence_breakdown", {}),
            "source_summary":        agg.get("source_summary", {}),
            "confidence_suppressed": agg.get("confidence_suppressed", False),
            "suppression_reason":    agg.get("suppression_reason"),
        }

    return {
        "patient": {
            "name":             patient.get("name", "Unknown"),
            "age":              patient.get("age", 0),
            "gender":           patient.get("gender", ""),
            "chief_complaint":  patient.get("chief_complaint", ""),
            "severity":         patient.get("severity", "moderate"),
            "arrival_time":     patient.get("arrival_time", ""),
            "allergies":        patient.get("allergies", []),
            "medications":      patient.get("medications", []),
            "medical_history":  patient.get("medical_history", []),
        },
        "vitals_analysis":    vitals_analysis,
        "symptoms":           symptoms,
        "nlp_summary":        nlp.get("summary", ""),
        "nlp_entities":       nlp.get("entities", []),
        "active_nlp_flags":   active_flags,
        "risk_scores":        risk_scores,
        "risk_severity":      risk.get("severity", "moderate"),
        "lab":                lab_facts,
        "imaging":            imaging_facts,
        "aggregation":        aggregation_facts,
        "investigations":     investigations,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 2 — Clinical Conclusions
# ═══════════════════════════════════════════════════════════════════════════════

def derive_clinical_conclusions(facts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply deterministic rules over clinical facts to produce conclusions.
    Every value here is auditable and testable without involving the LLM.
    """
    # ── PRATHAM v2 Engine Integrations ──────────────────────────────────
    from app.services.clinical_context_service import build_clinical_context
    from app.services.clinical_pattern_engine import extract_clinical_patterns
    from app.services.clinical_scoring_service import calculate_clinical_scores
    from app.services.evidence_ranking_engine import rank_evidence_for_conditions

    # 1. Clinical Context Engine
    agg = facts.get("aggregation")
    primary_condition = None
    alternative_conditions: List[Dict[str, Any]] = []
    probabilities: Dict[str, Optional[float]] = {}
    if agg:
        primary_condition = agg.get("primary_condition")
        probabilities = agg.get("probabilities", {})
        for cond, prob in sorted(probabilities.items(), key=lambda x: x[1] if x[1] is not None else -1, reverse=True):
            if cond == primary_condition or prob is None:
                continue
            alternative_conditions.append({
                "condition": CONDITION_LABELS.get(cond, cond),
                "condition_key": cond,
                "probability": prob,
            })

    patient_dict = facts.get("patient", {})
    risk_scores = facts.get("risk_scores", {})
    completeness = _compute_data_completeness(facts)
    agreement, agreement_details = _compute_subsystem_agreement(facts)
    confidence, confidence_factors = _compute_clinical_confidence(facts, completeness, agreement)
    supporting, conflicting = _compile_evidence(facts)
    uncertainty_reasons = _compute_uncertainty_reasons(facts, completeness, agreement, conflicting)
    ranking_justification = _build_ranking_justification(facts)
    limitations = _compute_clinical_limitations(facts, completeness)
    investigation_status = _classify_investigations(facts)

    available_count = sum(1 for v in completeness.values() if v["available"])
    total_count = len(completeness)
    completeness_pct = round((available_count / total_count) * 100) if total_count > 0 else 0
    missing_critical = [info["label"] for info in completeness.values() if not info["available"] and info.get("critical", False)]

    report_quality = {
        "evidence_completeness_pct": completeness_pct,
        "subsystem_agreement": agreement,
        "pipeline_integrity": "PASS" if available_count >= 2 else "PARTIAL",
        "missing_critical_inputs": missing_critical,
    }

    vitals_dict = {
        item["parameter"].lower().replace(" ", "_").replace("₂", "2"): item["value"]
        for item in facts.get("vitals_analysis", [])
    }
    context = build_clinical_context(
        patient_data=patient_dict,
        vitals_data=vitals_dict,
        symptoms_data=facts.get("symptoms", []),
        risk_scores=risk_scores,
        chief_complaint=patient_dict.get("chief_complaint"),
    )

    # 2. Disease-Agnostic Clinical Pattern Engine
    clinical_patterns = extract_clinical_patterns(
        vitals=vitals_dict,
        symptoms=facts.get("symptoms", []),
        lab_evaluations=facts.get("lab_evaluations", []),
        nlp_flags={"respiratory_distress": "respiratory" in str(facts.get("active_nlp_flags", []))},
        context=context,
    )

    # 3. Clinical Scoring Engine
    clinical_scores = calculate_clinical_scores(
        vitals=vitals_dict,
        symptoms=facts.get("symptoms", []),
        patient_data=patient_dict,
        lab_evaluations=facts.get("lab_evaluations", []),
        context=context,
    )

    # 4. Evidence Ranking Engine & YAML Knowledge Base
    ranked_conditions = rank_evidence_for_conditions(
        vitals=vitals_dict,
        symptoms=facts.get("symptoms", []),
        clinical_patterns=clinical_patterns,
        lab_evaluations=facts.get("lab_evaluations", []),
        imaging_data=facts.get("imaging"),
        nlp_flags={"respiratory_distress": "respiratory" in str(facts.get("active_nlp_flags", []))},
    )

    # Top ranked condition evidence metadata
    top_rank = ranked_conditions[0] if ranked_conditions else {}

    explainability_metadata = {
        "top_patterns": [p["pattern_name"] for p in clinical_patterns],
        "evidence_score": top_rank.get("evidence_score", 0.0),
        "support_score": top_rank.get("support_score", 0.0),
        "conflict_score": top_rank.get("conflict_score", 0.0),
        "missing_evidence_score": top_rank.get("missing_evidence_score", 0.0),
        "knowledge_base_version": top_rank.get("knowledge_base_version", "1.2"),
        "confidence_inputs": [f["label"] for f in completeness.values() if f["available"]],
    }

    # 4-Tier Recommendations
    suggested_investigations = top_rank.get("suggested_investigations") or [
        inv["investigation_type"] for inv in facts.get("investigations", [])
    ]

    return {
        "primary_condition":       CONDITION_LABELS.get(primary_condition, primary_condition) if primary_condition else (top_rank.get("condition_name") if top_rank else None),
        "primary_condition_key":   primary_condition or (top_rank.get("condition_key") if top_rank else None),
        "probabilities":           probabilities,
        "alternative_conditions":  alternative_conditions,
        "supporting_evidence":     supporting or (top_rank.get("matched_supporting", [])),
        "conflicting_evidence":    conflicting or (top_rank.get("matched_conflicting", [])),
        "clinical_confidence":     confidence,
        "confidence_factors":      confidence_factors,
        "uncertainty_reasons":     uncertainty_reasons,
        "ranking_justification":   ranking_justification,
        "clinical_context":        context.to_dict(),
        "clinical_patterns":       clinical_patterns,
        "clinical_scores":         clinical_scores,
        "ranked_conditions":       ranked_conditions,
        "explainability_metadata": explainability_metadata,
        "monitoring_priorities":   top_rank.get("monitoring_priorities") or monitoring_priorities,
        "clinical_precautions":    top_rank.get("clinical_precautions") or clinical_precautions,
        "suggested_investigations": suggested_investigations,
        "investigation_status":    investigation_status,
        "data_completeness":       completeness,
        "clinical_limitations":    limitations,
        "report_quality":          report_quality,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Internal helper functions
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_data_completeness(facts: Dict) -> Dict[str, Dict]:
    """Check which data sources are present and mark them."""
    return {
        "vitals": {
            "label": "Vital Signs",
            "available": len(facts.get("vitals_analysis", [])) > 0,
            "critical": True,
        },
        "symptoms": {
            "label": "Symptoms",
            "available": len(facts.get("symptoms", [])) > 0 or len(facts.get("active_nlp_flags", [])) > 0,
            "critical": False,
        },
        "nlp": {
            "label": "Clinical NLP",
            "available": bool(facts.get("nlp_summary")) or len(facts.get("active_nlp_flags", [])) > 0,
            "critical": False,
        },
        "risk": {
            "label": "Risk Assessment",
            "available": any(v > 0 for v in facts.get("risk_scores", {}).values()),
            "critical": True,
        },
        "lab": {
            "label": "Laboratory Analysis",
            "available": facts.get("lab") is not None,
            "critical": False,
        },
        "imaging": {
            "label": "Medical Imaging",
            "available": facts.get("imaging") is not None,
            "critical": False,
        },
        "aggregation": {
            "label": "Evidence Aggregation",
            "available": facts.get("aggregation") is not None,
            "critical": True,
        },
    }


def _compute_subsystem_agreement(facts: Dict) -> tuple[str, List[str]]:
    """
    Assess whether the available subsystems point in the same direction.
    Returns (level, [detail strings]).
    """
    details: List[str] = []
    conflicts = 0

    risk_scores = facts.get("risk_scores", {})
    lab = facts.get("lab")
    imaging = facts.get("imaging")
    agg = facts.get("aggregation")

    active_sources = sum(1 for x in [risk_scores and any(v > 0 for v in risk_scores.values()), lab, imaging, agg] if x)
    if active_sources < 2:
        return "INSUFFICIENT DATA", ["Insufficient active AI subsystems to evaluate agreement"]

    # Check 1: Do risk scores and imaging agree on respiratory vs cardiac?
    resp_risk = risk_scores.get("respiratory", 0)
    cardiac_risk = risk_scores.get("cardiac", 0)

    if imaging:
        img_pred = (imaging.get("prediction") or "").lower()
        img_prob = imaging.get("pneumonia_probability", 0) or 0

        if img_pred == "pneumonia" and img_prob > 0.5:
            details.append("Imaging supports respiratory pathology")
            if resp_risk < 30:
                conflicts += 1
                details.append("Risk engine does NOT flag significant respiratory risk — partial conflict with imaging")
        elif img_pred == "normal" and resp_risk >= 50:
            conflicts += 1
            details.append("Imaging shows normal findings but risk engine flags significant respiratory risk — conflict")
        else:
            details.append("Imaging and risk engine are not in direct conflict")

    # Check 2: Do lab findings agree with aggregation primary condition?
    if lab and agg:
        lab_pred = (lab.get("prediction") or "").lower()
        primary = (agg.get("primary_condition") or "").lower()

        if lab_pred == "high_risk" and primary in ("pneumonia", "pe"):
            details.append("Lab indicates cardiac risk but primary condition is respiratory — partial conflict")
            conflicts += 1
        elif lab_pred == "low_risk" and primary == "acs":
            details.append("Lab indicates low risk but primary condition is ACS — conflict")
            conflicts += 1
        else:
            details.append("Lab findings are consistent with aggregation")

    # Check 3: Do NLP flags support the aggregation direction?
    active_flags = facts.get("active_nlp_flags", [])
    if agg and active_flags:
        primary = (agg.get("primary_condition") or "").lower()
        has_cardiac_flag = any("cardiac" in f.lower() for f in active_flags)
        has_respiratory_flag = any("respiratory" in f.lower() or "breathlessness" in f.lower() for f in active_flags)

        if primary == "acs" and has_cardiac_flag:
            details.append("NLP cardiac flags support ACS finding")
        elif primary in ("pneumonia", "pe") and has_respiratory_flag:
            details.append("NLP respiratory flags support respiratory finding")
        elif primary == "acs" and not has_cardiac_flag and has_respiratory_flag:
            conflicts += 1
            details.append("NLP flags suggest respiratory pattern but primary is cardiac — partial conflict")

    if conflicts == 0:
        return "HIGH", details
    elif conflicts == 1:
        return "MODERATE", details
    else:
        return "LOW", details


def _compute_clinical_confidence(
    facts: Dict,
    completeness: Dict[str, Dict],
    agreement: str,
) -> tuple[str, List[str]]:
    """
    Multi-factor clinical confidence:
      base_probability × source_count × agreement
    Returns (level, [audit factors]).
    """
    factors: List[str] = []
    score = 0.0  # 0–100 internal scale

    agg = facts.get("aggregation")

    # Factor 1: Base probability of primary condition
    if agg and not agg.get("confidence_suppressed"):
        primary = agg.get("primary_condition")
        probs = agg.get("probabilities", {})
        primary_prob = probs.get(primary, 0) or 0

        if primary_prob >= 0.5:
            score += 40
            factors.append(f"✓ Primary condition probability is {primary_prob*100:.1f}% (strong signal)")
        elif primary_prob >= 0.3:
            score += 25
            factors.append(f"✓ Primary condition probability is {primary_prob*100:.1f}% (moderate signal)")
        else:
            score += 10
            factors.append(f"⚠ Primary condition probability is {primary_prob*100:.1f}% (weak signal)")
    elif agg and agg.get("confidence_suppressed"):
        score += 5
        factors.append(f"⚠ Aggregation confidence suppressed: {agg.get('suppression_reason', 'insufficient evidence')}")
    else:
        score += 0
        factors.append("⚠ No aggregation data available")

    # Factor 2: Active source count
    available = sum(1 for v in completeness.values() if v["available"])
    total = len(completeness)
    if available >= 5:
        score += 30
        factors.append(f"✓ {available}/{total} data sources available (comprehensive)")
    elif available >= 3:
        score += 20
        factors.append(f"✓ {available}/{total} data sources available (adequate)")
    else:
        score += 5
        factors.append(f"⚠ Only {available}/{total} data sources available (limited)")

    # Factor 3: Subsystem agreement
    if agreement == "HIGH":
        score += 30
        factors.append("✓ All available subsystems agree — no conflicting evidence detected")
    elif agreement == "MODERATE":
        score += 15
        factors.append("⚠ Partial agreement — some subsystem findings conflict")
    elif agreement == "INSUFFICIENT DATA":
        score += 0
        factors.append("⚠ Subsystem agreement cannot be calculated (insufficient data sources)")
    else:
        score += 5
        factors.append("⚠ Low agreement — significant conflicts between subsystems")

    # Force cap for sparse data (<3 available sources or missing aggregation)
    if available < 3 or not agg:
        level = "LOW"
        factors.append("⚠ Sparse evidence (<3 active sources) — confidence capped at LOW")
    elif agreement == "LOW":
        level = "LOW"
        factors.append("⚠ Severe subsystem conflict — confidence capped at LOW")
    elif agreement == "MODERATE" and score >= 85:
        level = "MODERATE"
        factors.append("⚠ Subsystem conflict — confidence capped at MODERATE")
    elif score >= 95:
        level = "VERY HIGH"
    elif score >= 85:
        level = "HIGH"
    elif score >= 65:
        level = "MODERATE"
    else:
        level = "LOW"

    return level, factors


def _compute_uncertainty_reasons(
    facts: Dict,
    completeness: Dict[str, Dict],
    agreement: str,
    conflicting: List[str],
) -> List[str]:
    """
    Explain WHY diagnostic certainty is reduced.
    """
    reasons: List[str] = []

    # Missing data sources
    for source, info in completeness.items():
        if not info["available"]:
            reasons.append(f"{info['label']} unavailable")

    # Subsystem disagreement
    if agreement != "HIGH":
        reasons.append("Subsystem findings partially conflict")

    # Aggregation suppressed
    agg = facts.get("aggregation")
    if agg and agg.get("confidence_suppressed"):
        reasons.append(f"Evidence aggregation suppressed: {agg.get('suppression_reason', 'insufficient data')}")

    # Conflicting evidence
    if conflicting:
        reasons.append(f"{len(conflicting)} conflicting evidence item(s) detected")

    return reasons


def _compile_evidence(facts: Dict) -> tuple[List[str], List[str]]:
    """
    Compile supporting and conflicting evidence for the primary condition.
    """
    supporting: List[str] = []
    conflicting: List[str] = []

    agg = facts.get("aggregation")
    if not agg:
        return supporting, conflicting

    primary = agg.get("primary_condition")
    if not primary:
        return supporting, conflicting

    # NLP evidence
    nlp_flags = facts.get("active_nlp_flags", [])
    if primary == "ACS":
        if any("cardiac" in f.lower() or "chest" in f.lower() for f in nlp_flags):
            supporting.append("NLP detected cardiac risk signals in clinical notes")
        if any("respiratory" in f.lower() for f in nlp_flags) and not any("cardiac" in f.lower() for f in nlp_flags):
            conflicting.append("NLP flags suggest respiratory pattern rather than cardiac")
    elif primary in ("Pneumonia", "PE"):
        if any("respiratory" in f.lower() or "breathlessness" in f.lower() for f in nlp_flags):
            supporting.append("NLP detected respiratory distress signals")
        if any("cardiac" in f.lower() for f in nlp_flags) and not any("respiratory" in f.lower() for f in nlp_flags):
            conflicting.append("NLP flags suggest cardiac pattern rather than respiratory")

    # Symptom evidence
    symptoms = facts.get("symptoms", [])
    if primary == "ACS" and "Chest Pain" in symptoms:
        supporting.append("Patient reports chest pain")
    if primary in ("Pneumonia", "PE") and "Breathlessness" in symptoms:
        supporting.append("Patient reports breathlessness")

    # Vitals evidence
    for v in facts.get("vitals_analysis", []):
        if v["status"] != "normal":
            param = v["parameter"]
            val = v["value"]
            unit = v["unit"]
            if primary in ("Pneumonia", "PE") and param in ("SpO₂", "Respiratory Rate"):
                supporting.append(f"Abnormal {param}: {val} {unit}")
            elif primary == "ACS" and param in ("Heart Rate", "Systolic BP"):
                supporting.append(f"Abnormal {param}: {val} {unit}")
            elif primary in ("Pneumonia", "PE") and param == "Temperature" and v["status"] == "high":
                supporting.append(f"Elevated temperature: {val} {unit} (fever)")

    # Risk score evidence
    risk = facts.get("risk_scores", {})
    if primary == "ACS":
        if risk.get("cardiac", 0) >= 50:
            supporting.append(f"Elevated cardiac risk score: {risk['cardiac']}/100")
        elif risk.get("cardiac", 0) < 20:
            conflicting.append(f"Low cardiac risk score: {risk['cardiac']}/100")
    elif primary in ("Pneumonia", "PE"):
        if risk.get("respiratory", 0) >= 50:
            supporting.append(f"Elevated respiratory risk score: {risk['respiratory']}/100")
        elif risk.get("respiratory", 0) < 20:
            conflicting.append(f"Low respiratory risk score: {risk['respiratory']}/100")

    # Lab evidence
    lab = facts.get("lab")
    if lab:
        pred = (lab.get("prediction") or "").lower()
        prob = lab.get("risk_probability", 0) or 0
        if primary == "ACS" and pred == "high_risk":
            supporting.append(f"Laboratory model indicates high cardiac risk (probability: {prob*100:.1f}%)")
        elif primary == "ACS" and pred == "low_risk":
            conflicting.append(f"Laboratory model indicates low cardiac risk (probability: {prob*100:.1f}%)")
        elif primary in ("Pneumonia", "PE") and pred == "high_risk":
            conflicting.append("Laboratory model flags cardiac risk, which may suggest alternative cardiac etiology")

    # Imaging evidence
    imaging = facts.get("imaging")
    if imaging:
        img_pred = (imaging.get("prediction") or "").lower()
        img_prob = imaging.get("pneumonia_probability", 0) or 0
        if primary == "Pneumonia" and img_pred == "pneumonia":
            supporting.append(f"Chest imaging positive for pneumonia (probability: {img_prob*100:.1f}%)")
        elif primary == "Pneumonia" and img_pred == "normal":
            conflicting.append("Chest imaging appears normal — does not support pneumonia finding")
        elif primary == "ACS" and img_pred == "pneumonia":
            conflicting.append("Chest imaging suggests pneumonia rather than cardiac etiology")
        elif primary == "ACS" and img_pred == "normal":
            supporting.append("Normal chest imaging is consistent with cardiac rather than respiratory etiology")

    return supporting, conflicting


def _build_ranking_justification(facts: Dict) -> Dict[str, Any]:
    """
    Explain why the primary condition was ranked #1 and why alternatives were ranked lower.
    Returns a structured justification object.
    """
    agg = facts.get("aggregation")
    if not agg:
        return {"primary_reasons": [], "vs_alternatives": []}

    primary = agg.get("primary_condition")
    probs = agg.get("probabilities", {})
    breakdown = agg.get("evidence_breakdown", {})

    primary_reasons: List[str] = []
    vs_alternatives: List[Dict[str, Any]] = []

    # Reasons from evidence breakdown for the primary
    primary_evidence = breakdown.get(primary, [])
    for item in primary_evidence:
        # Format: "source:+delta"  e.g. "nlp:chest_pain:+3.0"
        label = item.replace(":", " → ").replace("_", " ").replace("+", "↑").replace("-", "↓")
        primary_reasons.append(label)

    # Why each alternative is ranked lower
    for cond, prob in sorted(probs.items(), key=lambda x: x[1] if x[1] else -1, reverse=True):
        if cond == primary or prob is None:
            continue
        reasons: List[str] = []
        cond_evidence = breakdown.get(cond, [])
        primary_prob = probs.get(primary, 0) or 0

        if prob < primary_prob:
            reasons.append(f"Lower probability ({prob*100:.1f}% vs {primary_prob*100:.1f}%)")

        if len(cond_evidence) < len(primary_evidence):
            reasons.append(f"Fewer supporting evidence items ({len(cond_evidence)} vs {len(primary_evidence)})")

        if not cond_evidence:
            reasons.append("No direct evidence supporting this condition")

        vs_alternatives.append({
            "condition": CONDITION_LABELS.get(cond, cond),
            "reasons": reasons,
        })

    return {
        "primary_reasons": primary_reasons,
        "vs_alternatives": vs_alternatives,
    }


def _determine_monitoring_priorities(facts: Dict) -> List[Dict[str, str]]:
    """
    Determine which clinical parameters should be monitored.
    These are OBSERVATIONS to track, NOT actions to take.
    """
    priorities: List[Dict[str, str]] = []
    risk = facts.get("risk_scores", {})
    agg = facts.get("aggregation")
    primary = (agg.get("primary_condition") or "").lower() if agg else ""

    # SpO2 monitoring
    for v in facts.get("vitals_analysis", []):
        if v["parameter"] == "SpO₂" and v["status"] != "normal":
            priorities.append({"parameter": "Oxygen saturation (SpO₂)", "reason": f"Current value {v['value']}% is abnormal"})
            break
    if risk.get("respiratory", 0) >= 40 or primary in ("pneumonia", "pe"):
        if not any(p["parameter"].startswith("Oxygen") for p in priorities):
            priorities.append({"parameter": "Oxygen saturation (SpO₂)", "reason": "Elevated respiratory risk"})

    # Heart rate / cardiac monitoring
    if risk.get("cardiac", 0) >= 40 or primary in ("acs", "arrhythmia"):
        priorities.append({"parameter": "Continuous cardiac rhythm", "reason": "Elevated cardiac risk"})
    for v in facts.get("vitals_analysis", []):
        if v["parameter"] == "Heart Rate" and v["status"] != "normal":
            if not any("cardiac rhythm" in p["parameter"].lower() for p in priorities):
                priorities.append({"parameter": "Heart rate", "reason": f"Current value {v['value']} bpm is abnormal"})
            break

    # Blood pressure
    for v in facts.get("vitals_analysis", []):
        if v["parameter"] == "Systolic BP" and v["status"] != "normal":
            priorities.append({"parameter": "Blood pressure", "reason": f"Current systolic BP {v['value']} mmHg is abnormal"})
            break

    # Respiratory rate
    for v in facts.get("vitals_analysis", []):
        if v["parameter"] == "Respiratory Rate" and v["status"] != "normal":
            priorities.append({"parameter": "Respiratory rate", "reason": f"Current value {v['value']}/min is abnormal"})
            break

    # Temperature
    for v in facts.get("vitals_analysis", []):
        if v["parameter"] == "Temperature" and v["status"] != "normal":
            priorities.append({"parameter": "Temperature", "reason": f"Current value {v['value']}°C is abnormal"})
            break

    if not priorities:
        priorities.append({"parameter": "Standard clinical observations", "reason": "Routine monitoring"})

    return priorities


def _determine_clinical_precautions(facts: Dict) -> List[Dict[str, str]]:
    """
    Determine action-oriented clinical precautions.
    These are safety-focused actions — NEVER treatment recommendations.
    """
    precautions: List[Dict[str, str]] = []
    risk = facts.get("risk_scores", {})
    severity = facts.get("risk_severity", "moderate")
    agg = facts.get("aggregation")
    primary = (agg.get("primary_condition") or "").lower() if agg else ""

    # Respiratory precautions
    if risk.get("respiratory", 0) >= 50 or primary in ("pneumonia", "pe"):
        precautions.append({
            "action": "Observe for respiratory deterioration",
            "reason": "Significant respiratory risk identified",
        })
        precautions.append({
            "action": "Escalate if oxygen requirement increases",
            "reason": "Progressive hypoxemia may indicate worsening condition",
        })

    # Cardiac precautions
    if risk.get("cardiac", 0) >= 50 or primary in ("acs", "arrhythmia"):
        precautions.append({
            "action": "Maintain close cardiac observation",
            "reason": "Elevated cardiac risk identified",
        })

    # General high-severity precautions
    if severity in ("high", "critical"):
        precautions.append({
            "action": "Ensure immediate clinical availability",
            "reason": f"Overall severity assessed as {severity}",
        })

    # Imaging repeat consideration
    imaging = facts.get("imaging")
    if imaging and (imaging.get("prediction") or "").lower() == "pneumonia":
        precautions.append({
            "action": "Repeat imaging if condition worsens or fails to improve",
            "reason": "Baseline imaging shows abnormality",
        })

    if not precautions:
        precautions.append({
            "action": "Maintain standard clinical observation",
            "reason": "No immediate high-risk findings identified",
        })

    return precautions


def _compute_clinical_limitations(facts: Dict, completeness: Dict) -> List[Dict[str, Any]]:
    """
    Identify specific diagnostic limitations for the current assessment.
    """
    limitations: List[Dict[str, Any]] = []

    for source, info in completeness.items():
        limitations.append({
            "source": info["label"],
            "available": info["available"],
        })

    # Add specific investigation-based limitations
    investigations = facts.get("investigations", [])
    approved_types = {inv.get("investigation_type") for inv in investigations if inv.get("status") == "approved"}

    from app.services.investigation_registry import SUPPORTED_ANALYSES
    unsupported_approved = []
    for inv_type in approved_types:
        if inv_type not in SUPPORTED_ANALYSES:
            unsupported_approved.append(inv_type)

    if unsupported_approved:
        for inv_type in unsupported_approved:
            limitations.append({
                "source": f"{inv_type} Interpretation",
                "available": False,
                "note": "Approved but AI analysis not available in this version",
            })

    return limitations


def _classify_investigations(facts: Dict) -> List[Dict[str, Any]]:
    """
    Classify investigation recommendations into supported/unsupported categories.
    """
    from app.services.investigation_registry import SUPPORTED_ANALYSES, get_analysis_type

    investigations = facts.get("investigations", [])
    classified: List[Dict[str, Any]] = []

    for inv in investigations:
        inv_type = inv.get("investigation_type", "")
        status = inv.get("status", "pending_approval")
        analysis_type = get_analysis_type(inv_type)

        classified.append({
            "investigation_type":  inv_type,
            "status":              status,
            "ai_supported":        analysis_type is not None,
            "analysis_type":       analysis_type,
            "ai_status":           "Analysis available" if analysis_type else "Analysis not available in this version",
        })

    return classified


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

def build_clinical_evidence(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point.  Returns the complete Clinical Evidence Object
    containing both layers (facts + conclusions).
    """
    facts = build_clinical_facts(report_data)
    conclusions = derive_clinical_conclusions(facts)

    return {
        "facts":       facts,
        "conclusions": conclusions,
    }
