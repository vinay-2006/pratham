"""
PatientQueueService — Business logic for the nurse patient queue.

Domain: Investigations / Nurse Workflow
Responsibility: Assemble the lightweight patient queue used by the nurse
                workstation. Fetches investigations, evidence, and pipeline
                status in parallel, then builds one summary entry per active intake.

Extracted from: api/investigations.py::get_patient_queue (L613–792)

Async analysis — why asyncio.gather exists:
  The function performs three independent read-only DB/service calls:
    1. investigation_repository.get_by_intake_ids  — DB (investigations table)
    2. evidence_repository.get_by_intake_ids       — DB (evidence table)
    3. pipeline_status_service.get_batch_pipeline_status — DB (pipeline_status table)
  All three take the same `intake_ids` list as input and return independent
  result sets. There is no dependency between them: none uses the output of
  another. They are IO-bound and safe to run in parallel threads.

Async conclusion: OPTION 2 — Move gather into async service.
  Rationale:
    • The service exposes a single async function `get_queue_items()`.
    • The gather, to_thread calls, and all business logic move verbatim.
    • The API becomes: `return await get_queue_items()`.
    • Parallelism is fully preserved (same wall-clock performance).
    • No asyncio redesign — same pattern, different file.

Safety justification:
  ✓ Read-only — zero writes, zero status transitions
  ✓ No workflow ownership — CLOSED/OFFLINE exclusion is a display filter only
  ✓ Parallel fetch unchanged — asyncio.gather + to_thread moved verbatim
  ✓ Evidence completeness is a pure calculation on pre-fetched data
  ✓ All repositories already used; no new calls introduced
  ✓ Response dict shape unchanged

Business rules owned here:
  • CLOSED/OFFLINE exclusion (not shown in nurse queue)
  • Investigation count aggregation (approved/pending/rejected/needs_info)
  • Evidence completeness calculation (linked vs. proxy count)
  • Pipeline status default (all stages "pending" when no record exists)
  • WORKFLOW_PROGRESS_MAP lookup for progress percentage
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List

from app.domains.triage.repository import intake_repository
from app.domains.investigation.repository import investigation_repository
from app.domains.evidence.repository import evidence_repository
from app.domains.workflow.repository import workflow_repository
from app.models.workflow import WorkflowStatus, WORKFLOW_PROGRESS_MAP
from app.utils.patient_utils import (
    build_display_name,
    compute_age,
    derive_sex,
    derive_severity,
    extract_arrival_time,
)

logger = logging.getLogger(__name__)

_EXCLUDED_STATUSES: frozenset[str] = frozenset({
    WorkflowStatus.CLOSED.value,
    WorkflowStatus.OFFLINE.value,
})

_DEFAULT_PIPELINE_STATUS: Dict[str, str] = {
    "nlp": "pending", "risk": "pending", "lab": "pending",
    "imaging": "pending", "aggregation": "pending",
}

# Known legacy DB values → canonical WorkflowStatus values.
# Applied when workflow_logs has no entry for an intake, so the raw DB
# status must be normalized before reaching the frontend.
_STATUS_CANONICAL_MAP: Dict[str, str] = {
    "investigation_approved":  WorkflowStatus.APPROVED.value,   # investigations_approved
    "intake_pending":          WorkflowStatus.INTAKE_SUBMITTED.value,
}


def _normalize_patient_row(raw: Any) -> dict:
    """
    Normalize Supabase joined `patients` value.
    Depending on the FK relationship shape, this may be a dict, a list, or None.
    Consistent with command_center_service._normalize_patient_row.
    """
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list) and raw:
        return raw[0]
    return {}


def _count_evidence_uploaded(
    approved_inv_ids: List[str],
    ev_rows: List[Dict],
    approved_count: int,
) -> int:
    """
    Calculate the number of evidence items uploaded for approved investigations.

    Two-tier strategy (matches original logic exactly):
      Tier 1 — linked: count evidence rows whose investigation_id is in
                       approved_inv_ids (exact linkage available).
      Tier 2 — proxy:  if investigation_id is missing from evidence rows,
                       use min(len(ev_rows), approved_count) as a best-effort
                       upper-bounded estimate.
    """
    if not approved_inv_ids:
        return 0
    linked_inv_ids = {
        r.get("investigation_id")
        for r in ev_rows
        if r.get("investigation_id") in approved_inv_ids
    }
    if linked_inv_ids:
        return len(linked_inv_ids)
    if ev_rows:
        return min(len(ev_rows), approved_count)
    return 0


async def get_queue_items() -> List[Dict[str, Any]]:
    """
    Build the nurse patient queue with parallel batch fetching.

    Fetches up to 200 recent intakes, then concurrently retrieves:
      • investigation status counts
      • evidence upload state
      • pipeline stage status

    Returns a list of queue item dicts (same shape as original endpoint).
    Returns [] when no intakes exist.

    Raises Exception on any unrecovered repository failure (caller maps to HTTP 500).
    """
    result_data = intake_repository.list_recent(
        columns=(
            "id, status, created_at, severity_level, chief_complaint, "
            "case_id, arrival_type, ambulance_eta, "
            "patients(first_name, last_name, gender, date_of_birth), "
            "risk_scores(overall_severity)"
        ),
        limit=200,
    )

    if not result_data:
        return []

    intake_ids = [intake["id"] for intake in result_data]

    # ── Parallel batch fetches (three independent IO-bound reads) ─────────────
    # Repository errors propagate — a DB failure must NOT appear as
    # "0 investigations" or "0 evidence" to the clinician.
    # Single retry handles transient Supabase "Server disconnected" in to_thread.
    def _batch_investigations() -> List[Dict]:
        try:
            return investigation_repository.get_by_intake_ids(
                intake_ids, columns="id, intake_id, status"
            )
        except Exception:
            logger.warning("[Queue] Investigation fetch retry after transient error")
            return investigation_repository.get_by_intake_ids(
                intake_ids, columns="id, intake_id, status"
            )

    def _batch_evidence() -> List[Dict]:
        try:
            return evidence_repository.get_by_intake_ids(
                intake_ids, columns="intake_id, investigation_id"
            )
        except Exception:
            # Retry with minimal columns (some schemas lack investigation_id)
            return evidence_repository.get_by_intake_ids(
                intake_ids, columns="intake_id"
            )

    def _batch_pipeline() -> Dict[str, Dict]:
        from app.services.pipeline_status_service import get_batch_pipeline_status
        return get_batch_pipeline_status(intake_ids)

    def _batch_workflow_status() -> Dict[str, str]:
        try:
            return workflow_repository.get_batch_latest_status(intake_ids)
        except Exception:
            logger.warning("[Queue] Workflow status fetch retry after transient error")
            return workflow_repository.get_batch_latest_status(intake_ids)

    all_investigations, all_evidence, pipeline_by_intake, canonical_statuses = await asyncio.gather(
        asyncio.to_thread(_batch_investigations),
        asyncio.to_thread(_batch_evidence),
        asyncio.to_thread(_batch_pipeline),
        asyncio.to_thread(_batch_workflow_status),
    )

    # Index results by intake_id for O(1) per-intake lookup
    inv_by_intake: Dict[str, List[Dict]] = {}
    for inv in all_investigations:
        inv_by_intake.setdefault(inv["intake_id"], []).append(inv)

    ev_by_intake: Dict[str, List[Dict]] = {}
    for ev in all_evidence:
        ev_by_intake.setdefault(ev["intake_id"], []).append(ev)

    # ── Per-intake assembly ───────────────────────────────────────────────────
    queue_items: List[Dict[str, Any]] = []

    for intake in result_data:
        iid            = intake["id"]
        raw_db_status  = intake.get("status", "intake_submitted")

        # Resolve canonical workflow status from workflow_logs (SSOT).
        # When workflow_logs has no entry for this intake, apply
        # _STATUS_CANONICAL_MAP to normalize known legacy DB values.
        if iid in canonical_statuses:
            current_status = canonical_statuses[iid]
        else:
            current_status = _STATUS_CANONICAL_MAP.get(raw_db_status, raw_db_status)

        # Closed and offline cases are not shown in the nurse queue
        if current_status in _EXCLUDED_STATUSES:
            continue

        patient_row = _normalize_patient_row(intake.get("patients"))
        risk_rows   = intake.get("risk_scores") or []
        risk_row    = risk_rows[0] if isinstance(risk_rows, list) and risk_rows else {}

        name     = build_display_name(patient_row)
        age      = compute_age(patient_row.get("date_of_birth"))
        sex      = derive_sex(patient_row.get("gender"))
        severity = derive_severity(risk_row) if risk_row else (
            (intake.get("severity_level") or "moderate").lower()
        )
        arrival  = extract_arrival_time(intake.get("created_at", ""))

        # Investigation status counts
        inv_rows = inv_by_intake.get(iid, [])
        counts: Dict[str, int] = {
            "approved": 0, "pending_approval": 0,
            "rejected": 0, "needs_info": 0,
        }
        approved_inv_ids: List[str] = []
        for inv in inv_rows:
            s = inv.get("status", "")
            if s in counts:
                counts[s] += 1
            if s == "approved":
                approved_inv_ids.append(inv["id"])

        # Evidence completeness
        evidence_uploaded = _count_evidence_uploaded(
            approved_inv_ids,
            ev_by_intake.get(iid, []),
            counts["approved"],
        )

        pipeline_status = pipeline_by_intake.get(iid, dict(_DEFAULT_PIPELINE_STATUS))

        queue_items.append({
            "intake_id":      iid,
            "patient_name":   name,
            "age":            age,
            "sex":            sex,
            "severity":       severity,
            "arrival_time":   arrival,
            "intake_status":  raw_db_status,
            "chief_complaint": intake.get("chief_complaint", ""),
            "created_at":     intake.get("created_at", ""),
            "workflow_status": current_status,
            "case_id":        intake.get("case_id"),
            "arrival_type":   intake.get("arrival_type") or "walk_in",
            "ambulance_eta":  intake.get("ambulance_eta"),
            "progress":       WORKFLOW_PROGRESS_MAP.get(current_status, 10),
            "investigation_counts": {
                "approved":   counts["approved"],
                "pending":    counts["pending_approval"],
                "rejected":   counts["rejected"],
                "needs_info": counts["needs_info"],
                "total":      sum(counts.values()),
            },
            "evidence_completeness": {
                "uploaded": evidence_uploaded,
                "required": counts["approved"],
            },
            "pipeline_status": pipeline_status,
        })

    return queue_items
