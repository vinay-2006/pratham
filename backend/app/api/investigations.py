
"""
GET  /api/investigations/pending  — Fetch all pending-approval intakes for doctor queue
POST /api/investigations/approve  — Doctor investigation approval endpoint
POST /api/investigations/reject   — Doctor investigation rejection endpoint
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.supabase_client import supabase

router = APIRouter()


def _build_display_name(patient_row: dict | None) -> str:
    """Build patient display name from first_name/last_name, avoiding duplication."""
    row = patient_row or {}
    first = (row.get("first_name") or "").strip()
    last = (row.get("last_name") or "").strip()
    if last and last != first:
        return f"{first} {last}".strip() or "Unknown"
    return first or "Unknown"



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


# ── Helpers ──────────────────────────────────────────────────────────────────

SYMPTOM_LABEL_MAP: Dict[str, str] = {
    "chest_pain": "Chest Pain",
    "breathlessness": "Breathlessness",
    "trauma": "Trauma",
    "bleeding": "Bleeding",
    "unconsciousness": "Unconsciousness",
    "neurological_symptoms": "Neurological Symptoms",
}


def _derive_severity(risk: Dict[str, Any] | None) -> str:
    """Return a severity string from risk_scores row."""
    if not risk:
        return "moderate"
    overall = (risk.get("overall_severity") or "").lower()
    if overall in ("critical", "high", "moderate", "low"):
        return overall
    # Fallback: compute from individual scores
    top = max(
        risk.get("cardiac_risk", 0) or 0,
        risk.get("respiratory_risk", 0) or 0,
        risk.get("trauma_risk", 0) or 0,
        risk.get("neurological_risk", 0) or 0,
    )
    if top >= 70:
        return "critical"
    if top >= 50:
        return "high"
    if top >= 30:
        return "moderate"
    return "low"


def _derive_urgency(severity: str) -> str:
    return {"critical": "Critical", "high": "Urgent"}.get(severity, "Routine")


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


def _has_row(table: str, intake_id: str) -> bool:
    """Best-effort existence check for optional pipeline tables."""
    try:
        res = (
            supabase.table(table)
            .select("id")
            .eq("intake_id", intake_id)
            .limit(1)
            .execute()
        )
        return bool(res.data)
    except Exception:
        return False






# ── GET pending approvals for the doctor queue ───────────────────────────────

@router.get("/investigations/pending", tags=["Investigations"])
async def get_pending_approvals():
    """
    Returns all patients with pending_approval investigations,
    joined with patient info, vitals, symptoms, and risk scores.
    This is what the doctor approvals page fetches on load.
    """
    try:
        # Fetch intakes with status intake_pending,
        # joined with related tables
        result = supabase.table("emergency_intake")\
            .select(
                "id, chief_complaint, emergency_description, "
                "ambulance_eta, severity_level, status, created_at, "
                "patients(id, first_name, last_name, gender, date_of_birth, contact_number), "
                "vitals(heart_rate, spo2, bp_systolic, bp_diastolic, temperature, respiratory_rate), "
                "symptoms(chest_pain, breathlessness, trauma, bleeding, unconsciousness, neurological_symptoms), "
                "risk_scores(cardiac_risk, respiratory_risk, trauma_risk, neurological_risk, overall_severity)"
            )\
            .eq("status", "intake_pending")\
            .order("created_at", desc=True)\
            .execute()

        patients_data: List[Dict[str, Any]] = []
        for intake in result.data:
            # Fetch pending investigations for this intake
            inv_result = supabase.table("investigation_recommendations")\
                .select("id, investigation_type, status")\
                .eq("intake_id", intake["id"])\
                .eq("status", "pending_approval")\
                .execute()

            raw_vitals = intake.get("vitals")
            vitals_row = raw_vitals[0] if raw_vitals else None
            raw_syms = intake.get("symptoms")
            syms_row = raw_syms[0] if raw_syms else None
            raw_risk = intake.get("risk_scores")
            risk_row = raw_risk[0] if raw_risk else None
            patient_row = intake.get("patients")

            # ── Build notification-shaped response ──────────────────────
            from datetime import datetime

            name = _build_display_name(patient_row)

            gender = ((patient_row or {}).get("gender") or "").lower()
            sex = "M" if gender == "male" else "F"

            dob = (patient_row or {}).get("date_of_birth")
            age = 0
            if dob:
                if "-" in str(dob):
                    try:
                        birth_year = int(str(dob).split("-")[0])
                        age = datetime.now().year - birth_year
                    except Exception:
                        pass
                else:
                    try:
                        age = int(dob)
                    except ValueError:
                        pass

            severity = _derive_severity(risk_row)

            # Active symptoms as display labels
            symptom_labels = [
                label
                for field, label in SYMPTOM_LABEL_MAP.items()
                if (syms_row or {}).get(field)
            ]

            hr = (vitals_row or {}).get("heart_rate")
            spo2_val = (vitals_row or {}).get("spo2")
            bp_sys = (vitals_row or {}).get("bp_systolic")
            bp_dia = (vitals_row or {}).get("bp_diastolic")
            bp_str = f"{int(bp_sys)}/{int(bp_dia)}" if bp_sys and bp_dia else "—"
            vitals_summary = f"HR {hr or '—'} · SpO₂ {f'{spo2_val}%' if spo2_val else '—'} · BP {bp_str}"

            # Investigations list
            inv_types = [r["investigation_type"] for r in (inv_result.data or [])]

            # Timestamp
            created = intake.get("created_at", "")
            ts = ""
            if created and len(str(created)) >= 16:
                ts = str(created)[11:16]  # "HH:MM"

            patients_data.append({
                "id": f"ntf-{intake['id'][:8]}",
                "intake_id": intake["id"],
                "patientName": name,
                "age": age,
                "sex": sex,
                "severity": severity,
                "symptoms": symptom_labels,
                "vitalsSummary": vitals_summary,
                "recommendedInvestigations": inv_types,
                "timestamp": ts,
                "urgency": _derive_urgency(severity),
                "status": "Pending Approval",
                "emergencyDescription": intake.get("emergency_description", ""),
                "vitals": {
                    "heartRate": hr,
                    "spo2": spo2_val,
                    "bloodPressure": bp_str,
                    "respiratoryRate": (vitals_row or {}).get("respiratory_rate"),
                    "temperature": (vitals_row or {}).get("temperature"),
                },
            })

        return patients_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST approve ─────────────────────────────────────────────────────────────

def _safe_update(table: str, fields: dict, fallback_fields: dict, **eq_filters):
    """Update rows in *table* matching *eq_filters* with *fields*.

    The *fallback_fields* parameter is accepted for call-site compatibility
    but is no longer used — the audit columns (approved_at, rejected_at, etc.)
    are present in the schema, so the full *fields* payload is sent directly.
    """
    q = supabase.table(table).update(fields)
    for k, v in eq_filters.items():
        q = q.eq(k, v)
    q.execute()


def _safe_insert(table: str, fields: dict, fallback_fields: dict):
    """Insert a row into *table* with *fields*.

    The *fallback_fields* parameter is accepted for call-site compatibility
    but is no longer used.
    """
    supabase.table(table).insert(fields).execute()


@router.post("/investigations/approve", response_model=ApprovalResponse, tags=["Investigations"])
async def approve_investigations(data: ApprovalRequest) -> ApprovalResponse:
    """
    Doctor approves selected investigations for a patient intake.
    Updates investigation_recommendations statuses and writes audit trail.
    """
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        # 1. Mark all existing pending recommendations as rejected first
        _safe_update(
            "investigation_recommendations",
            {"status": "rejected", "rejected_at": now, "rejected_by": data.doctor_name, "review_notes": data.doctor_notes},
            {"status": "rejected"},
            intake_id=data.intake_id, status="pending_approval",
        )

        # 2. Mark approved system-recommended tests as approved
        for test in data.approved_tests:
            _safe_update(
                "investigation_recommendations",
                {"status": "approved", "approved_at": now, "approved_by": data.doctor_name, "review_notes": data.doctor_notes},
                {"status": "approved"},
                intake_id=data.intake_id, investigation_type=test,
            )

        # 3. Insert custom tests as new approved records
        from app.services.investigation_registry import normalize_investigation_name
        for custom_test in (data.custom_tests or []):
            if custom_test.strip():
                normalized = normalize_investigation_name(custom_test)
                _safe_insert(
                    "investigation_recommendations",
                    {"intake_id": data.intake_id, "investigation_type": normalized, "status": "approved", "approved_at": now, "approved_by": data.doctor_name, "review_notes": data.doctor_notes},
                    {"intake_id": data.intake_id, "investigation_type": normalized, "status": "approved"},
                )

        # 4. Update emergency_intake status
        supabase.table("emergency_intake").update({
            "status": "investigation_approved",
        }).eq("id", data.intake_id).execute()

        total = len(data.approved_tests) + len(data.custom_tests or [])
        return ApprovalResponse(
            intake_id=data.intake_id,
            approved_count=total,
            status="investigation_approved",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST reject ──────────────────────────────────────────────────────────────

@router.post("/investigations/reject", tags=["Investigations"])
async def reject_investigations(data: RejectRequest):
    """
    Doctor rejects all investigations for a patient intake.
    Writes audit trail (rejected_at, rejected_by, review_notes).
    """
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        _safe_update(
            "investigation_recommendations",
            {"status": "rejected", "rejected_at": now, "rejected_by": data.doctor_name, "review_notes": data.doctor_notes},
            {"status": "rejected"},
            intake_id=data.intake_id,
        )

        # Note: We do NOT update emergency_intake.status for rejections because
        # the DB check constraint only allows specific values.
        # The rejection is tracked via investigation_recommendations.status = 'rejected'.

        return {"intake_id": data.intake_id, "status": "rejected"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST needs_info ──────────────────────────────────────────────────────────

@router.post("/investigations/needs-info", tags=["Investigations"])
async def needs_info_investigations(data: NeedsInfoRequest):
    """
    Doctor requests more information for a patient intake's investigations.
    """
    try:
        _safe_update(
            "investigation_recommendations",
            {"status": "needs_info", "review_notes": data.doctor_notes},
            {"status": "needs_info"},
            intake_id=data.intake_id, status="pending_approval",
        )

        try:
            supabase.table("emergency_intake").update({
                "status": "needs_info",
            }).eq("id", data.intake_id).execute()
        except Exception:
            pass  # Non-fatal: DB check constraint may reject this status value

        return {"intake_id": data.intake_id, "status": "needs_info"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET investigation history (all statuses, 72h retention) ──────────────────

@router.get("/investigations/history", tags=["Investigations"])
async def get_investigation_history(status: Optional[str] = None):
    """
    Returns investigation records across ALL statuses with 72-hour retention.
    Optional query param ?status=approved|rejected|needs_info to filter.
    Approved, rejected, and needs_info records are retained for 72 hours.
    Pending records are always included regardless of age.
    """
    try:
        from datetime import datetime, timezone, timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()

        # Build query for non-pending statuses (with 72h window)
        valid_statuses = {"approved", "rejected", "needs_info", "pending_approval"}
        query_status = status if status in valid_statuses else None

        # Fetch intakes with joined data
        query = supabase.table("emergency_intake")\
            .select(
                "id, chief_complaint, emergency_description, "
                "ambulance_eta, severity_level, status, created_at, "
                "patients(id, first_name, last_name, gender, date_of_birth, contact_number), "
                "vitals(heart_rate, spo2, bp_systolic, bp_diastolic, temperature, respiratory_rate), "
                "symptoms(chest_pain, breathlessness, trauma, bleeding, unconsciousness, neurological_symptoms), "
                "risk_scores(cardiac_risk, respiratory_risk, trauma_risk, neurological_risk, overall_severity)"
            )

        # Filter by intake status based on requested investigation status
        # NOTE: "rejected" does NOT set emergency_intake.status (DB check constraint)
        # so we cannot filter by intake status for rejections — we post-filter instead.
        if query_status == "approved":
            query = query.eq("status", "investigation_approved")
        elif query_status == "needs_info":
            query = query.eq("status", "needs_info")
        elif query_status == "pending_approval":
            query = query.eq("status", "intake_pending")
        # For "rejected" or "all" (None): no filter — we post-filter after fetching investigations

        query = query.order("created_at", desc=True)
        result = query.execute()

        patients_data: List[Dict[str, Any]] = []
        for intake in result.data:
            # Apply 72h retention for non-pending statuses
            intake_status = intake.get("status", "")
            created = intake.get("created_at", "")
            if intake_status != "intake_pending" and created < cutoff:
                continue  # Skip records older than 72 hours

            # Fetch investigations for this intake (with graceful audit column handling)
            try:
                inv_result = supabase.table("investigation_recommendations")\
                    .select("id, investigation_type, status, approved_at, approved_by, rejected_at, rejected_by, review_notes, created_at")\
                    .eq("intake_id", intake["id"])\
                    .execute()
            except Exception:
                inv_result = supabase.table("investigation_recommendations")\
                    .select("id, investigation_type, status, created_at")\
                    .eq("intake_id", intake["id"])\
                    .execute()

            raw_vitals = intake.get("vitals")
            vitals_row = raw_vitals[0] if raw_vitals else None
            raw_syms = intake.get("symptoms")
            syms_row = raw_syms[0] if raw_syms else None
            raw_risk = intake.get("risk_scores")
            risk_row = raw_risk[0] if raw_risk else None
            patient_row = intake.get("patients")

            from datetime import datetime as dt
            name = _build_display_name(patient_row)

            gender = ((patient_row or {}).get("gender") or "").lower()
            sex = "M" if gender == "male" else "F"

            dob = (patient_row or {}).get("date_of_birth")
            age = 0
            if dob:
                if "-" in str(dob):
                    try:
                        birth_year = int(str(dob).split("-")[0])
                        age = dt.now().year - birth_year
                    except Exception:
                        pass

            severity = _derive_severity(risk_row)

            symptom_labels = [
                label for field, label in SYMPTOM_LABEL_MAP.items()
                if (syms_row or {}).get(field)
            ]

            hr = (vitals_row or {}).get("heart_rate")
            spo2_val = (vitals_row or {}).get("spo2")
            bp_sys = (vitals_row or {}).get("bp_systolic")
            bp_dia = (vitals_row or {}).get("bp_diastolic")
            bp_str = f"{int(bp_sys)}/{int(bp_dia)}" if bp_sys and bp_dia else "—"
            vitals_summary = f"HR {hr or '—'} · SpO₂ {f'{spo2_val}%' if spo2_val else '—'} · BP {bp_str}"

            inv_types = [r["investigation_type"] for r in (inv_result.data or [])]
            inv_statuses = [r.get("status", "") for r in (inv_result.data or [])]

            # Derive notification status from both intake status and investigation statuses
            # Rejected intakes don't update emergency_intake.status (DB constraint)
            # so we check investigation_recommendations statuses instead
            if intake_status == "investigation_approved":
                notification_status = "Approved"
            elif intake_status == "needs_info":
                notification_status = "Needs Info"
            elif inv_statuses and all(s == "rejected" for s in inv_statuses):
                notification_status = "Rejected"
            elif intake_status == "intake_pending":
                notification_status = "Pending Approval"
            else:
                notification_status = "Pending Approval"

            # Post-filter: ensure each intake appears in exactly one tab
            if query_status == "rejected" and notification_status != "Rejected":
                continue
            if query_status == "pending_approval" and notification_status != "Pending Approval":
                continue

            ts = ""
            if created and len(str(created)) >= 16:
                ts = str(created)[11:16]

            # Build audit info from first investigation with audit data
            audit_info = {}
            for inv in (inv_result.data or []):
                if inv.get("approved_by"):
                    audit_info = {
                        "reviewedBy": inv["approved_by"],
                        "reviewedAt": inv.get("approved_at", ""),
                        "reviewNotes": inv.get("review_notes", ""),
                    }
                    break
                if inv.get("rejected_by"):
                    audit_info = {
                        "reviewedBy": inv["rejected_by"],
                        "reviewedAt": inv.get("rejected_at", ""),
                        "reviewNotes": inv.get("review_notes", ""),
                    }
                    break

            patients_data.append({
                "id": f"ntf-{intake['id'][:8]}",
                "intake_id": intake["id"],
                "patientName": name,
                "age": age,
                "sex": sex,
                "severity": severity,
                "symptoms": symptom_labels,
                "vitalsSummary": vitals_summary,
                "recommendedInvestigations": inv_types,
                "timestamp": ts,
                "urgency": _derive_urgency(severity),
                "status": notification_status,
                "emergencyDescription": intake.get("emergency_description", ""),
                "vitals": {
                    "heartRate": hr,
                    "spo2": spo2_val,
                    "bloodPressure": bp_str,
                    "respiratoryRate": (vitals_row or {}).get("respiratory_rate"),
                    "temperature": (vitals_row or {}).get("temperature"),
                },
                "audit": audit_info,
            })

        return patients_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET patient queue — lightweight summary for nurse list ────────────────────

@router.get("/investigations/queue", tags=["Investigations"])
async def get_patient_queue():
    """
    Lightweight patient queue for the nurse workstation.
    Returns one entry per intake with: demographics, severity, arrival time,
    investigation status counts (approved/pending/rejected), and evidence completeness.
    Ordered newest-first. Uses batch queries to avoid N+1.
    """
    import asyncio

    try:
        result = (
            supabase.table("emergency_intake")
            .select(
                "id, status, created_at, severity_level, chief_complaint, "
                "patients(first_name, last_name, gender, date_of_birth), "
                "risk_scores(overall_severity)"
            )
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )

        if not result.data:
            return []

        intake_ids = [intake["id"] for intake in result.data]

        # ── Batch fetch all related data in parallel ──────────────────────
        def _batch_investigations():
            try:
                res = supabase.table("investigation_recommendations") \
                    .select("id, intake_id, status") \
                    .in_("intake_id", intake_ids).execute()
                return res.data or []
            except Exception:
                return []

        def _batch_evidence():
            try:
                res = supabase.table("evidence") \
                    .select("intake_id, investigation_id") \
                    .in_("intake_id", intake_ids).execute()
                return res.data or []
            except Exception:
                # investigation_id column may not exist yet (migration 003)
                try:
                    res = supabase.table("evidence") \
                        .select("intake_id") \
                        .in_("intake_id", intake_ids).execute()
                    return res.data or []
                except Exception:
                    return []

        def _batch_table(table_name):
            try:
                res = supabase.table(table_name) \
                    .select("intake_id") \
                    .in_("intake_id", intake_ids).execute()
                return {r["intake_id"] for r in (res.data or [])}
            except Exception:
                return set()

        def _batch_pipeline():
            from app.services.pipeline_status_service import get_batch_pipeline_status
            return get_batch_pipeline_status(intake_ids)

        (
            all_investigations,
            all_evidence,
            nlp_set,
            lab_set,
            imaging_set,
            agg_set,
            pipeline_by_intake,
        ) = await asyncio.gather(
            asyncio.to_thread(_batch_investigations),
            asyncio.to_thread(_batch_evidence),
            asyncio.to_thread(lambda: _batch_table("nlp_extractions")),
            asyncio.to_thread(lambda: _batch_table("lab_results")),
            asyncio.to_thread(lambda: _batch_table("imaging_results")),
            asyncio.to_thread(lambda: _batch_table("aggregation_results")),
            asyncio.to_thread(_batch_pipeline),
        )

        # ── Index batch results by intake_id ──────────────────────────────
        inv_by_intake: Dict[str, List[Dict]] = {}
        for inv in all_investigations:
            inv_by_intake.setdefault(inv["intake_id"], []).append(inv)

        ev_by_intake: Dict[str, List[Dict]] = {}
        for ev in all_evidence:
            ev_by_intake.setdefault(ev["intake_id"], []).append(ev)

        # ── Build queue items ─────────────────────────────────────────────
        from datetime import datetime as _dt

        queue_items: List[Dict[str, Any]] = []

        for intake in result.data:
            iid = intake["id"]
            patient_row = intake.get("patients") or {}
            risk_rows = intake.get("risk_scores") or []
            risk_row = risk_rows[0] if risk_rows else {}

            # Demographics
            name = _build_display_name(patient_row)
            gender = (patient_row.get("gender") or "").lower()
            sex = "M" if gender == "male" else "F"

            dob = patient_row.get("date_of_birth")
            age = 0
            if dob:
                if "-" in str(dob):
                    try:
                        age = _dt.now().year - int(str(dob).split("-")[0])
                    except Exception:
                        pass
                else:
                    try:
                        age = int(dob)
                    except ValueError:
                        pass

            severity = _derive_severity(risk_row) if risk_row else (
                (intake.get("severity_level") or "moderate").lower()
            )

            created = intake.get("created_at", "")
            arrival = str(created)[11:16] if created and len(str(created)) >= 16 else ""

            # Investigation counts (from batch data)
            inv_rows = inv_by_intake.get(iid, [])
            counts: Dict[str, int] = {
                "approved": 0,
                "pending_approval": 0,
                "rejected": 0,
                "needs_info": 0,
            }
            approved_inv_ids: List[str] = []
            for inv in inv_rows:
                s = inv.get("status", "")
                if s in counts:
                    counts[s] += 1
                if s == "approved":
                    approved_inv_ids.append(inv["id"])

            # Evidence completeness (from batch data)
            # Count evidence that is either linked by investigation_id OR
            # simply exists for this intake (handles missing column case)
            evidence_uploaded = 0
            if approved_inv_ids:
                ev_rows = ev_by_intake.get(iid, [])
                linked_inv_ids = {
                    r.get("investigation_id")
                    for r in ev_rows
                    if r.get("investigation_id") in approved_inv_ids
                }
                if linked_inv_ids:
                    evidence_uploaded = len(linked_inv_ids)
                elif ev_rows:
                    # No linked evidence — count raw evidence rows as uploaded
                    # (each file counts as one upload, capped at approved count)
                    evidence_uploaded = min(len(ev_rows), counts["approved"])

            # Pipeline status from the real pipeline_status table (all 4 states)
            pipeline_status = pipeline_by_intake.get(iid, {
                "nlp": "pending", "risk": "pending", "lab": "pending",
                "imaging": "pending", "aggregation": "pending",
            })

            # Workflow status (from dedicated service)
            from app.services.workflow_service import compute_workflow_status
            inv_counts_for_wf = {
                "approved": counts["approved"],
                "pending_approval": counts["pending_approval"],
                "rejected": counts["rejected"],
                "total": sum(counts.values()),
            }
            ev_for_wf = {"uploaded": evidence_uploaded, "required": counts["approved"]}
            workflow_status = compute_workflow_status(inv_counts_for_wf, ev_for_wf, pipeline_status)

            queue_items.append({
                "intake_id": iid,
                "patient_name": name,
                "age": age,
                "sex": sex,
                "severity": severity,
                "arrival_time": arrival,
                "intake_status": intake.get("status", ""),
                "chief_complaint": intake.get("chief_complaint", ""),
                "created_at": intake.get("created_at", ""),
                "workflow_status": workflow_status,
                "investigation_counts": {
                    "approved": counts["approved"],
                    "pending": counts["pending_approval"],
                    "rejected": counts["rejected"],
                    "needs_info": counts["needs_info"],
                    "total": sum(counts.values()),
                },
                "evidence_completeness": {
                    "uploaded": evidence_uploaded,
                    "required": counts["approved"],
                },
                "pipeline_status": pipeline_status,
            })

        return queue_items

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
        # Total intakes
        intake_res = (
            supabase.table("emergency_intake")
            .select("id")
            .limit(500)
            .execute()
        )
        total = len(intake_res.data or [])

        # Intakes with at least one pending_approval investigation
        pending_res = (
            supabase.table("investigation_recommendations")
            .select("intake_id")
            .eq("status", "pending_approval")
            .execute()
        )
        # Deduplicate by intake_id
        pending_intake_ids = {r["intake_id"] for r in (pending_res.data or [])}

        return {
            "total_patients": total,
            "pending_approval_patients": len(pending_intake_ids),
        }
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
    from app.api.evidence import get_evidence_type  # avoid circular at module level

    try:
        # 1. Fetch intake with all related rows
        intake_res = (
            supabase.table("emergency_intake")
            .select(
                "id, status, created_at, severity_level, "
                "emergency_description, chief_complaint, ambulance_eta, "
                "patients(id, first_name, last_name, gender, date_of_birth, contact_number), "
                "vitals(heart_rate, spo2, bp_systolic, bp_diastolic, temperature, respiratory_rate), "
                "symptoms(chest_pain, breathlessness, trauma, bleeding, unconsciousness, neurological_symptoms), "
                "risk_scores(cardiac_risk, respiratory_risk, trauma_risk, neurological_risk, overall_severity)"
            )
            .eq("id", intake_id)
            .execute()
        )

        if not intake_res.data:
            raise HTTPException(status_code=404, detail="Intake not found")

        intake = intake_res.data[0]

        # 2–3. Fetch investigations, evidence, and AI results in parallel
        import asyncio

        def _fetch_inv():
            return supabase.table("investigation_recommendations") \
                .select("id, investigation_type, status, approved_at, rejected_at, review_notes, created_at") \
                .eq("intake_id", intake_id).order("created_at").execute()

        def _fetch_ev():
            try:
                return supabase.table("evidence") \
                    .select("id, evidence_type, file_url, file_name, uploaded_at, investigation_id") \
                    .eq("intake_id", intake_id).order("uploaded_at", desc=True).execute()
            except Exception:
                return supabase.table("evidence") \
                    .select("id, evidence_type, file_url, file_name, uploaded_at") \
                    .eq("intake_id", intake_id).order("uploaded_at", desc=True).execute()

        def _fetch_lab():
            try:
                res = supabase.table("lab_results") \
                    .select("id, model_name, prediction, risk_probability, shap_values, input_features, top_features, created_at") \
                    .eq("intake_id", intake_id).order("created_at", desc=True).limit(1).execute()
                return res.data[0] if res.data else None
            except Exception:
                return None

        def _fetch_imaging():
            try:
                try:
                    res = supabase.table("imaging_results") \
                        .select("id, model_name, prediction, pneumonia_probability, confidence, created_at, evidence_id, gradcam_url") \
                        .eq("intake_id", intake_id).order("created_at", desc=True).limit(1).execute()
                except Exception:
                    res = supabase.table("imaging_results") \
                        .select("id, model_name, prediction, pneumonia_probability, confidence, created_at, evidence_id") \
                        .eq("intake_id", intake_id).order("created_at", desc=True).limit(1).execute()
                return res.data[0] if res.data else None
            except Exception:
                return None

        def _fetch_agg():
            try:
                res = supabase.table("aggregation_results").select("*") \
                    .eq("intake_id", intake_id).order("created_at", desc=True).limit(1).execute()
                return res.data[0] if res.data else None
            except Exception:
                return None

        def _fetch_nlp():
            try:
                res = supabase.table("nlp_extractions").select("*") \
                    .eq("intake_id", intake_id).limit(1).execute()
                return res.data[0] if res.data else None
            except Exception:
                return None

        inv_res, ev_res, lab_result, imaging_result, aggregation_result, nlp_result = await asyncio.gather(
            asyncio.to_thread(_fetch_inv),
            asyncio.to_thread(_fetch_ev),
            asyncio.to_thread(_fetch_lab),
            asyncio.to_thread(_fetch_imaging),
            asyncio.to_thread(_fetch_agg),
            asyncio.to_thread(_fetch_nlp),
        )

        evidence_rows = ev_res.data or []

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

        inv_list = inv_res.data or []
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
                analysis_result = {
                    "type": "lab",
                    "model_name": lab_result.get("model_name"),
                    "prediction": lab_result.get("prediction"),
                    "probability": lab_result.get("risk_probability"),
                    "top_features": lab_result.get("top_features"),
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

        # 5. Build structured response
        patient_row = intake.get("patients") or {}
        vitals_rows = intake.get("vitals") or []
        vitals_row = vitals_rows[0] if vitals_rows else {}
        syms_rows = intake.get("symptoms") or []
        syms_row = syms_rows[0] if syms_rows else {}
        risk_rows = intake.get("risk_scores") or []
        risk_row = risk_rows[0] if risk_rows else {}

        # Pipeline status from the real pipeline_status table (shows running/failed)
        from app.services.pipeline_status_service import get_pipeline_status_flat
        try:
            pipeline_status = get_pipeline_status_flat(intake_id)
        except Exception:
            # Graceful fallback if pipeline_status table is unreachable
            pipeline_status = {
                "nlp": "completed" if nlp_result else "pending",
                "risk": "completed" if risk_rows else "pending",
                "lab": "completed" if lab_result else "pending",
                "imaging": "completed" if imaging_result else "pending",
                "aggregation": "completed" if aggregation_result else "pending",
            }

        name = _build_display_name(patient_row)
        gender = (patient_row.get("gender") or "").lower()

        from datetime import datetime as _dt2
        dob = patient_row.get("date_of_birth")
        age = 0
        if dob:
            if "-" in str(dob):
                try:
                    age = _dt2.now().year - int(str(dob).split("-")[0])
                except Exception:
                    pass
            else:
                try:
                    age = int(dob)
                except ValueError:
                    pass

        bp_sys = vitals_row.get("bp_systolic")
        bp_dia = vitals_row.get("bp_diastolic")
        bp_str = f"{int(bp_sys)}/{int(bp_dia)}" if bp_sys and bp_dia else "—"

        symptom_labels = [
            label
            for field, label in SYMPTOM_LABEL_MAP.items()
            if syms_row.get(field)
        ]

        created = intake.get("created_at", "")
        arrival = str(created)[11:16] if created and len(str(created)) >= 16 else ""
        eta = intake.get("ambulance_eta")

        completeness_label = (
            f"{uploaded_count} / {approved_count} complete"
            if approved_count > 0
            else "No approved investigations"
        )

        return {
            "intake_id": intake_id,
            "intake_status": intake.get("status", ""),
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
        from datetime import datetime, timezone
        from app.services.investigation_registry import normalize_investigation_name
        
        raw_name = data.investigation_name.strip()
        if not raw_name:
            raise HTTPException(status_code=400, detail="Investigation name cannot be empty")
            
        now = datetime.now(timezone.utc).isoformat()
        canonical_name = normalize_investigation_name(raw_name)
        
        # Check if already exists for this intake
        existing = supabase.table("investigation_recommendations")\
            .select("id, status")\
            .eq("intake_id", data.intake_id)\
            .eq("investigation_type", canonical_name)\
            .execute()
            
        if existing.data:
            row = supabase.table("investigation_recommendations").update({
                "status": "approved",
                "approved_at": now,
                "approved_by": data.doctor_name,
                "review_notes": data.doctor_notes
            }).eq("intake_id", data.intake_id).eq("investigation_type", canonical_name).execute()
        else:
            row = supabase.table("investigation_recommendations").insert({
                "intake_id": data.intake_id,
                "investigation_type": canonical_name,
                "status": "approved",
                "approved_at": now,
                "approved_by": data.doctor_name,
                "review_notes": data.doctor_notes
            }).execute()
            
        # Update emergency_intake status to ensure patient is in approved status if previously pending
        supabase.table("emergency_intake").update({
            "status": "investigation_approved",
        }).eq("id", data.intake_id).execute()
        
        return {
            "success": True,
            "id": row.data[0]["id"] if row.data else None,
            "canonical_name": canonical_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

