"""
Workflow Service — Single source of truth for patient workflow status and timeline.

Every consumer (queue, patient detail, dashboard, future mobile) calls these
functions instead of computing workflow logic inline.

Workflow States:
    doctor_review_required  →  evidence_collection  →  ai_processing  →  report_ready
                            →  no_approved (edge case: all rejected)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.db.supabase_client import supabase

logger = logging.getLogger(__name__)


# ── Workflow Status ──────────────────────────────────────────────────────────

WORKFLOW_LABELS: Dict[str, str] = {
    "doctor_review_required": "Doctor Review Required",
    "evidence_collection":    "Awaiting Evidence Upload",
    "ai_processing":          "AI Analysis Running",
    "report_ready":           "Clinical Report Ready",
    "no_approved":            "No Approved Investigations",
}


def compute_workflow_status(
    inv_counts: Dict[str, int],
    evidence: Dict[str, int],
    pipeline_status: Dict[str, str],
) -> str:
    """
    Compute human-readable workflow status from investigation counts,
    evidence completeness, and pipeline stage statuses.

    Parameters:
        inv_counts: {"approved": N, "pending_approval": N, "rejected": N, "total": N, ...}
        evidence:   {"uploaded": N, "required": N}
        pipeline_status: {"nlp": "completed", "risk": "completed", "lab": "pending", ...}

    Returns one of:
        "doctor_review_required"
        "evidence_collection"
        "ai_processing"
        "report_ready"
        "no_approved"
    """
    total = inv_counts.get("total", 0)
    approved = inv_counts.get("approved", 0)
    pending = inv_counts.get("pending_approval", 0)

    # No investigations yet, or some still pending doctor decision
    if approved == 0:
        if total == 0 or pending > 0:
            return "doctor_review_required"
        # All rejected / needs_info, none approved
        return "no_approved"

    # Approved investigations exist — check evidence
    uploaded = evidence.get("uploaded", 0)
    required = evidence.get("required", 0)
    if required > 0 and uploaded < required:
        return "evidence_collection"

    # Evidence complete — check pipeline
    agg_status = pipeline_status.get("aggregation", "pending")
    if agg_status == "completed":
        return "report_ready"

    # Pipeline still in progress
    return "ai_processing"


def get_workflow_label(status: str) -> str:
    """Return the human-readable label for a workflow status."""
    return WORKFLOW_LABELS.get(status, status)


# ── Patient Timeline ────────────────────────────────────────────────────────

# Icon names match lucide-react icon components
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

    Reads from:
      - emergency_intake.created_at
      - investigation_recommendations.created_at, approved_at, rejected_at
      - evidence.uploaded_at, evidence_type, file_name
      - pipeline_status.started_at, completed_at, status, duration_ms
      - aggregation_results.created_at

    Returns a sorted list of timeline events (newest last):
    [
        {
            "event": "Patient Arrived",
            "timestamp": "2026-07-04T09:31:00Z",
            "icon": "ambulance",
            "type": "intake",
            "detail": null
        },
        ...
    ]
    """
    events: List[Dict[str, Any]] = []

    try:
        # 1. Intake creation
        intake_res = (
            supabase.table("emergency_intake")
            .select("created_at, chief_complaint")
            .eq("id", intake_id)
            .limit(1)
            .execute()
        )
        if intake_res.data:
            row = intake_res.data[0]
            cc = row.get("chief_complaint", "")
            detail = f"Chief complaint: {cc}" if cc else None
            events.append({
                "event": "Patient Arrived",
                "timestamp": row.get("created_at"),
                "icon": EVENT_ICONS["intake"],
                "type": "intake",
                "detail": detail,
            })

        # 2. Investigation recommendations
        inv_res = (
            supabase.table("investigation_recommendations")
            .select("investigation_type, status, created_at, approved_at, rejected_at")
            .eq("intake_id", intake_id)
            .order("created_at")
            .execute()
        )
        inv_rows = inv_res.data or []

        # Group creation by timestamp (they're usually created together)
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

        # Approval / rejection events
        approved_list = [r for r in inv_rows if r.get("approved_at")]
        rejected_list = [r for r in inv_rows if r.get("rejected_at")]

        if approved_list:
            # Use earliest approval time
            earliest_approval = min(
                r["approved_at"] for r in approved_list if r.get("approved_at")
            )
            events.append({
                "event": f"Doctor Approved {len(approved_list)} Investigation(s)",
                "timestamp": earliest_approval,
                "icon": EVENT_ICONS["approved"],
                "type": "approved",
                "detail": None,
            })

        if rejected_list:
            earliest_rejection = min(
                r["rejected_at"] for r in rejected_list if r.get("rejected_at")
            )
            events.append({
                "event": f"Doctor Rejected {len(rejected_list)} Investigation(s)",
                "timestamp": earliest_rejection,
                "icon": EVENT_ICONS["rejected"],
                "type": "rejected",
                "detail": None,
            })

        # 3. Evidence uploads
        try:
            ev_res = (
                supabase.table("evidence")
                .select("evidence_type, file_name, uploaded_at")
                .eq("intake_id", intake_id)
                .order("uploaded_at")
                .execute()
            )
            for ev in (ev_res.data or []):
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
            pass  # evidence table may have schema variations

        # 4. Pipeline status events
        try:
            ps_res = (
                supabase.table("pipeline_status")
                .select("stage, status, started_at, completed_at, duration_ms, error_message")
                .eq("intake_id", intake_id)
                .execute()
            )
            for ps in (ps_res.data or []):
                stage = ps.get("stage", "")
                label = STAGE_LABELS.get(stage, stage.title())
                status = ps.get("status", "")
                duration = ps.get("duration_ms")
                duration_str = ""
                if duration is not None:
                    if duration < 1000:
                        duration_str = f" ({duration}ms)"
                    else:
                        duration_str = f" ({duration / 1000:.1f}s)"

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
            pass  # pipeline_status table may not exist

        # 5. Aggregation result (report generated)
        try:
            agg_res = (
                supabase.table("aggregation_results")
                .select("created_at")
                .eq("intake_id", intake_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if agg_res.data:
                events.append({
                    "event": "Clinical Report Generated",
                    "timestamp": agg_res.data[0].get("created_at"),
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
