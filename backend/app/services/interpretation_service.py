"""
interpretation_service.py — Grounded LLM Clinical Interpretation Layer

Receives the Clinical Evidence Object (facts + conclusions) from
clinical_reasoning_service.py and generates clinician-friendly narrative text.

Architecture constraints:
    • The LLM receives ONLY structured evidence — never raw images or PDFs.
    • The LLM returns ONLY valid JSON populating predefined text fields.
    • The LLM NEVER computes confidence, rankings, or evidence lists.
    • The LLM NEVER invents findings beyond supplied evidence.
    • The LLM NEVER recommends medications or treatment plans.
    • The LLM NEVER strengthens certainty beyond the structured evidence.
    • If evidence is incomplete or conflicting, the LLM explicitly communicates uncertainty.

Fallback: If Groq is unavailable, a deterministic rule-based generator produces
reasonable placeholder narratives so reports never crash.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── Expected LLM output fields ──────────────────────────────────────────────

NARRATIVE_FIELDS = [
    "clinical_overview",
    "overall_impression",
    "cardiac_summary",
    "respiratory_summary",
    "laboratory_summary",
    "imaging_summary",
    "monitoring_narrative",
    "precautions_narrative",
    "alternative_considerations_narrative",
    "limitations_narrative",
]


# ═══════════════════════════════════════════════════════════════════════════════
# LLM Interpretation
# ═══════════════════════════════════════════════════════════════════════════════

def generate_clinical_interpretation(
    clinical_evidence: Dict[str, Any],
) -> Dict[str, str]:
    """
    Call Groq LLM to generate clinical narrative text from the Clinical Evidence Object.
    Returns a dict mapping each NARRATIVE_FIELDS key to a text string.
    Falls back to rule-based generation on any failure.
    """
    try:
        return _call_llm(clinical_evidence)
    except Exception as exc:
        logger.warning(
            "[PRATHAM/INTERP] LLM interpretation failed, using fallback: %s", exc
        )
        return generate_fallback_interpretation(clinical_evidence)


def _build_llm_prompt(clinical_evidence: Dict[str, Any]) -> str:
    """
    Build the system + user prompt for the Groq LLM.
    The evidence is serialized as JSON and the LLM is instructed to
    return ONLY valid JSON with the predefined narrative fields.
    """
    facts = clinical_evidence.get("facts", {})
    conclusions = clinical_evidence.get("conclusions", {})

    # Build a focused evidence summary for the LLM (not the entire raw object)
    evidence_for_llm = {
        "patient": facts.get("patient", {}),
        "vitals": facts.get("vitals_analysis", []),
        "symptoms": facts.get("symptoms", []),
        "nlp_summary": facts.get("nlp_summary", ""),
        "active_clinical_flags": facts.get("active_nlp_flags", []),
        "risk_scores": facts.get("risk_scores", {}),
        "risk_severity": facts.get("risk_severity", ""),
        "lab_findings": facts.get("lab"),
        "imaging_findings": facts.get("imaging"),
        "primary_condition": conclusions.get("primary_condition"),
        "alternative_conditions": conclusions.get("alternative_conditions", []),
        "clinical_confidence": conclusions.get("clinical_confidence"),
        "supporting_evidence": conclusions.get("supporting_evidence", []),
        "conflicting_evidence": conclusions.get("conflicting_evidence", []),
        "uncertainty_reasons": conclusions.get("uncertainty_reasons", []),
        "monitoring_priorities": conclusions.get("monitoring_priorities", []),
        "clinical_precautions": conclusions.get("clinical_precautions", []),
        "clinical_limitations": conclusions.get("clinical_limitations", []),
        "data_completeness": {
            k: v["available"]
            for k, v in conclusions.get("data_completeness", {}).items()
        },
    }

    system_prompt = (
        "You are a clinical decision-support report writer for an emergency department AI system called PRATHAM.\n\n"
        "STRICT RULES — you MUST follow ALL of these:\n"
        "1. Return ONLY valid JSON. No markdown. No explanation. No preamble.\n"
        "2. Use ONLY the supplied clinical evidence. Do NOT invent any findings.\n"
        "3. NEVER recommend medications or prescribe treatment.\n"
        "4. NEVER diagnose beyond supplied evidence.\n"
        "5. NEVER strengthen certainty beyond the structured evidence.\n"
        "   If evidence is incomplete or conflicting, explicitly communicate uncertainty.\n"
        "6. Use professional clinical language suitable for an attending physician.\n"
        "7. Keep each field concise (2-4 sentences).\n"
        "8. If a data source is missing, explicitly state it is unavailable.\n\n"
        "Return this exact JSON structure:\n"
        "{\n"
        '  "clinical_overview": "Concise summary of the patient\'s current clinical presentation.",\n'
        '  "overall_impression": "Most likely clinical interpretation based on all available evidence.",\n'
        '  "cardiac_summary": "Assessment of cardiac status based on available evidence.",\n'
        '  "respiratory_summary": "Assessment of respiratory status based on available evidence.",\n'
        '  "laboratory_summary": "Interpretation of laboratory findings. State if unavailable.",\n'
        '  "imaging_summary": "Interpretation of imaging findings. State if unavailable.",\n'
        '  "monitoring_narrative": "Brief explanation of why these monitoring parameters were selected.",\n'
        '  "precautions_narrative": "Brief explanation of the clinical precautions and their rationale.",\n'
        '  "alternative_considerations_narrative": "Explanation of what else could explain these symptoms and why the primary condition was favored.",\n'
        '  "limitations_narrative": "Statement about what diagnostic information is missing and how it affects this assessment."\n'
        "}"
    )

    user_prompt = (
        "Generate a clinical interpretation report based on the following structured clinical evidence.\n\n"
        f"CLINICAL EVIDENCE:\n{json.dumps(evidence_for_llm, indent=2, default=str)}"
    )

    return system_prompt, user_prompt


def _call_llm(clinical_evidence: Dict[str, Any]) -> Dict[str, str]:
    """
    Call Groq API to generate the clinical narrative.
    Raises on failure so the caller can fall back.
    """
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set — cannot call LLM")

    from groq import Groq
    client = Groq(api_key=api_key)

    system_prompt, user_prompt = _build_llm_prompt(clinical_evidence)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()

    # Strip <think>...</think> reasoning tags (some models include these)
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # Strip markdown code fences if present
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            cleaned = part.strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
            if cleaned.startswith("{"):
                raw = cleaned
                break

    # Extract first JSON object as fallback
    if not raw.startswith("{"):
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            raw = match.group(0)

    result = json.loads(raw)

    # Ensure all expected fields are present
    for field in NARRATIVE_FIELDS:
        if field not in result or not isinstance(result[field], str):
            result[field] = ""

    logger.info("[PRATHAM/INTERP] LLM interpretation generated successfully")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Rule-Based Fallback
# ═══════════════════════════════════════════════════════════════════════════════

def generate_fallback_interpretation(
    clinical_evidence: Dict[str, Any],
) -> Dict[str, str]:
    """
    Deterministic rule-based narrative generator.
    Used when the LLM is unavailable. Produces reasonable clinical text
    from the structured evidence without any AI generation.
    """
    facts = clinical_evidence.get("facts", {})
    conclusions = clinical_evidence.get("conclusions", {})

    patient = facts.get("patient", {})
    name = patient.get("name", "The patient")
    age = patient.get("age", 0)
    gender = patient.get("gender", "")
    chief = patient.get("chief_complaint", "unspecified complaint")
    severity = patient.get("severity", "moderate")

    primary = conclusions.get("primary_condition", "an unspecified condition")
    confidence = conclusions.get("clinical_confidence", "MODERATE")
    supporting = conclusions.get("supporting_evidence", [])
    conflicting_ev = conclusions.get("conflicting_evidence", [])
    uncertainty = conclusions.get("uncertainty_reasons", [])
    alternatives = conclusions.get("alternative_conditions", [])
    limitations_list = conclusions.get("clinical_limitations", [])
    monitoring = conclusions.get("monitoring_priorities", [])
    precautions = conclusions.get("clinical_precautions", [])

    gender_str = "male" if gender == "male" else "female" if gender == "female" else ""
    age_gender = f"{age}-year-old {gender_str}".strip() if age else "patient"

    # ── Clinical Overview ────────────────────────────────────────────────
    clinical_overview = (
        f"{name} is a {age_gender} presenting with {chief}. "
        f"Initial assessment indicates {severity} severity. "
    )
    if supporting:
        clinical_overview += f"Key findings include: {'; '.join(supporting[:3])}."

    # ── Overall Impression ───────────────────────────────────────────────
    overall_impression = f"Based on available evidence, the most likely condition is {primary} with {confidence} confidence."
    if uncertainty:
        overall_impression += f" Diagnostic certainty is limited by: {'; '.join(uncertainty[:3])}."

    # ── Cardiac Summary ──────────────────────────────────────────────────
    risk = facts.get("risk_scores", {})
    cardiac_risk = risk.get("cardiac", 0)
    lab = facts.get("lab")
    if cardiac_risk >= 50:
        cardiac_summary = f"Cardiac risk is elevated at {cardiac_risk}/100. "
    elif cardiac_risk >= 30:
        cardiac_summary = f"Cardiac risk is moderate at {cardiac_risk}/100. "
    else:
        cardiac_summary = f"Cardiac risk is low at {cardiac_risk}/100. "

    if lab:
        pred = (lab.get("prediction") or "").replace("_", " ").title()
        prob = lab.get("risk_probability", 0) or 0
        cardiac_summary += f"Laboratory analysis indicates {pred} (probability: {prob*100:.1f}%)."
    else:
        cardiac_summary += "Laboratory cardiac analysis is not yet available."

    # ── Respiratory Summary ──────────────────────────────────────────────
    resp_risk = risk.get("respiratory", 0)
    imaging = facts.get("imaging")
    if resp_risk >= 50:
        respiratory_summary = f"Respiratory risk is elevated at {resp_risk}/100. "
    elif resp_risk >= 30:
        respiratory_summary = f"Respiratory risk is moderate at {resp_risk}/100. "
    else:
        respiratory_summary = f"Respiratory risk is low at {resp_risk}/100. "

    spo2_entry = next((v for v in facts.get("vitals_analysis", []) if v["parameter"] == "SpO₂"), None)
    if spo2_entry:
        respiratory_summary += f"Oxygen saturation is {spo2_entry['value']}%. "

    if imaging:
        img_pred = (imaging.get("prediction") or "").replace("_", " ").title()
        img_prob = imaging.get("pneumonia_probability", 0) or 0
        respiratory_summary += f"Chest imaging analysis: {img_pred} (pneumonia probability: {img_prob*100:.1f}%)."
    else:
        respiratory_summary += "Chest imaging analysis is not yet available."

    # ── Laboratory Summary ───────────────────────────────────────────────
    if lab:
        pred = (lab.get("prediction") or "").replace("_", " ").title()
        prob = lab.get("risk_probability", 0) or 0
        top = lab.get("top_features") or {}
        laboratory_summary = f"Laboratory analysis indicates {pred} with risk probability of {prob*100:.1f}%. "
        if top:
            top_names = [k.replace("_", " ").title() for k in list(top.keys())[:3]]
            laboratory_summary += f"Key contributing factors: {', '.join(top_names)}."
    else:
        laboratory_summary = "Laboratory AI analysis has not been performed for this patient. Interpretation is limited to clinical and imaging findings."

    # ── Imaging Summary ──────────────────────────────────────────────────
    if imaging:
        img_pred = (imaging.get("prediction") or "").replace("_", " ").title()
        img_prob = imaging.get("pneumonia_probability", 0) or 0
        img_conf = imaging.get("confidence", 0) or 0
        imaging_summary = (
            f"Chest radiograph analysis indicates {img_pred} with "
            f"pneumonia probability of {img_prob*100:.1f}% and "
            f"model confidence of {img_conf*100:.1f}%."
        )
    else:
        imaging_summary = "Medical imaging analysis has not been performed for this patient. This limits the ability to assess for pulmonary pathology."

    # ── Monitoring Narrative ─────────────────────────────────────────────
    if monitoring:
        mon_items = [f"{m['parameter']} ({m['reason']})" for m in monitoring[:4]]
        monitoring_narrative = f"The following parameters warrant close monitoring: {'; '.join(mon_items)}."
    else:
        monitoring_narrative = "Standard clinical observations are recommended."

    # ── Precautions Narrative ────────────────────────────────────────────
    if precautions:
        prec_items = [f"{p['action']}" for p in precautions[:4]]
        precautions_narrative = f"Clinical precautions include: {'; '.join(prec_items)}. These are safety-oriented observations and do not constitute treatment recommendations."
    else:
        precautions_narrative = "No specific clinical precautions beyond standard care."

    # ── Alternative Considerations ───────────────────────────────────────
    if alternatives:
        alt_names = [a["condition"] for a in alternatives[:3]]
        alt_text = f"Alternative conditions considered include: {', '.join(alt_names)}. "
    else:
        alt_text = "No significant alternative conditions identified. "

    if conflicting_ev:
        alt_text += f"Note: {'; '.join(conflicting_ev[:2])}. Further investigation may be appropriate."
    alternative_considerations_narrative = alt_text

    # ── Limitations Narrative ────────────────────────────────────────────
    missing = [l["source"] for l in limitations_list if not l.get("available", True)]
    if missing:
        limitations_narrative = (
            f"This assessment is based on incomplete data. "
            f"The following sources are unavailable: {', '.join(missing)}. "
            f"The absence of these inputs may reduce diagnostic certainty."
        )
    else:
        limitations_narrative = "This assessment is based on comprehensive data from all available clinical subsystems."

    return {
        "clinical_overview": clinical_overview.strip(),
        "overall_impression": overall_impression.strip(),
        "cardiac_summary": cardiac_summary.strip(),
        "respiratory_summary": respiratory_summary.strip(),
        "laboratory_summary": laboratory_summary.strip(),
        "imaging_summary": imaging_summary.strip(),
        "monitoring_narrative": monitoring_narrative.strip(),
        "precautions_narrative": precautions_narrative.strip(),
        "alternative_considerations_narrative": alternative_considerations_narrative.strip(),
        "limitations_narrative": limitations_narrative.strip(),
    }
