"""
PRATHAM Copilot — real patient context from Supabase, scoped by the caller's role.

The role scope is enforced HERE, before anything reaches the LLM: data the user
may not see is never placed in the prompt, so it cannot leak into an answer.

  nurse  → triage view: demographics, complaint, vitals, symptoms, severity,
           workflow status and investigation orders. No AI diagnosis output.
  doctor → full clinical picture incl. labs, imaging, differential, reports.
  admin  → no patient data at all; operational/aggregate metrics only.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.db.supabase_client import supabase

_UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def _rows(table: str, intake_id: str, order: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    q = supabase.table(table).select("*").eq("intake_id", intake_id)
    if order:
        q = q.order(order, desc=True)
    return q.limit(limit).execute().data or []


def resolve_intake(ref: Optional[str]) -> Optional[Dict[str, Any]]:
    """Accept either the intake UUID or the human case id (PRA-2026-XXXXXX)."""
    if not ref:
        return None
    ref = ref.strip()
    col = "id" if _UUID_RE.match(ref) else "case_id"
    data = supabase.table("emergency_intake").select("*").eq(col, ref).limit(1).execute().data
    return data[0] if data else None


def _age(dob: Optional[str]) -> Optional[int]:
    if not dob:
        return None
    try:
        born = datetime.fromisoformat(str(dob)[:10]).date()
    except ValueError:
        return None
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _true_flags(row: Dict[str, Any], skip=("id", "intake_id")) -> List[str]:
    return [k for k, v in row.items() if k not in skip and v is True]


def _build_triage(intake: Dict[str, Any]) -> Dict[str, Any]:
    iid = intake["id"]
    patient: Dict[str, Any] = {}
    if intake.get("patient_id"):
        p = supabase.table("patients").select("*").eq("id", intake["patient_id"]).limit(1).execute().data
        patient = p[0] if p else {}
    vitals = _rows("vitals", iid, "recorded_at", 1)
    symptoms = _rows("symptoms", iid, None, 1)
    risk = _rows("risk_scores", iid, "created_at", 1)
    invs = _rows("investigation_recommendations", iid, "created_at", 30)
    wf = _rows("workflow_logs", iid, "changed_at", 8)
    v = vitals[0] if vitals else {}
    return {
        "case_id": intake.get("case_id"),
        "patient": {
            "name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or "Unknown",
            "age": _age(patient.get("date_of_birth")),
            "sex": patient.get("gender"),
            "allergies": patient.get("allergies") or [],
            "current_medications": patient.get("current_medications") or [],
            "past_medical_history": patient.get("past_medical_history") or [],
        },
        "arrival": {"type": intake.get("arrival_type"), "ambulance_eta_min": intake.get("ambulance_eta")},
        "chief_complaint": intake.get("chief_complaint"),
        "emergency_description": intake.get("emergency_description"),
        "triage_severity": intake.get("severity_level"),
        "workflow_status": intake.get("status"),
        "vitals": {
            "heart_rate": v.get("heart_rate"),
            "spo2": v.get("spo2"),
            "bp": f"{v.get('bp_systolic')}/{v.get('bp_diastolic')}" if v.get("bp_systolic") else None,
            "temperature": v.get("temperature"),
            "respiratory_rate": v.get("respiratory_rate"),
            "recorded_at": v.get("recorded_at"),
        },
        "reported_symptoms": _true_flags(symptoms[0]) if symptoms else [],
        "triage_risk_scores": {
            k: risk[0].get(k)
            for k in ("cardiac_risk", "respiratory_risk", "trauma_risk", "neurological_risk", "overall_severity")
        }
        if risk
        else {},
        "investigations": [
            {"type": i.get("investigation_type"), "status": i.get("status"), "doctor_notes": i.get("doctor_notes")}
            for i in invs
        ],
        "workflow_history": [
            {"at": w.get("changed_at"), "to": w.get("new_status"), "by": w.get("actor_name"), "reason": w.get("reason")}
            for w in wf
        ],
    }


def _build_clinical(intake: Dict[str, Any]) -> Dict[str, Any]:
    iid = intake["id"]
    ctx = _build_triage(intake)
    agg = _rows("aggregation_results", iid, "created_at", 1)
    labs = _rows("lab_results", iid, "created_at", 1)
    img = _rows("imaging_results", iid, "created_at", 1)
    nlp = _rows("nlp_extractions", iid, "created_at", 1)
    ctx["nlp_findings"] = {
        "flags": _true_flags(nlp[0]) if nlp else [],
        "entities": nlp[0].get("extracted_entities") if nlp else [],
    }
    if agg:
        a = agg[0]
        ctx["differential"] = {
            "primary_condition": a.get("primary_condition"),
            "probabilities": {
                "ACS": a.get("acs_probability"),
                "PE": a.get("pe_probability"),
                "Pneumonia": a.get("pneumonia_probability"),
                "Arrhythmia": a.get("arrhythmia_probability"),
                "Other": a.get("other_probability"),
            },
            "confidence_suppressed": a.get("confidence_suppressed"),
            "suppression_reason": a.get("suppression_reason"),
            "evidence_breakdown": a.get("evidence_breakdown_json"),
        }
    if labs:
        l = labs[0]
        shap = l.get("shap_values") or {}
        top = sorted(shap.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
        ctx["lab_model"] = {
            "risk_label": l.get("risk_label"),
            "cardiac_risk_score": l.get("cardiac_risk_score"),
            "risk_probability": l.get("risk_probability"),
            "prediction": l.get("prediction"),
            "input_features": l.get("input_features"),
            "top_contributing_features": dict(top),
        }
    if img:
        i = img[0]
        ctx["imaging_model"] = {
            "prediction": i.get("prediction"),
            "pneumonia_probability": i.get("pneumonia_probability"),
            "confidence": i.get("confidence") or i.get("confidence_level"),
        }
    ev = (
        supabase.table("evidence").select("evidence_type,file_name,uploaded_at").eq("intake_id", iid).limit(20).execute().data
        or []
    )
    ctx["uploaded_evidence"] = ev
    return ctx


def _build_admin_overview() -> Dict[str, Any]:
    intakes = supabase.table("emergency_intake").select("status,severity_level").limit(2000).execute().data or []
    invs = supabase.table("investigation_recommendations").select("status").limit(5000).execute().data or []
    pipe = supabase.table("pipeline_status").select("stage,status").limit(2000).execute().data or []
    return {
        "note": "Aggregate operational metrics only. No patient-identifiable data.",
        "total_intakes": len(intakes),
        "intakes_by_status": dict(Counter(i.get("status") for i in intakes)),
        "intakes_by_severity": dict(Counter(i.get("severity_level") for i in intakes)),
        "investigations_by_status": dict(Counter(i.get("status") for i in invs)),
        "pipeline_stage_status": dict(Counter(f"{p.get('stage')}:{p.get('status')}" for p in pipe)),
    }


def _build_queue_overview() -> Dict[str, Any]:
    rows = (
        supabase.table("emergency_intake")
        .select("case_id,status,severity_level,chief_complaint")
        .order("created_at", desc=True)
        .limit(15)
        .execute()
        .data
        or []
    )
    return {"recent_cases": rows, "note": "No patient selected; showing the most recent cases."}


def build_case_context(role: str, intake_ref: Optional[str]) -> Dict[str, Any]:
    """Return {'scope','data','intake_found'}, filtered for ``role``."""
    if role == "admin":
        return {"scope": "admin_aggregate", "data": _build_admin_overview(), "intake_found": False}

    intake = resolve_intake(intake_ref)
    if not intake:
        return {"scope": f"{role}_no_patient", "data": _build_queue_overview(), "intake_found": False}

    if role == "doctor":
        return {"scope": "doctor_full", "data": _build_clinical(intake), "intake_found": True, "intake_id": intake["id"]}
    return {"scope": "nurse_triage", "data": _build_triage(intake), "intake_found": True, "intake_id": intake["id"]}
