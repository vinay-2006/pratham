"""
Workflow Service — Single source of truth for patient workflow status, timeline, and transitions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from app.domains.triage.repository import intake_repository
from app.domains.shared.enums import WorkflowStatus
from app.domains.workflow.repository import workflow_repository
from app.domains.pipeline.repository import pipeline_repository
from app.domains.ai.repository import aggregation_results_repository
from app.domains.evidence.repository import evidence_repository
from app.domains.investigation.repository import investigation_repository

logger = logging.getLogger(__name__)

# Human-readable labels matching WorkflowStatus values
WORKFLOW_LABELS: Dict[WorkflowStatus, str] = {
    WorkflowStatus.INTAKE_SUBMITTED: "Intake Submitted",
    WorkflowStatus.EN_ROUTE: "En Route",
    WorkflowStatus.ARRIVED: "Arrived",
    WorkflowStatus.AWAITING_APPROVAL: "Awaiting Doctor Approval",
    WorkflowStatus.APPROVED: "Investigations Approved",
    WorkflowStatus.UPLOAD_PENDING: "Evidence Upload Pending",
    WorkflowStatus.ANALYSIS_RUNNING: "Analysis Running",
    WorkflowStatus.REPORT_READY: "Clinical Report Ready",
    WorkflowStatus.UNDER_REVIEW: "Under Doctor Review",
    WorkflowStatus.CLOSED: "Case Closed",
    WorkflowStatus.OFFLINE: "Offline Care",
}

# ── State Machine Validation Rules ──────────────────────────────────────────
# Define permitted next states from each starting state.
VALID_TRANSITIONS: Dict[WorkflowStatus, List[WorkflowStatus]] = {
    WorkflowStatus.INTAKE_SUBMITTED: [
        WorkflowStatus.EN_ROUTE,
        WorkflowStatus.ARRIVED,
        WorkflowStatus.AWAITING_APPROVAL,
        WorkflowStatus.OFFLINE,
    ],
    WorkflowStatus.EN_ROUTE: [
        WorkflowStatus.ARRIVED,
        WorkflowStatus.OFFLINE,
    ],
    WorkflowStatus.ARRIVED: [
        WorkflowStatus.AWAITING_APPROVAL,
        WorkflowStatus.OFFLINE,
    ],
    WorkflowStatus.AWAITING_APPROVAL: [
        WorkflowStatus.ARRIVED,
        WorkflowStatus.APPROVED,
        WorkflowStatus.UPLOAD_PENDING,  # P1 — enables return_to_nurse (doctor sends case back to nurse)
        WorkflowStatus.CLOSED,
        WorkflowStatus.OFFLINE,
    ],
    WorkflowStatus.APPROVED: [
        WorkflowStatus.UPLOAD_PENDING,
        WorkflowStatus.ANALYSIS_RUNNING,  # Allow direct bypass if no files needed
        WorkflowStatus.REPORT_READY,
        WorkflowStatus.OFFLINE,
    ],
    WorkflowStatus.UPLOAD_PENDING: [
        WorkflowStatus.ANALYSIS_RUNNING,
        WorkflowStatus.OFFLINE,
    ],
    WorkflowStatus.ANALYSIS_RUNNING: [
        WorkflowStatus.REPORT_READY,
        WorkflowStatus.OFFLINE,
    ],
    WorkflowStatus.REPORT_READY: [
        WorkflowStatus.UNDER_REVIEW,
        WorkflowStatus.CLOSED,
        WorkflowStatus.OFFLINE,
    ],
    WorkflowStatus.UNDER_REVIEW: [
        WorkflowStatus.CLOSED,
        WorkflowStatus.OFFLINE,
    ],
    WorkflowStatus.CLOSED: [],
    WorkflowStatus.OFFLINE: [],
}

def validate_status_transition(current_status: str, new_status: str) -> bool:
    """
    Validate if transition from current_status to new_status is permitted.
    """
    try:
        curr = WorkflowStatus(current_status)
        nxt = WorkflowStatus(new_status)
    except ValueError:
        return False

    # Standard loopbacks/self-transitions are always allowed
    if curr == nxt:
        return True

    # Check state machine transitions list
    allowed = VALID_TRANSITIONS.get(curr, [])
    return nxt in allowed

# ── Log Status Transition ───────────────────────────────────────────────────

def log_status_transition(
    intake_id: str,
    old_status: Optional[str],
    new_status: str,
    actor_type: str,
    actor_name: str,
    reason: Optional[str] = None,
) -> None:
    """
    Insert a status transition audit log into public.workflow_logs.
    Delegates to WorkflowRepository (R1.1 — sole persistence owner).
    """
    try:
        workflow_repository.log_transition(
            intake_id=intake_id,
            old_status=old_status,
            new_status=new_status,
            actor_type=actor_type,
            actor_name=actor_name,
            reason=reason,
        )
        logger.info(
            "[PRATHAM/WORKFLOW] Status log inserted: %s -> %s for intake %s",
            old_status, new_status, intake_id
        )
    except Exception as exc:
        logger.error(
            "[PRATHAM/WORKFLOW] Failed to write status transition log: %s", exc
        )

# ── Update Workflow Status ──────────────────────────────────────────────────

def to_db_status(status: str) -> str:
    """
    Map the standardized 11-status values to legacy statuses allowed by the database CHECK constraint.
    """
    mapping = {
        "intake_submitted": "intake_pending",
        "en_route": "intake_pending",
        "arrived": "intake_pending",
        "awaiting_doctor_approval": "intake_pending",
        "investigations_approved": "investigation_approved",
        "evidence_upload_pending": "evidence_upload_pending",
        "analysis_running": "evidence_upload_pending",
        "clinical_report_ready": "clinical_report_ready",
        "under_doctor_review": "clinical_report_ready",
        "case_closed": "case_closed",
        "offline_care": "case_closed",
        "needs_info": "needs_info",
    }
    return mapping.get(status, status)


def get_workflow_status(intake_id: str, default_status: str) -> str:
    """
    Query the latest true standardized status from workflow_logs.
    Delegates to WorkflowRepository (R1.1 — sole persistence owner).
    """
    try:
        status = workflow_repository.get_latest_status(intake_id)
        if status is not None:
            return status
    except Exception:
        pass
    return default_status


def resolve_intakes_status(intakes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Batch resolve the true status for a list of intakes using workflow_logs.
    Delegates to WorkflowRepository (R1.1 — sole persistence owner).
    """
    if not intakes:
        return intakes
    intake_ids = [r["id"] for r in intakes if "id" in r]
    if not intake_ids:
        return intakes
    try:
        latest_status = workflow_repository.get_batch_latest_status(intake_ids)
        for r in intakes:
            if "id" in r:
                r["status"] = latest_status.get(r["id"], r.get("status"))
    except Exception:
        pass
    return intakes


# ── Update Workflow Status ──────────────────────────────────────────────────

def update_workflow_status(
    intake_id: str,
    new_status: str,
    actor_type: str,
    actor_name: str,
    reason: Optional[str] = None,
) -> bool:
    """
    Transition a patient's state in public.emergency_intake.
    Performs state machine validation, updates the database, and creates an audit log entry.
    """
    try:
        # Fetch current status
        intake_row = intake_repository.get_by_id(intake_id, columns="status")

        if not intake_row:
            logger.error("[PRATHAM/WORKFLOW] Intake %s not found for status update", intake_id)
            return False

        old_status = get_workflow_status(intake_id, intake_row.get("status"))

        # Validate transition rules
        if old_status and not validate_status_transition(old_status, new_status):
            logger.warning(
                "[PRATHAM/WORKFLOW] Invalid status transition rejected: %s -> %s for intake %s",
                old_status, new_status, intake_id
            )
            return False

        # Apply update
        intake_repository.update_status(intake_id, to_db_status(new_status))

        # Log transition
        log_status_transition(
            intake_id=intake_id,
            old_status=old_status,
            new_status=new_status,
            actor_type=actor_type,
            actor_name=actor_name,
            reason=reason,
        )
        return True

    except Exception as exc:
        logger.error("[PRATHAM/WORKFLOW] Error updating status: %s", exc)
        return False

# ── Server-Owned ETA & Expiration Check ─────────────────────────────────────

def check_and_update_patient_lifecycle(intake: Dict[str, Any]) -> str:
    """
    Determines and updates (if expired or arrived) the status of a patient dynamically.
    Returns the corrected status.
    """
    intake_id = intake["id"]
    status = intake.get("status", "intake_submitted")
    created_at_str = intake.get("created_at")

    if not created_at_str:
        return status

    try:
        # Convert created_at format YYYY-MM-DDTHH:MM:SS... to datetime object
        # Handles various timezone formats cleanly
        created_at_val = created_at_str.replace("Z", "+00:00")
        created_at = datetime.fromisoformat(created_at_val)
    except Exception:
        return status

    now = datetime.now(timezone.utc)
    elapsed_time = now - created_at

    # 1. 48-Hour Cleanup (Offline Care)
    # Only transition Pending/Active categories to Offline Care.
    # Exclude report_ready, under_doctor_review, and case_closed.
    active_statuses = {
        WorkflowStatus.INTAKE_SUBMITTED.value,
        WorkflowStatus.EN_ROUTE.value,
        WorkflowStatus.ARRIVED.value,
        WorkflowStatus.AWAITING_APPROVAL.value,
        WorkflowStatus.APPROVED.value,
        WorkflowStatus.UPLOAD_PENDING.value,
        WorkflowStatus.ANALYSIS_RUNNING.value,
    }

    if elapsed_time > timedelta(hours=48) and status in active_statuses:
        # Transition to Offline Care
        success = update_workflow_status(
            intake_id=intake_id,
            new_status=WorkflowStatus.OFFLINE.value,
            actor_type="System",
            actor_name="Automated Cleanup Engine",
            reason="Active triage window exceeded 48 hours."
        )
        if success:
            return WorkflowStatus.OFFLINE.value

    # 2. Server-Owned Ambulance ETA Arrival Check
    eta_mins = intake.get("ambulance_eta")
    if status == WorkflowStatus.EN_ROUTE.value and eta_mins is not None:
        arrival_time = created_at + timedelta(minutes=eta_mins)
        if now >= arrival_time:
            # Auto-arrive
            success = update_workflow_status(
                intake_id=intake_id,
                new_status=WorkflowStatus.ARRIVED.value,
                actor_type="System",
                actor_name="Automated ETA Engine",
                reason="Estimated arrival time elapsed."
            )
            if success:
                # Instantly chain Arrived -> Awaiting Doctor Approval as well!
                update_workflow_status(
                    intake_id=intake_id,
                    new_status=WorkflowStatus.AWAITING_APPROVAL.value,
                    actor_type="System",
                    actor_name="Triage Pipeline",
                    reason="Patient checked in for clinical triage."
                )
                return WorkflowStatus.AWAITING_APPROVAL.value

    return status

def get_workflow_label(status: str) -> str:
    """Return the human-readable label for a workflow status."""
    try:
        val = WorkflowStatus(status)
        return WORKFLOW_LABELS.get(val, status)
    except ValueError:
        return status

# ── Patient Timeline ────────────────────────────────────────────────────────

EVENT_ICONS: Dict[str, str] = {
    "intake":      "ambulance",
    "investigate":  "clipboard-list",
    "approved":    "check-circle",
    "rejected":    "x-circle",
    "uploaded":    "upload",
    "nlp":         "brain",
    "risk":        "shield-alert",
    "lab":         "flask-conical",
    "imaging":     "file-image",
    "aggregation": "layers",
    "failed":      "alert-triangle",
    "report":      "file-text",
}

STAGE_LABELS: Dict[str, str] = {
    "nlp":         "NLP Analysis",
    "risk":        "Risk Analysis",
    "lab":         "Lab AI Analysis",
    "imaging":     "Imaging AI Analysis",
    "aggregation": "Aggregation",
}

def build_patient_timeline(intake_id: str) -> List[Dict[str, Any]]:
    """
    Reconstruct patient journey from existing database timestamps.
    """
    events: List[Dict[str, Any]] = []

    try:
        # 1. Intake creation
        intake_row = intake_repository.get_by_id(
            intake_id,
            columns="created_at, chief_complaint, arrival_type, case_id",
        )
        if intake_row:
            row = intake_row
            cc = row.get("chief_complaint", "")
            arr = (row.get("arrival_type") or "walk_in").replace("_", " ").title()
            cid = row.get("case_id", "PRA-Case")
            events.append({
                "event": "Intake Submitted",
                "timestamp": row.get("created_at"),
                "icon": EVENT_ICONS["intake"],
                "type": "intake",
                "detail": f"Registered via {arr}. Case: {cid}",
            })

        # 2. Investigation recommendations
        inv_rows = investigation_repository.get_by_intake_id_with_columns(
            intake_id,
            columns="investigation_type, status, created_at, approved_at, rejected_at",
        )

        if inv_rows:
            first_created = inv_rows[0].get("created_at")
            inv_types = [r.get("investigation_type", "") for r in inv_rows]
            events.append({
                "event": f"{len(inv_rows)} Investigation(s) Recommended",
                "timestamp": first_created,
                "icon": EVENT_ICONS["investigate"],
                "type": "investigate",
                "detail": ", ".join(inv_types) if inv_types else None,
            })

        approved_list = [r for r in inv_rows if r.get("approved_at")]
        rejected_list = [r for r in inv_rows if r.get("rejected_at")]

        if approved_list:
            earliest_approval = min(r["approved_at"] for r in approved_list if r.get("approved_at"))
            events.append({
                "event": f"Doctor Approved {len(approved_list)} Investigation(s)",
                "timestamp": earliest_approval,
                "icon": EVENT_ICONS["approved"],
                "type": "approved",
                "detail": None,
            })

        if rejected_list:
            earliest_rejection = min(r["rejected_at"] for r in rejected_list if r.get("rejected_at"))
            events.append({
                "event": f"Doctor Rejected {len(rejected_list)} Investigation(s)",
                "timestamp": earliest_rejection,
                "icon": EVENT_ICONS["rejected"],
                "type": "rejected",
                "detail": None,
            })

        # 3. Evidence uploads
        try:
            ev_rows = evidence_repository.get_by_intake_id_with_columns(
                intake_id,
                columns="evidence_type, file_name, uploaded_at",
                order_by="uploaded_at",
                desc=False,
            )
            for ev in ev_rows:
                ev_type = (ev.get("evidence_type") or "file").replace("_", " ").title()
                fname = ev.get("file_name", "")
                events.append({
                    "event": f"{ev_type} Uploaded",
                    "timestamp": ev.get("uploaded_at"),
                    "icon": EVENT_ICONS["uploaded"],
                    "type": "uploaded",
                    "detail": fname if fname else None,
                })
        except Exception:
            pass

        # 4. Pipeline status events
        try:
            ps_rows = pipeline_repository.get_by_intake_id(intake_id)
            for ps in ps_rows:
                stage = ps.get("stage", "")
                label = STAGE_LABELS.get(stage, stage.title())
                status = ps.get("status", "")
                duration = ps.get("duration_ms")
                duration_str = f" ({duration / 1000:.1f}s)" if duration else ""

                if status == "completed" and ps.get("completed_at"):
                    events.append({
                        "event": f"{label} Completed{duration_str}",
                        "timestamp": ps["completed_at"],
                        "icon": EVENT_ICONS.get(stage, "check-circle"),
                        "type": "pipeline_completed",
                        "detail": None,
                    })
                elif status == "failed" and ps.get("completed_at"):
                    error = ps.get("error_message", "")
                    events.append({
                        "event": f"{label} Failed",
                        "timestamp": ps["completed_at"],
                        "icon": EVENT_ICONS["failed"],
                        "type": "pipeline_failed",
                        "detail": error[:100] if error else None,
                    })
        except Exception:
            pass

        # 5. Aggregation result (report generated)
        try:
            agg_row = aggregation_results_repository.get_latest(intake_id, columns="created_at")
            if agg_row:
                events.append({
                    "event": "Clinical Report Generated",
                    "timestamp": agg_row.get("created_at"),
                    "icon": EVENT_ICONS["report"],
                    "type": "report",
                    "detail": None,
                })
        except Exception:
            pass

    except Exception as exc:
        logger.error("[PRATHAM/WORKFLOW] build_patient_timeline failed for %s: %s", intake_id, exc)

    # Sort by timestamp (oldest first)
    events.sort(key=lambda e: e.get("timestamp") or "")
    return events


def update_status_on_evidence_upload(intake_id: str, actor_name: str = "Nurse") -> None:
    """
    Checks the count of approved investigations vs uploaded evidence
    and transitions the patient's workflow status automatically.
    """
    try:
        # Fetch approved investigations
        approved_count = investigation_repository.count_by_intake_and_status(intake_id, "approved")

        # Fetch evidence files
        uploaded_count = evidence_repository.count_by_intake_id(intake_id)

        # Fetch current status
        intake_row = intake_repository.get_by_id(intake_id, columns="status")

        if intake_row:
            curr_status = intake_row.get("status")
            
            # Determine target status
            if approved_count > 0 and uploaded_count >= approved_count:
                target_status = WorkflowStatus.ANALYSIS_RUNNING.value
            else:
                target_status = WorkflowStatus.UPLOAD_PENDING.value

            if curr_status != target_status:
                update_workflow_status(
                    intake_id=intake_id,
                    new_status=target_status,
                    actor_type="Nurse",
                    actor_name=actor_name,
                    reason="Evidence uploaded"
                )
    except Exception as exc:
        logger.error("[PRATHAM/WORKFLOW] update_status_on_evidence_upload failed: %s", exc)

