"""
GET  /api/investigations/pending  — Fetch all pending-approval intakes for doctor queue
POST /api/investigations/approve  — Doctor investigation approval endpoint
POST /api/investigations/reject   — Doctor investigation rejection endpoint
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.supabase_client import supabase

router = APIRouter()


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

            first = (patient_row or {}).get("first_name", "")
            last = (patient_row or {}).get("last_name", "")
            name = f"{first} {last}".strip() or "Unknown"

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
    """Try update with full fields; if column missing, retry with fallback."""
    try:
        q = supabase.table(table).update(fields)
        for k, v in eq_filters.items():
            q = q.eq(k, v)
        q.execute()
    except Exception as e:
        if "column" in str(e).lower() or "PGRST204" in str(e):
            q = supabase.table(table).update(fallback_fields)
            for k, v in eq_filters.items():
                q = q.eq(k, v)
            q.execute()
        else:
            raise

def _safe_insert(table: str, fields: dict, fallback_fields: dict):
    """Try insert with full fields; if column missing, retry with fallback."""
    try:
        supabase.table(table).insert(fields).execute()
    except Exception as e:
        if "column" in str(e).lower() or "PGRST204" in str(e):
            supabase.table(table).insert(fallback_fields).execute()
        else:
            raise

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
        for custom_test in (data.custom_tests or []):
            if custom_test.strip():
                _safe_insert(
                    "investigation_recommendations",
                    {"intake_id": data.intake_id, "investigation_type": custom_test.strip(), "status": "approved", "approved_at": now, "approved_by": data.doctor_name, "review_notes": data.doctor_notes},
                    {"intake_id": data.intake_id, "investigation_type": custom_test.strip(), "status": "approved"},
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
    Writes audit trail (rejected_at, rejected_by, review_notes) if columns exist.
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
        except Exception as status_err:
            print(f"[PRATHAM] Could not update intake status to needs_info (non-fatal): {status_err}")

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
            first = (patient_row or {}).get("first_name", "")
            last = (patient_row or {}).get("last_name", "")
            name = f"{first} {last}".strip() or "Unknown"

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
