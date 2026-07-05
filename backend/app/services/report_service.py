"""
report_service.py — Single Source of Truth for Clinical Report Data

Both the JSON report endpoint and the PDF export endpoint call
`get_complete_report(intake_id)`. This avoids duplicating database
queries or report-building logic across endpoints.

Architecture (PRATHAM v1):
    1. Fetch raw data from all DB tables.
    2. Build the legacy-compatible report dict.
    3. Run clinical_reasoning_service → Clinical Evidence Object (facts + conclusions).
    4. Run interpretation_service → LLM narrative (or fallback).
    5. Assemble unified 17-section Report DTO.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.db.supabase_client import supabase

logger = logging.getLogger(__name__)

# ── Version constants ────────────────────────────────────────────────────────
PRATHAM_VERSION = "1.0"

# ── Helpers ──────────────────────────────────────────────────────────────────

SYMPTOM_LABEL_MAP: Dict[str, str] = {
    "chest_pain": "Chest Pain",
    "breathlessness": "Breathlessness",
    "trauma": "Trauma",
    "bleeding": "Bleeding",
    "unconsciousness": "Unconsciousness",
    "neurological_symptoms": "Neurological Symptoms",
}


def _build_display_name(patient_row: dict | None) -> str:
    row = patient_row or {}
    first = (row.get("first_name") or "").strip()
    last = (row.get("last_name") or "").strip()
    if last and last != first:
        return f"{first} {last}".strip() or "Unknown"
    return first or "Unknown"


def _compute_age(dob: str | None) -> int:
    if not dob:
        return 0
    if "-" in str(dob):
        try:
            return max(0, datetime.now().year - int(str(dob).split("-")[0]))
        except (ValueError, IndexError):
            pass
    try:
        return int(dob)
    except (TypeError, ValueError):
        return 0


# ── Core function ────────────────────────────────────────────────────────────

async def get_complete_report(intake_id: str) -> Dict[str, Any]:
    """
    Fetch and assemble the complete clinical intelligence report
    for a given intake_id.  Returns the unified 17-section Report DTO.

    Raises ValueError if the intake is not found.
    """

    # ── 1. Intake + Patient + Vitals + Symptoms + Risk ────────────────
    intake_res = (
        supabase.table("emergency_intake")
        .select(
            "id, status, created_at, severity_level, "
            "emergency_description, chief_complaint, ambulance_eta, "
            "patients(id, first_name, last_name, gender, date_of_birth, "
            "contact_number, allergies, current_medications, past_medical_history), "
            "vitals(heart_rate, spo2, bp_systolic, bp_diastolic, temperature, respiratory_rate), "
            "symptoms(chest_pain, breathlessness, trauma, bleeding, unconsciousness, neurological_symptoms), "
            "risk_scores(cardiac_risk, respiratory_risk, trauma_risk, neurological_risk, overall_severity)"
        )
        .eq("id", intake_id)
        .execute()
    )

    if not intake_res.data:
        raise ValueError(f"Intake {intake_id} not found")

    intake = intake_res.data[0]
    patient_row = intake.get("patients") or {}
    vitals_rows = intake.get("vitals") or []
    vitals_row = vitals_rows[0] if vitals_rows else {}
    syms_rows = intake.get("symptoms") or []
    syms_row = syms_rows[0] if syms_rows else {}
    risk_rows = intake.get("risk_scores") or []
    risk_row = risk_rows[0] if risk_rows else {}

    name = _build_display_name(patient_row)
    gender = (patient_row.get("gender") or "").lower()
    age = _compute_age(patient_row.get("date_of_birth"))

    bp_sys = vitals_row.get("bp_systolic")
    bp_dia = vitals_row.get("bp_diastolic")
    bp_str = f"{int(bp_sys)}/{int(bp_dia)}" if bp_sys and bp_dia else "—"

    symptom_list = [
        label for field, label in SYMPTOM_LABEL_MAP.items()
        if syms_row.get(field)
    ]

    severity = (risk_row.get("overall_severity") or "moderate").lower()

    # ── 2–6. Fetch independent AI + evidence data in parallel ────────

    def _fetch_nlp():
        try:
            res = supabase.table("nlp_extractions").select("*").eq("intake_id", intake_id).limit(1).execute()
            return res.data[0] if res.data else {}
        except Exception:
            return {}

    def _fetch_lab():
        try:
            res = supabase.table("lab_results").select("*").eq("intake_id", intake_id).order("created_at", desc=True).limit(1).execute()
            return res.data[0] if res.data else None
        except Exception:
            return None

    def _fetch_imaging():
        try:
            res = supabase.table("imaging_results").select("*").eq("intake_id", intake_id).order("created_at", desc=True).limit(1).execute()
            return res.data[0] if res.data else None
        except Exception:
            return None

    def _fetch_agg():
        try:
            res = supabase.table("aggregation_results").select("*").eq("intake_id", intake_id).order("created_at", desc=True).limit(1).execute()
            return res.data[0] if res.data else None
        except Exception:
            return None

    def _fetch_evidence():
        try:
            res = supabase.table("evidence").select("id, evidence_type, file_name, file_url, uploaded_at").eq("intake_id", intake_id).order("uploaded_at", desc=True).execute()
            return res.data or []
        except Exception:
            return []

    def _fetch_investigations():
        try:
            res = supabase.table("investigation_recommendations").select(
                "id, investigation_type, evidence_type, status, review_notes"
            ).eq("intake_id", intake_id).execute()
            return res.data or []
        except Exception:
            return []

    nlp_data, lab_data, imaging_data, agg_data, evidence_list, investigations = await asyncio.gather(
        asyncio.to_thread(_fetch_nlp),
        asyncio.to_thread(_fetch_lab),
        asyncio.to_thread(_fetch_imaging),
        asyncio.to_thread(_fetch_agg),
        asyncio.to_thread(_fetch_evidence),
        asyncio.to_thread(_fetch_investigations),
    )

    nlp_flags = {
        "chest_pain": syms_row.get("chest_pain", False),
        "breathlessness": syms_row.get("breathlessness", False),
        "cardiac_risk_flag": nlp_data.get("cardiac_risk_flag", False),
        "respiratory_distress": nlp_data.get("respiratory_distress", False),
        "head_trauma": nlp_data.get("head_trauma", False),
        "loss_of_consciousness": nlp_data.get("loss_of_consciousness", False),
        "neurological_risk_flag": nlp_data.get("neurological_risk_flag", False),
    }
    nlp_entities = nlp_data.get("extracted_entities") or []
    nlp_summary = ""
    raw_llm = nlp_data.get("raw_llm_output")
    if isinstance(raw_llm, dict):
        nlp_summary = raw_llm.get("clinical_summary", "")

    # Fetch the original X-ray URL if imaging has evidence_id
    xray_url = ""
    if imaging_data and imaging_data.get("evidence_id"):
        try:
            ev_res = (
                supabase.table("evidence")
                .select("file_url")
                .eq("id", imaging_data["evidence_id"])
                .limit(1)
                .execute()
            )
            if ev_res.data:
                xray_url = ev_res.data[0].get("file_url", "")
        except Exception:
            pass

    # ── 7. Pipeline status ───────────────────────────────────────────
    from app.services.pipeline_status_service import get_pipeline_status
    try:
        pipeline_data = get_pipeline_status(intake_id)
        pipeline_status = {
            stage: info["status"]
            for stage, info in pipeline_data["stages"].items()
        }
    except Exception:
        pipeline_status = {
            "nlp": "completed" if nlp_data else "pending",
            "risk": "completed" if risk_row else "pending",
            "lab": "completed" if lab_data else "pending",
            "imaging": "completed" if imaging_data else "pending",
            "aggregation": "completed" if agg_data else "pending",
        }

    # Parse aggregation probabilities
    probabilities: Dict[str, Optional[float]] = {}
    evidence_breakdown: Dict[str, List[str]] = {}
    source_summary: Dict[str, bool] = {}
    if agg_data:
        probability_columns = {
            "ACS": ("acs_probability", "prob_acs"),
            "PE": ("pe_probability", "prob_pe"),
            "Pneumonia": ("pneumonia_probability", "prob_pneumonia"),
            "Arrhythmia": ("arrhythmia_probability", "prob_arrhythmia"),
            "Other": ("other_probability", "prob_other"),
        }
        for cond, keys in probability_columns.items():
            val = None
            for key in keys:
                if agg_data.get(key) is not None:
                    val = agg_data.get(key)
                    break
            probabilities[cond] = float(val) if val is not None else None
        try:
            eb = agg_data.get("evidence_breakdown_json")
            if isinstance(eb, str):
                evidence_breakdown = json.loads(eb)
            elif isinstance(eb, dict):
                evidence_breakdown = eb
        except Exception:
            pass
        try:
            ss = agg_data.get("source_summary_json")
            if isinstance(ss, str):
                source_summary = json.loads(ss)
            elif isinstance(ss, dict):
                source_summary = ss
        except Exception:
            pass

    created = intake.get("created_at", "")

    # ── Build the base report data (backward-compatible) ─────────────
    base_report = {
        "intake_id": intake_id,
        "generated_at": datetime.now().isoformat(),

        "patient_summary": {
            "patient_id": patient_row.get("id"),
            "name": name,
            "age": age,
            "gender": gender,
            "contact": patient_row.get("contact_number"),
            "chief_complaint": intake.get("chief_complaint", ""),
            "emergency_description": intake.get("emergency_description", ""),
            "ambulance_eta": intake.get("ambulance_eta", ""),
            "severity": severity,
            "allergies": patient_row.get("allergies") or [],
            "medications": patient_row.get("current_medications") or [],
            "medical_history": patient_row.get("past_medical_history") or [],
            "arrival_time": str(created)[11:16] if created and len(str(created)) >= 16 else "",
        },

        "vitals": {
            "heart_rate": vitals_row.get("heart_rate"),
            "spo2": vitals_row.get("spo2"),
            "bp_systolic": bp_sys,
            "bp_diastolic": bp_dia,
            "blood_pressure": bp_str,
            "temperature": vitals_row.get("temperature"),
            "respiratory_rate": vitals_row.get("respiratory_rate"),
        },

        "symptoms": symptom_list,

        "nlp_findings": {
            "flags": nlp_flags,
            "entities": nlp_entities,
            "summary": nlp_summary,
        },

        "risk_engine": {
            "cardiac": risk_row.get("cardiac_risk", 0) or 0,
            "respiratory": risk_row.get("respiratory_risk", 0) or 0,
            "trauma": risk_row.get("trauma_risk", 0) or 0,
            "neurological": risk_row.get("neurological_risk", 0) or 0,
            "severity": severity,
        },

        "lab_intelligence": {
            "available": lab_data is not None,
            "model_name": lab_data.get("model_name") if lab_data else None,
            "prediction": lab_data.get("prediction") if lab_data else None,
            "risk_probability": lab_data.get("risk_probability") if lab_data else None,
            "top_features": lab_data.get("top_features") if lab_data else None,
            "shap_values": lab_data.get("shap_values") if lab_data else None,
            "created_at": lab_data.get("created_at") if lab_data else None,
        },

        "lab_evaluations": (
            __import__("app.services.lab_intelligence_service", fromlist=["evaluate_lab_panel"])
            .evaluate_lab_panel(lab_data.get("top_features") if lab_data else None)
            .get("evaluations", [])
        ),

        "imaging_intelligence": {
            "available": imaging_data is not None,
            "model_name": imaging_data.get("model_name") if imaging_data else None,
            "prediction": imaging_data.get("prediction") if imaging_data else None,
            "pneumonia_probability": imaging_data.get("pneumonia_probability") if imaging_data else None,
            "confidence": imaging_data.get("confidence") if imaging_data else None,
            "xray_url": xray_url,
            "gradcam_url": imaging_data.get("gradcam_url", "") if imaging_data else "",
            "created_at": imaging_data.get("created_at") if imaging_data else None,
        },

        "aggregation": {
            "available": agg_data is not None,
            "primary_condition": agg_data.get("primary_condition") if agg_data else None,
            "confidence_suppressed": agg_data.get("confidence_suppressed") if agg_data else None,
            "suppression_reason": agg_data.get("suppression_reason") if agg_data else None,
            "probabilities": probabilities,
            "evidence_breakdown": evidence_breakdown,
            "source_summary": source_summary,
        },

        "evidence": evidence_list,
        "pipeline_status": pipeline_status,
        "investigations": investigations,
    }

    # ── 8. Clinical Reasoning + Interpretation ───────────────────────
    from app.services.clinical_reasoning_service import build_clinical_evidence
    from app.services.interpretation_service import generate_clinical_interpretation

    try:
        clinical_evidence = build_clinical_evidence(base_report)
        interpretation = generate_clinical_interpretation(clinical_evidence)
    except Exception as exc:
        logger.error("[PRATHAM] Clinical reasoning/interpretation failed: %s", exc)
        clinical_evidence = {"facts": {}, "conclusions": {}}
        interpretation = {}

    # ── 9. Assemble the unified Report DTO ───────────────────────────
    conclusions = clinical_evidence.get("conclusions", {})

    base_report["clinical_interpretation"] = interpretation
    base_report["clinical_conclusions"] = conclusions
    base_report["report_version"] = PRATHAM_VERSION
    base_report["clinical_audit_log"] = {
        "report_generated_at": datetime.now().isoformat(),
        "generated_by": f"PRATHAM v{PRATHAM_VERSION}",
        "evidence_sources": [k for k, v in conclusions.get("data_completeness", {}).items() if v.get("available")],
        "pipeline_integrity": conclusions.get("report_quality", {}).get("pipeline_integrity", "PASS"),
    }

    return base_report
