
"""
GET  /api/investigations/pending  — Fetch all pending-approval intakes for doctor queue
POST /api/investigations/approve  — Doctor investigation approval endpoint
POST /api/investigations/reject   — Doctor investigation rejection endpoint
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.domains.triage.repository import intake_repository
from app.domains.investigation.repository import investigation_repository
from app.domains.evidence.repository import evidence_repository
from app.domains.workflow.repository import workflow_repository
# pipeline_repository removed — no routes in this module use it directly (main.py/admin.py import it independently)
from app.domains.ai.repository import (
    lab_results_repository,
    imaging_results_repository,
    aggregation_results_repository,
    nlp_repository,
)
from app.models.workflow import WorkflowStatus
from app.services.workflow_service import (
    check_and_update_patient_lifecycle,
    update_workflow_status,
)
from app.services.doctor_dashboard_service import get_dashboard_stats
from app.services.investigation_stats_service import get_queue_stats as _get_queue_stats_service
from app.services.doctor_review_service import get_doctor_review_list
from app.services.doctor_reports_service import get_reports_list
from app.services.registry_service import get_patient_registry
from app.services.pending_approvals_service import get_pending_approvals as _get_pending_approvals
from app.services.investigation_history_service import get_investigation_history as _get_investigation_history
from app.services.patient_queue_service import get_queue_items as _get_queue_items
from app.services.investigation_approval_service import (
    approve as _approve_service,
    reject as _reject_service,
    needs_info as _needs_info_service,
    add_investigation as _add_investigation_service,
    recommend_investigation as _recommend_investigation_service,
    check_update_eligibility as _check_update_eligibility_service,
    update_investigations as _update_investigations_service,
)
from app.services.case_lifecycle_service import (
    confirm_arrival as _confirm_arrival_service,
    close_case as _close_case_service,
    return_to_nurse as _return_to_nurse_service,
)
from app.utils.patient_utils import (
    compute_age as _compute_age,
    build_display_name as _build_display_name_util,
    derive_sex,
    extract_arrival_time,
    derive_severity as _derive_severity_util,
    derive_urgency as _derive_urgency_util,
    SYMPTOM_LABEL_MAP as _SYMPTOM_LABEL_MAP_UTIL,
)
from app.domains.shared.utils.evidence_mapping import get_evidence_type  # P5 — replaces api/evidence.py cross-import

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_display_name(patient_row: dict | None) -> str:
    """Thin wrapper; delegates to shared utility."""
    return _build_display_name_util(patient_row)



# ── Request / Response models ────────────────────────────────────────────────

class ApprovalRequest(BaseModel):
    intake_id: str
    approved_tests: List[str]
    custom_tests: Optional[List[str]] = []
    doctor_notes: Optional[str] = None
    doctor_name: Optional[str] = "Unknown Doctor"


class ApprovalResponse(BaseModel):
    intake_id: str
    approved_count: int
    status: str


class RejectRequest(BaseModel):
    intake_id: str
    doctor_notes: Optional[str] = None
    doctor_name: Optional[str] = "Unknown Doctor"


class NeedsInfoRequest(BaseModel):
    intake_id: str
    doctor_notes: Optional[str] = None
    doctor_name: Optional[str] = "Unknown Doctor"


class UpdateInvestigationsRequest(BaseModel):
    intake_id: str
    approved_tests: List[str]
    custom_tests: Optional[List[str]] = []
    doctor_notes: Optional[str] = None
    doctor_name: Optional[str] = "Unknown Doctor"


# ── Helpers (thin wrappers — implementations live in patient_utils) ───────────

SYMPTOM_LABEL_MAP: Dict[str, str] = _SYMPTOM_LABEL_MAP_UTIL


def _derive_severity(risk: Dict[str, Any] | None) -> str:
    """Delegates to patient_utils.derive_severity."""
    return _derive_severity_util(risk)


def _derive_urgency(severity: str) -> str:
    """Delegates to patient_utils.derive_urgency."""
    return _derive_urgency_util(severity)


def _storage_path_from_file_url(file_url: str | None) -> str:
    """Extract the Supabase Storage object path from a signed evidence URL."""
    if not file_url:
        return ""
    if "/evidence/" not in file_url:
        return ""
    path_part = file_url.split("/evidence/", 1)[-1]
    if "?" in path_part:
        path_part = path_part.split("?", 1)[0]
    return path_part


# _has_row removed — zero callers confirmed (Part F, Phase 2 Final Sprint)






# ── GET pending approvals for the doctor queue ───────────────────────────────

@router.get("/investigations/pending", tags=["Investigations"])
async def get_pending_approvals():
    """
    Returns all patients with pending_approval investigations,
    joined with patient info, vitals, symptoms, and risk scores.
    This is what the doctor approvals page fetches on load.
    """
    try:
        return _get_pending_approvals()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ── GET investigation history — all statuses, 72h retention window ───────────

@router.get("/investigations/history", tags=["Investigations"])
async def get_investigation_history(status: str = None):
    """
    Returns investigation history for the doctor notifications panel.
    Includes all statuses (approved, rejected, needs_info, pending_approval)
    within a 72-hour retention window.

    Optional query param:
      status: filter by one of 'approved', 'rejected', 'needs_info',
              'pending_approval'. Invalid or absent values return all records.

    Frontend: frontend/src/lib/case-store.tsx calls this on mount;
              falls back to /investigations/pending if this returns 404.
    """
    try:
        return _get_investigation_history(status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST approve ─────────────────────────────────────────────────────────────

# _safe_update and _safe_insert shims removed — logic lives in investigation_approval_service (Part F, Phase 2 Final Sprint)


@router.post("/investigations/approve", response_model=ApprovalResponse, tags=["Investigations"])
async def approve_investigations(data: ApprovalRequest) -> ApprovalResponse:
    """
    Doctor approves selected investigations for a patient intake.
    Unselected pending tests are auto-rejected.
    Workflow status always transitions to APPROVED (investigations_approved),
    completing the "Doctor Approval" milestone.
    """
    try:
        result = _approve_service(
            intake_id=data.intake_id,
            approved_tests=data.approved_tests,
            custom_tests=data.custom_tests or [],
            doctor_name=data.doctor_name or "Unknown Doctor",
            doctor_notes=data.doctor_notes,
        )
        return ApprovalResponse(
            intake_id=result["intake_id"],
            approved_count=result["approved_count"],
            status=result["status"],
        )
    except Exception as e:
        logger.exception("[PRATHAM] Approve investigations failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── POST reject ──────────────────────────────────────────────────────────────

@router.post("/investigations/reject", tags=["Investigations"])
async def reject_investigations(data: RejectRequest):
    """
    Doctor rejects recommended investigations.
    """
    try:
        return _reject_service(
            intake_id=data.intake_id,
            doctor_notes=data.doctor_notes,
            doctor_name=data.doctor_name or "Doctor",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST needs_info ──────────────────────────────────────────────────────────

@router.post("/investigations/needs-info", tags=["Investigations"])
async def needs_info_investigations(data: NeedsInfoRequest):
    """
    Doctor requests more information for a patient intake's investigations.
    """
    try:
        return _needs_info_service(intake_id=data.intake_id, doctor_notes=data.doctor_notes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET update eligibility — check if approved investigations can be modified ─

@router.get("/investigations/{intake_id}/update-eligibility", tags=["Investigations"])
async def get_update_eligibility(intake_id: str):
    """
    Check whether an approved patient's investigations can be updated.

    Returns eligibility status, reason, and current investigation list
    (pre-populated with approved/rejected state) for the update editor.

    This is UI information only — the POST /investigations/update endpoint
    independently re-verifies eligibility before mutating.
    """
    try:
        return _check_update_eligibility_service(intake_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST update — modify approved investigation decisions ────────────────────

@router.post("/investigations/update", response_model=ApprovalResponse, tags=["Investigations"])
async def update_investigations(data: UpdateInvestigationsRequest) -> ApprovalResponse:
    """
    Update investigation decisions for an already-approved case.

    Pre-checks (re-verified independently, never trusts GET result):
        - Canonical workflow status must be investigations_approved
        - Evidence count must be 0
        - Downstream pipeline stages must be pending/failed

    Returns 409 if the case is no longer eligible for update.
    Returns 500 on mutation failure.
    """
    try:
        result = _update_investigations_service(
            intake_id=data.intake_id,
            approved_tests=data.approved_tests,
            custom_tests=data.custom_tests or [],
            doctor_name=data.doctor_name or "Unknown Doctor",
            doctor_notes=data.doctor_notes,
        )
        return ApprovalResponse(
            intake_id=result["intake_id"],
            approved_count=result["approved_count"],
            status=result["status"],
        )
    except ValueError as ve:
        # Eligibility failure — 409 Conflict
        raise HTTPException(status_code=409, detail=str(ve))
    except Exception as e:
        logger.exception("[PRATHAM] Update investigations failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── GET patient queue — lightweight summary for nurse list ────────────────────

@router.get("/investigations/queue", tags=["Investigations"])
async def get_patient_queue():
    """
    Lightweight patient queue for the nurse workstation.
    Returns one entry per active intake.
    """
    try:
        return await _get_queue_items()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET queue stats — lightweight badge data for sidebar ──────────────────────

@router.get("/investigations/queue/stats", tags=["Investigations"])
async def get_queue_stats():
    """
    Lightweight stats for sidebar badges.
    Returns total patient count and how many have pending-approval investigations.
    """
    try:
        return _get_queue_stats_service()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET patient timeline ──────────────────────────────────────────────────────

@router.get("/investigations/patient/{intake_id}/timeline", tags=["Investigations"])
async def get_patient_timeline(intake_id: str):
    """
    Patient journey timeline reconstructed from existing database timestamps.
    Returns a chronologically sorted list of events.
    """
    from app.services.workflow_service import build_patient_timeline
    return await asyncio.to_thread(build_patient_timeline, intake_id)


# ── GET patient detail — full workspace data for a single intake ──────────────

@router.get("/investigations/patient/{intake_id}", tags=["Investigations"])
async def get_patient_detail(intake_id: str):
    """
    Full patient detail for the nurse workspace.
    Returns demographics, vitals, symptoms, risk scores, and every investigation
    with its status, expected evidence_type (from backend mapping), and all
    uploaded evidence files.
    """
    try:
        # 1. Fetch intake with all related rows
        intake = intake_repository.get_by_id(
            intake_id,
            columns=(
                "id, status, created_at, severity_level, "
                "emergency_description, chief_complaint, ambulance_eta, "
                "patients(id, first_name, last_name, gender, date_of_birth, contact_number), "
                "vitals(heart_rate, spo2, bp_systolic, bp_diastolic, temperature, respiratory_rate), "
                "symptoms(chest_pain, breathlessness, trauma, bleeding, unconsciousness, neurological_symptoms), "
                "risk_scores(cardiac_risk, respiratory_risk, trauma_risk, neurological_risk, overall_severity)"
            ),
        )

        if not intake:
            raise HTTPException(status_code=404, detail="Intake not found")



        # 2–3. Fetch investigations, evidence, and AI results in parallel
        import asyncio

        def _fetch_inv():
            return investigation_repository.get_by_intake_id_with_columns(
                intake_id,
                columns="id, investigation_type, status, approved_at, rejected_at, review_notes, created_at",
            )

        def _fetch_ev():
            try:
                return evidence_repository.get_by_intake_id_with_columns(
                    intake_id,
                    columns="id, evidence_type, file_url, file_name, uploaded_at, investigation_id",
                    order_by="uploaded_at",
                    desc=True,
                )
            except Exception:
                return evidence_repository.get_by_intake_id_with_columns(
                    intake_id,
                    columns="id, evidence_type, file_url, file_name, uploaded_at",
                    order_by="uploaded_at",
                    desc=True,
                )

        def _fetch_lab():
            try:
                return lab_results_repository.get_latest(
                    intake_id,
                    columns="id, model_name, prediction, risk_probability, shap_values, input_features, created_at",
                )
            except Exception:
                return None

        def _fetch_imaging():
            try:
                try:
                    return imaging_results_repository.get_latest(
                        intake_id,
                        columns="id, model_name, prediction, pneumonia_probability, confidence, created_at, evidence_id, gradcam_url",
                    )
                except Exception:
                    return imaging_results_repository.get_latest(
                        intake_id,
                        columns="id, model_name, prediction, pneumonia_probability, confidence, created_at, evidence_id",
                    )
            except Exception:
                return None

        def _fetch_agg():
            try:
                return aggregation_results_repository.get_by_intake_id(intake_id)
            except Exception:
                return None

        def _fetch_nlp():
            try:
                return nlp_repository.get_by_intake_id(intake_id)
            except Exception:
                return None

        def _fetch_pipeline():
            try:
                from app.services.pipeline_status_service import get_pipeline_status_flat
                return get_pipeline_status_flat(intake_id)
            except Exception:
                return {"nlp": "pending", "risk": "pending", "lab": "pending", "imaging": "pending", "aggregation": "pending"}

        inv_data, ev_data, lab_result, imaging_result, aggregation_result, nlp_result, pipeline_status = await asyncio.gather(
            asyncio.to_thread(_fetch_inv),
            asyncio.to_thread(_fetch_ev),
            asyncio.to_thread(_fetch_lab),
            asyncio.to_thread(_fetch_imaging),
            asyncio.to_thread(_fetch_agg),
            asyncio.to_thread(_fetch_nlp),
            asyncio.to_thread(_fetch_pipeline),
        )

        evidence_rows = ev_data

        # Build evidence lookup indexes
        # ev_by_inv_id  : investigation_id  → [evidence rows]  (exact/linked match)
        # ev_by_type    : evidence_type     → [evidence rows]  (unlinked/legacy rows)
        ev_by_inv_id: Dict[str, List[Dict]] = {}
        ev_by_type: Dict[str, List[Dict]] = {}
        for ev in evidence_rows:
            linked_inv_id = ev.get("investigation_id")
            ev_type = ev.get("evidence_type", "")
            if linked_inv_id:
                ev_by_inv_id.setdefault(linked_inv_id, []).append(ev)
            else:
                # Unlinked evidence (investigation_id IS NULL) — filed by type
                # so we can distribute it to the right investigation later.
                ev_by_type.setdefault(ev_type, []).append(ev)

        inv_list = inv_data
        evidence_type_counts: Dict[str, int] = {}
        for inv in inv_list:
            inv_evidence_type = get_evidence_type(inv.get("investigation_type", ""))
            evidence_type_counts[inv_evidence_type] = evidence_type_counts.get(inv_evidence_type, 0) + 1

        # Track which unlinked evidence IDs have been claimed
        claimed_ev_ids: set = set()

        # 4. Build per-investigation entries
        approved_count = 0
        uploaded_count = 0
        investigations: List[Dict[str, Any]] = []

        for inv in inv_list:
            inv_id = inv["id"]
            inv_type = inv.get("investigation_type", "")
            inv_status = inv.get("status", "")
            evidence_type = get_evidence_type(inv_type)

            # Evidence: prefer investigation_id lookup (exact/linked match)
            inv_evidence = ev_by_inv_id.get(inv_id, [])

            # Fallback for unlinked evidence (investigation_id IS NULL):
            # Assign one unclaimed file per approved investigation that needs one.
            # This distributes files fairly when investigation_id column is missing.
            if not inv_evidence and inv_status == "approved":
                fallback = ev_by_type.get(evidence_type, [])
                unclaimed = [e for e in fallback if e.get("id") not in claimed_ev_ids]
                if unclaimed:
                    # Take just the first unclaimed file for this investigation
                    inv_evidence = [unclaimed[0]]

            # Mark every file assigned to this investigation as claimed
            for e in inv_evidence:
                eid = e.get("id")
                if eid:
                    claimed_ev_ids.add(eid)

            # Compute 3-state progress (only for approved investigations)
            if inv_status == "approved":
                approved_count += 1
                if inv_evidence:
                    progress = "uploaded"
                    uploaded_count += 1
                else:
                    progress = "awaiting_upload"
            else:
                progress = None

            # Attach analysis result if applicable
            analysis_result = None
            analysis_status = "not_applicable"
            if evidence_type == "xray" and imaging_result:
                analysis_result = {
                    "type": "imaging",
                    "model_name": imaging_result.get("model_name"),
                    "prediction": imaging_result.get("prediction"),
                    "probability": imaging_result.get("pneumonia_probability"),
                    "confidence": imaging_result.get("confidence"),
                    "created_at": imaging_result.get("created_at"),
                    "gradcam_url": imaging_result.get("gradcam_url", ""),
                }
                analysis_status = "completed"
            elif evidence_type == "lab_report" and lab_result:
                # Compute top_features safely from shap_values
                shaps = lab_result.get("shap_values")
                top_features = {}
                if isinstance(shaps, dict):
                    try:
                        sorted_shaps = sorted(
                            [item for item in shaps.items() if isinstance(item[1], (int, float))],
                            key=lambda kv: abs(kv[1]),
                            reverse=True
                        )
                        top_features = {k: round(v, 6) for k, v in sorted_shaps[:5]}
                    except Exception:
                        pass
                elif isinstance(shaps, list):
                    try:
                        # Handle list of dicts: [{"feature": "x", "value": 0.1}]
                        # or list of key-value pairs: [["x", 0.1]]
                        if all(isinstance(x, dict) for x in shaps):
                            sorted_shaps = sorted(
                                shaps,
                                key=lambda x: abs(x.get("value", 0)) if isinstance(x.get("value"), (int, float)) else 0,
                                reverse=True
                            )
                            for item in sorted_shaps[:5]:
                                feat_name = item.get("feature") or item.get("name")
                                feat_val = item.get("value") or item.get("shap") or 0
                                if feat_name:
                                    top_features[str(feat_name)] = round(float(feat_val), 6)
                        elif all(isinstance(x, (list, tuple)) and len(x) >= 2 for x in shaps):
                            sorted_shaps = sorted(
                                [x for x in shaps if isinstance(x[1], (int, float))],
                                key=lambda x: abs(x[1]),
                                reverse=True
                            )
                            for item in sorted_shaps[:5]:
                                top_features[str(item[0])] = round(float(item[1]), 6)
                    except Exception:
                        pass
                analysis_result = {
                    "type": "lab",
                    "model_name": lab_result.get("model_name"),
                    "prediction": lab_result.get("prediction"),
                    "probability": lab_result.get("risk_probability"),
                    "top_features": top_features,
                    "created_at": lab_result.get("created_at"),
                }
                analysis_status = "completed"
            elif evidence_type in ("xray", "lab_report"):
                analysis_status = "pending"

            investigations.append({
                "id": inv_id,
                "investigation_type": inv_type,
                "evidence_type": evidence_type,
                "status": inv_status,
                "progress": progress,
                "approved_at": inv.get("approved_at"),
                "rejected_at": inv.get("rejected_at"),
                "review_notes": inv.get("review_notes"),
                "analysis_result": analysis_result,
                "analysis_status": analysis_status,
                "evidence": [
                    {
                        "evidence_id": e.get("id"),
                        "file_name": e.get("file_name"),
                        "file_url": e.get("file_url", ""),
                        "storage_path": _storage_path_from_file_url(e.get("file_url", "")),
                        "uploaded_at": e.get("uploaded_at"),
                    }
                    for e in inv_evidence
                ],
            })

        # Collect unlinked evidence (uploaded but not matched to any investigation)
        exact_linked_ev_ids = {
            e.get("id")
            for linked_rows in ev_by_inv_id.values()
            for e in linked_rows
            if e.get("id")
        }
        unlinked_evidence = [
            {
                "evidence_id": e.get("id"),
                "evidence_type": e.get("evidence_type"),
                "file_name": e.get("file_name"),
                "file_url": e.get("file_url", ""),
                "storage_path": _storage_path_from_file_url(e.get("file_url", "")),
                "uploaded_at": e.get("uploaded_at"),
            }
            for e in evidence_rows
            if e.get("id") and e.get("id") not in claimed_ev_ids
               and e.get("id") not in exact_linked_ev_ids
        ]
        symptoms_raw = intake.get("symptoms") or []
        symptoms_dict = symptoms_raw[0] if isinstance(symptoms_raw, list) and symptoms_raw else (symptoms_raw if isinstance(symptoms_raw, dict) else {})
        symptom_labels = [
            label
            for field, label in SYMPTOM_LABEL_MAP.items()
            if symptoms_dict.get(field)
        ]

        created = intake.get("created_at", "")
        arrival = str(created)[11:16] if created and len(str(created)) >= 16 else ""
        eta = intake.get("ambulance_eta")

        completeness_label = (
            f"{uploaded_count} / {approved_count} complete"
            if approved_count > 0
            else "No approved investigations"
        )

        patient_row = intake.get("patients") or {}
        vitals_raw = intake.get("vitals") or []
        vitals_row = vitals_raw[0] if isinstance(vitals_raw, list) and vitals_raw else (vitals_raw if isinstance(vitals_raw, dict) else {})
        risk_row = (intake.get("risk_scores") or [{}])[0]
        
        name = _build_display_name(patient_row)
        gender = (patient_row.get("gender") or "").lower()
        age = _compute_age(patient_row.get("date_of_birth"))
        
        bp_systolic = vitals_row.get("bp_systolic")
        bp_diastolic = vitals_row.get("bp_diastolic")
        bp_str = f"{bp_systolic}/{bp_diastolic}" if bp_systolic and bp_diastolic else "—"

        # Resolve canonical workflow status (SSOT = workflow_logs)
        _raw_intake_status = intake.get("status", "")
        _canonical_status = workflow_repository.get_latest_status(intake_id) or _raw_intake_status

        return {
            "intake_id": intake_id,
            "intake_status": _raw_intake_status,
            "workflow_status": _canonical_status,
            "patient": {
                "name": name,
                "age": age,
                "sex": "M" if gender == "male" else "F",
                "gender": gender,
                "arrival_time": arrival,
                "eta": f"{eta} min" if eta else "—",
                "contact": patient_row.get("contact_number"),
                "chief_complaint": intake.get("chief_complaint", ""),
                "emergency_description": intake.get("emergency_description", ""),
            },
            "vitals": {
                "heart_rate": vitals_row.get("heart_rate"),
                "spo2": vitals_row.get("spo2"),
                "blood_pressure": bp_str,
                "respiratory_rate": vitals_row.get("respiratory_rate"),
                "temperature": vitals_row.get("temperature"),
            },
            "symptoms": symptom_labels,
            "risk": {
                "severity": _derive_severity(risk_row),
                "cardiac": risk_row.get("cardiac_risk", 0) or 0,
                "respiratory": risk_row.get("respiratory_risk", 0) or 0,
                "trauma": risk_row.get("trauma_risk", 0) or 0,
                "neurological": risk_row.get("neurological_risk", 0) or 0,
            },
            "investigations": investigations,
            "unlinked_evidence": unlinked_evidence,
            "pipeline_status": pipeline_status,
            "evidence_completeness": {
                "uploaded": uploaded_count,
                "required": approved_count,
                "label": completeness_label,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AddInvestigationRequest(BaseModel):
    intake_id: str
    investigation_name: str
    doctor_name: Optional[str] = "Doctor"
    doctor_notes: Optional[str] = "Manually added by doctor"

@router.post("/investigations/add", tags=["Investigations"])
async def add_investigation(data: AddInvestigationRequest):
    """
    Doctor manually adds and approves an investigation for a patient.
    Normalizes name, resolves aliases, inserts as approved with timestamp.
    """
    try:
        return _add_investigation_service(
            intake_id=data.intake_id,
            investigation_name=data.investigation_name,
            doctor_name=data.doctor_name or "Doctor",
            doctor_notes=data.doctor_notes or "Manually added by doctor",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST Manual Arrival Confirmation ──────────────────────────────────────────

class ArrivalConfirmRequest(BaseModel):
    intake_id: str
    actor_name: str

@router.post("/intake/arrival/confirm", tags=["Intake"])
async def confirm_arrival(data: ArrivalConfirmRequest):
    """
    Manually confirm the arrival of a patient.
    Transitions their state: (Current) -> Arrived -> Awaiting Doctor Approval.
    """
    success = _confirm_arrival_service(
        intake_id=data.intake_id,
        actor_name=data.actor_name,
    )
    if not success:
        raise HTTPException(status_code=400, detail="Invalid status transition to Arrived")
    return {"status": "success", "new_status": WorkflowStatus.AWAITING_APPROVAL.value}


# ── GET Workflow Transition Logs ──────────────────────────────────────────────

@router.get("/intake/{intake_id}/workflow-logs", tags=["Intake"])
async def get_workflow_logs(intake_id: str):
    """
    Fetch the list of status transitions (audit trail) for a patient case.
    """
    try:
        return workflow_repository.get_logs(intake_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET Permanent Historical Patient Registry ───────────────────────────────

@router.get("/intake/registry", tags=["Intake"])
async def get_registry():
    """
    Fetch permanent historical patient registry list.
    """
    try:
        return get_patient_registry()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── POST Close Case ───────────────────────────────────────────────────────────

class CloseCaseRequest(BaseModel):
    actor_name: str
    reason: Optional[str] = "Doctor marked case as closed."

@router.post("/intake/{intake_id}/close", tags=["Intake"])
async def close_case(intake_id: str, data: CloseCaseRequest):
    """
    Manually close a patient case from the Doctor report page.
    """
    try:
        success = _close_case_service(
            intake_id=intake_id,
            actor_name=data.actor_name,
            reason=data.reason or "Doctor marked case as closed.",
        )
        if not success:
            raise HTTPException(status_code=400, detail="Invalid status transition to Case Closed")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET Doctor Dashboard Stats ────────────────────────────────────────────────

@router.get("/doctor/dashboard/stats", tags=["Doctor"])
async def get_doctor_dashboard_stats():
    """
    Fetch live statistics and 24-hour trends for the doctor dashboard.
    Optimized: reads status directly from DB - no per-patient lifecycle calls.
    """
    try:
        return get_dashboard_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET Doctor Clinical Worklist Patients ──────────────────────────────────────

@router.get("/doctor/review/patients", tags=["Doctor"])
async def get_doctor_review_patients():
    """
    Fetch patient worklist specifically for the Doctor review.
    Only returns cases in: awaiting_doctor_approval, investigations_approved,
    evidence_upload_pending, analysis_running.
    """
    try:
        items, elapsed_ms = get_doctor_review_list()
        logger.info("[PRATHAM] Doctor review query returned %d patients in %.0fms", len(items), elapsed_ms)
        return items
    except Exception as exc:
        logger.exception("[PRATHAM] Doctor review endpoint failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ── GET Doctor Clinical Reports List ──────────────────────────────────────────

@router.get("/doctor/reports/list", tags=["Doctor"])
async def get_doctor_reports_list():
    """
    Fetch generated clinical reports listing for doctors.
    Only returns cases in: clinical_report_ready, under_doctor_review.
    """
    try:
        return get_reports_list()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── POST Return to Nurse ──────────────────────────────────────────────────────

class ReturnToNurseRequest(BaseModel):
    intake_id: str
    actor_name: str
    reason: str

@router.post("/investigations/return-to-nurse", tags=["Doctor"])
async def return_to_nurse(data: ReturnToNurseRequest):
    """
    Return the case to the Nurse for re-upload or details correction.
    Transitions workflow status: Awaiting Doctor Approval -> Evidence Upload Pending.
    """
    try:
        success = _return_to_nurse_service(
            intake_id=data.intake_id,
            actor_name=data.actor_name,
            reason=data.reason,
        )
        if not success:
            raise HTTPException(status_code=400, detail="Invalid status transition to Evidence Upload Pending")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── POST Doctor Recommends Test ────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    intake_id: str
    investigation_type: str
    doctor_name: str

@router.post("/investigations/recommend", tags=["Doctor"])
async def recommend_investigation(data: RecommendRequest):
    """
    Doctor recommends and auto-approves a new custom investigation test.
    Updates status to Approved and logs.
    """
    try:
        return _recommend_investigation_service(
            intake_id=data.intake_id,
            investigation_type=data.investigation_type,
            doctor_name=data.doctor_name,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

