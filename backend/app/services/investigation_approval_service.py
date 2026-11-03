"""
InvestigationApprovalService — Orchestration for doctor investigation decisions.

Domain: Investigations / Doctor Approval
Responsibility: Orchestrate the doctor's approval, rejection, needs-info,
                manual add, and recommend mutations on investigation_recommendations.

Extracted from: api/investigations.py (approve, reject, needs_info, add, recommend)

Ownership map per mutation:
─────────────────────────────────────────────────────────────────────────────
  HTTP concern      → remains in API layer (routing, response model)
  Orchestration     → this service
  Business rules    → this service (upsert-or-create, guard conditions)
  Persistence       → delegated to repositories
  Audit logging     → delegated to workflow_service.update_workflow_status
                      (which calls log_status_transition → workflow_repository)
─────────────────────────────────────────────────────────────────────────────

Transaction boundaries (unchanged from original):
  • approve  : three sequential repository calls + one workflow_status call
               No DB-level transaction wrapping in the original — preserved.
  • reject   : one repository call. No workflow transition. Preserved.
  • needs_info: one repository call + one non-fatal intake status call. Preserved.
  • add      : upsert + conditional workflow transition. Preserved.
  • recommend: create + conditional workflow transition. Preserved.

Rollback behaviour:
  • None of the original mutations have explicit rollback. On exception the
    caller catches and returns HTTP 500. Preserved identically.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.domains.triage.repository import intake_repository
from app.domains.investigation.repository import investigation_repository
from app.domains.evidence.repository import evidence_repository
from app.models.workflow import WorkflowStatus
from app.services.workflow_service import (
    update_workflow_status,
    log_status_transition,   # P3 — needed for needs_info audit trail
    get_workflow_status,     # P3 — resolve old_status for audit entry
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers (verbatim from investigations.py _safe_update/_safe_insert)
# ---------------------------------------------------------------------------

def _safe_update(
    intake_id: str,
    investigation_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    fields: Dict[str, Any] = None,
) -> None:
    """
    Update investigation_recommendations rows matching the given filters.

    Replaces _safe_update("investigation_recommendations", fields, ..., **eq_filters)
    from api/investigations.py. The table argument is removed — this service only
    ever updates investigation_recommendations.
    """
    fields = fields or {}
    if investigation_type and intake_id:
        investigation_repository.update_by_intake_and_type(intake_id, investigation_type, fields)
    elif intake_id and status_filter:
        investigation_repository.update_batch_by_intake(intake_id, fields, status_filter=status_filter)
    else:
        investigation_repository.update_batch_by_intake(intake_id or "", fields)


def _safe_insert(intake_id: str, fields: Dict[str, Any]) -> None:
    """
    Insert a new investigation_recommendations row.

    Replaces _safe_insert("investigation_recommendations", fields, ...) from
    api/investigations.py.
    """
    investigation_repository.create(fields)


# ---------------------------------------------------------------------------
# approve
# ---------------------------------------------------------------------------

def approve(
    intake_id: str,
    approved_tests: List[str],
    custom_tests: List[str],
    doctor_name: str,
    doctor_notes: Optional[str],
) -> Dict[str, Any]:
    """
    Doctor approves selected investigations.

    Orchestration (matches original exactly):
      1. Bulk-reject all pending_approval recommendations
      2. Mark each approved_test as approved
      3. Insert each custom_test as a new approved recommendation
      4. Transition intake workflow: any → investigations_approved

    Transaction strategy (P4 — Phase 3.1):
      PostgREST/supabase-py does not support multi-statement transactions.
      A compensating rollback pattern is used instead:
        - If steps 2 or 3 fail after step 1 has run, all rejected
          investigations are restored to pending_approval before raising.
        - Step 4 failure is logged but does NOT undo investigation updates
          (workflow_logs inconsistency is less harmful than lost approvals).

    Returns: {"intake_id", "approved_count", "status"}

    Raises Exception on any step failure (caller maps to HTTP 500).
    """
    from app.services.investigation_registry import normalize_investigation_name

    now = datetime.now(timezone.utc).isoformat()

    # Step 1: bulk-reject remaining pending
    _safe_update(
        intake_id=intake_id,
        status_filter="pending_approval",
        fields={"status": "rejected", "rejected_at": now,
                "rejected_by": doctor_name, "review_notes": doctor_notes},
    )

    # Steps 2 + 3: approve selected and insert custom tests.
    # Compensating rollback: if anything here fails, restore investigations
    # to pending_approval so the doctor can retry without data corruption.
    try:
        # Step 2: approve each explicitly selected test
        for test in approved_tests:
            _safe_update(
                intake_id=intake_id,
                investigation_type=test,
                fields={"status": "approved", "approved_at": now,
                        "approved_by": doctor_name, "review_notes": doctor_notes},
            )

        # Step 3: insert custom tests as new approved records
        for custom_test in (custom_tests or []):
            if custom_test.strip():
                normalized = normalize_investigation_name(custom_test)
                _safe_insert(
                    intake_id=intake_id,
                    fields={
                        "intake_id": intake_id,
                        "investigation_type": normalized,
                        "status": "approved",
                        "approved_at": now,
                        "approved_by": doctor_name,
                        "review_notes": doctor_notes,
                    },
                )

    except Exception as step_exc:
        # Compensating rollback: restore all rejected investigations to
        # pending_approval so the doctor queue is consistent (P4).
        logger.error(
            "[PRATHAM/APPROVE] Step 2/3 failed for intake %s: %s. "
            "Compensating: restoring pending_approval.",
            intake_id, step_exc,
        )
        try:
            _safe_update(
                intake_id=intake_id,
                status_filter="rejected",
                fields={"status": "pending_approval",
                        "rejected_at": None, "rejected_by": None},
            )
        except Exception as rollback_exc:
            logger.error(
                "[PRATHAM/APPROVE] Compensating rollback also failed for intake %s: %s. "
                "Manual intervention required.",
                intake_id, rollback_exc,
            )
        raise  # Re-raise original exception so caller returns HTTP 500

    # Step 4: workflow transition → investigations_approved.
    # Handled separately: a workflow log failure does not warrant
    # undoing already-committed investigation approvals.
    wf_ok = update_workflow_status(
        intake_id=intake_id,
        new_status=WorkflowStatus.APPROVED.value,
        actor_type="Doctor",
        actor_name=doctor_name,
        reason=f"Approved: {', '.join(approved_tests) or 'none'}. Notes: {doctor_notes or 'none'}",
    )
    if not wf_ok:
        logger.warning(
            "[PRATHAM/APPROVE] Workflow status update failed for intake %s "
            "(investigations already approved — workflow log may be inconsistent).",
            intake_id,
        )

    total = len(approved_tests) + len(custom_tests or [])
    return {
        "intake_id":      intake_id,
        "approved_count": total,
        "status":         WorkflowStatus.APPROVED.value,
    }


# ---------------------------------------------------------------------------
# reject
# ---------------------------------------------------------------------------

def reject(
    intake_id: str,
    doctor_notes: Optional[str],
    doctor_name: Optional[str] = "Doctor",
) -> Dict[str, Any]:
    """
    Doctor rejects all pending_approval recommendations for an intake.

    Orchestration:
      1. Bulk-update pending_approval → rejected  (investigation_recommendations)
      2. Transition intake workflow: AWAITING_APPROVAL → ARRIVED  (P2 — Phase 3.1)

    Post-rejection state: ARRIVED
      • Patient is removed from the doctor's "Pending Approvals" dashboard count
        (only AWAITING_APPROVAL is counted there; ARRIVED is not).
      • Patient is removed from the doctor's active worklist (ARRIVED is not in
        REVIEW_STATUSES).
      • Patient remains visible to the nurse (ARRIVED is not in _EXCLUDED_STATUSES).
      • Patient timeline already records the rejection event from rejected_at timestamps
        on investigation rows — no additional timeline entry needed.
      • Investigation history service derives notification_status="Rejected" from
        inv_statuses — correct without any intake.status change.

    Step 2 is non-fatal: investigation-row rejection is already committed when
    step 2 runs. If the workflow update fails, it is logged and the function
    continues to return normally — investigation data is never rolled back.

    Returns: {"intake_id", "status"}

    Raises Exception on step 1 failure (caller maps to HTTP 500).
    """
    # Step 1: bulk-reject all pending investigations
    _safe_update(
        intake_id=intake_id,
        status_filter="pending_approval",
        fields={"status": "rejected", "review_notes": doctor_notes},
    )

    # Step 2: workflow transition — AWAITING_APPROVAL → ARRIVED (P2)
    # Non-fatal: investigation rows are already committed.
    wf_ok = update_workflow_status(
        intake_id=intake_id,
        new_status=WorkflowStatus.ARRIVED.value,
        actor_type="Doctor",
        actor_name=doctor_name or "Doctor",
        reason=(
            f"Investigations rejected. "
            f"Notes: {doctor_notes or 'none'}. "
            "Case returned for nurse re-assessment."
        ),
    )
    if not wf_ok:
        logger.warning(
            "[PRATHAM/REJECT] Workflow transition AWAITING_APPROVAL → ARRIVED failed "
            "for intake %s. Investigation rows rejected; workflow log may be inconsistent.",
            intake_id,
        )

    return {"intake_id": intake_id, "status": "rejected"}


# ---------------------------------------------------------------------------
# needs_info
# ---------------------------------------------------------------------------

def needs_info(
    intake_id: str,
    doctor_notes: Optional[str],
) -> Dict[str, Any]:
    """
    Doctor requests more information.

    Orchestration (matches original exactly):
      1. Bulk-update pending_approval → needs_info
      2. Non-fatal attempt to update intake status to "needs_info"
         (guarded with bare except — original comment: DB check constraint may reject)

    Returns: {"intake_id", "status"}

    Raises Exception on repository failure of step 1 (step 2 failure is swallowed).
    """
    _safe_update(
        intake_id=intake_id,
        status_filter="pending_approval",
        fields={"status": "needs_info", "review_notes": doctor_notes},
    )

    # Non-fatal: intake table has a CHECK constraint that may not allow "needs_info".
    # The direct update is preserved for identical external behaviour (P3).
    # An audit log entry is now emitted so the workflow_logs table stays complete.
    try:
        # Resolve current canonical status before overwriting (for accurate audit record)
        intake_row = intake_repository.get_by_id(intake_id, columns="status")
        old_status = get_workflow_status(intake_id, (intake_row or {}).get("status"))

        intake_repository.update_status(intake_id, "needs_info")

        # Emit audit log entry via workflow service (P3 — restores audit trail)
        log_status_transition(
            intake_id=intake_id,
            old_status=old_status,
            new_status="needs_info",
            actor_type="Doctor",
            actor_name="Doctor",
            reason=doctor_notes or "Doctor requested more information.",
        )
    except Exception:
        pass  # Non-fatal: matches original posture; logged by log_status_transition internally

    return {"intake_id": intake_id, "status": "needs_info"}


# ---------------------------------------------------------------------------
# add_investigation
# ---------------------------------------------------------------------------

def add_investigation(
    intake_id: str,
    investigation_name: str,
    doctor_name: str,
    doctor_notes: str,
) -> Dict[str, Any]:
    """
    Doctor manually adds and approves an investigation.

    Orchestration (matches original exactly):
      1. Validate name is non-empty (caller may also validate; this guards at service level)
      2. Normalize investigation name via investigation_registry
      3. Upsert: update if already exists, else create
      4. Conditionally transition: if currently in early states → investigations_approved

    Guard condition (proven from code):
      Only transitions if current canonical status is one of:
        INTAKE_SUBMITTED, EN_ROUTE, ARRIVED, AWAITING_APPROVAL

    Returns: {"success": True, "id": row_id, "canonical_name": canonical_name}

    Raises ValueError for empty name (caller maps to HTTP 400).
    Raises Exception on other failures (caller maps to HTTP 500).
    """
    from app.services.investigation_registry import normalize_investigation_name
    from app.services.workflow_service import get_workflow_status

    raw_name = investigation_name.strip()
    if not raw_name:
        raise ValueError("Investigation name cannot be empty")

    now = datetime.now(timezone.utc).isoformat()
    canonical_name = normalize_investigation_name(raw_name)

    # Upsert: update existing or create new
    existing = investigation_repository.get_by_intake_and_type(
        intake_id, canonical_name, columns="id, status"
    )
    if existing:
        investigation_repository.update_by_intake_and_type(
            intake_id, canonical_name, {
                "status": "approved",
                "approved_at": now,
                "approved_by": doctor_name,
                "review_notes": doctor_notes,
            }
        )
        row_id = existing[0].get("id")
    else:
        created = investigation_repository.create({
            "intake_id": intake_id,
            "investigation_type": canonical_name,
            "status": "approved",
            "approved_at": now,
            "approved_by": doctor_name,
            "review_notes": doctor_notes,
        })
        row_id = created.get("id") if created else None

    # Conditional workflow transition (guard: only from early states)
    _EARLY_STATES = frozenset({
        WorkflowStatus.INTAKE_SUBMITTED.value,
        WorkflowStatus.EN_ROUTE.value,
        WorkflowStatus.ARRIVED.value,
        WorkflowStatus.AWAITING_APPROVAL.value,
    })
    current_intake = intake_repository.get_by_id(intake_id, columns="status")
    if current_intake:
        current_raw = current_intake.get("status")
        current_canonical = get_workflow_status(intake_id, current_raw)
        if current_canonical in _EARLY_STATES:
            update_workflow_status(
                intake_id=intake_id,
                new_status=WorkflowStatus.APPROVED.value,
                actor_type="Doctor",
                actor_name=doctor_name or "Doctor",
                reason=f"Manually approved investigation: {canonical_name}",
            )

    return {"success": True, "id": row_id, "canonical_name": canonical_name}


# ---------------------------------------------------------------------------
# recommend_investigation
# ---------------------------------------------------------------------------

def recommend_investigation(
    intake_id: str,
    investigation_type: str,
    doctor_name: str,
) -> Dict[str, Any]:
    """
    Doctor recommends and auto-approves a new custom investigation.

    Orchestration (matches original exactly):
      1. Normalize investigation type name
      2. Create new investigation_recommendations row as approved
      3. Conditionally transition: if currently in early states → investigations_approved

    Guard condition (proven from code):
      Only transitions if current raw status is one of:
        AWAITING_APPROVAL, INTAKE_SUBMITTED, ARRIVED
      (Note: does NOT include EN_ROUTE — this matches the original exactly)

    Returns: {"status": "success", "id": row_id}

    Raises Exception on failure (caller maps to HTTP 500).
    """
    from app.services.investigation_registry import normalize_investigation_name

    now = datetime.now(timezone.utc).isoformat()
    canonical_name = normalize_investigation_name(investigation_type)

    created = investigation_repository.create({
        "intake_id": intake_id,
        "investigation_type": canonical_name,
        "status": "approved",
        "approved_at": now,
        "approved_by": doctor_name,
        "review_notes": "Requested by Doctor during clinical review.",
    })

    # Conditional workflow transition
    # NOTE: guard uses raw status (not canonical) — matches original behaviour exactly
    _RECOMMEND_GUARD_STATES = frozenset({
        WorkflowStatus.AWAITING_APPROVAL.value,
        WorkflowStatus.INTAKE_SUBMITTED.value,
        WorkflowStatus.ARRIVED.value,
    })
    res_int = intake_repository.get_by_id(intake_id, columns="status")
    if res_int:
        curr = res_int.get("status")
        if curr in _RECOMMEND_GUARD_STATES:
            update_workflow_status(
                intake_id=intake_id,
                new_status=WorkflowStatus.APPROVED.value,
                actor_type="Doctor",
                actor_name=doctor_name,
                reason=f"Requested additional test: {canonical_name}",
            )

    return {"status": "success", "id": created.get("id") if created else None}


# ---------------------------------------------------------------------------
# Post-approval investigation update — safe modification of approved decisions
# ---------------------------------------------------------------------------

# Pipeline stages whose non-pending status indicates downstream processing
# has started. NLP and Risk run at intake time and are always completed —
# they are NOT indicators of post-approval processing.
_DOWNSTREAM_STAGES = ("lab", "imaging", "aggregation")
_SAFE_PIPELINE_STATUSES = frozenset({"pending", "failed"})


def _resolve_eligibility(intake_id: str) -> Dict[str, Any]:
    """
    Shared eligibility logic used by both the GET (informational) and
    POST (guard) paths.  Returns a dict with:
        eligible: bool
        reason: str (human-readable explanation if ineligible)
        current_status: str | None
        current_investigations: list[dict] (only when eligible)
    """
    from app.services.pipeline_status_service import get_pipeline_status_flat

    # 1. Resolve canonical workflow status
    intake_row = intake_repository.get_by_id(intake_id, columns="status")
    if not intake_row:
        return {"eligible": False, "reason": "Intake not found", "current_status": None, "current_investigations": []}

    current_status = get_workflow_status(intake_id, intake_row.get("status"))
    if current_status != WorkflowStatus.APPROVED.value:
        return {
            "eligible": False,
            "reason": f"Case is in '{current_status}' state — investigations can only be updated in the 'investigations_approved' state",
            "current_status": current_status,
            "current_investigations": [],
        }

    # 2. Check evidence count
    evidence_count = evidence_repository.count_by_intake_id(intake_id)
    if evidence_count > 0:
        return {
            "eligible": False,
            "reason": f"Evidence has been uploaded ({evidence_count} file(s)) — investigations cannot be modified after evidence submission",
            "current_status": current_status,
            "current_investigations": [],
        }

    # 3. Check downstream pipeline stages
    pipeline_flat = get_pipeline_status_flat(intake_id)
    unsafe_stages = [
        s for s in _DOWNSTREAM_STAGES
        if pipeline_flat.get(s) not in _SAFE_PIPELINE_STATUSES
    ]
    if unsafe_stages:
        return {
            "eligible": False,
            "reason": f"AI analysis has started for: {', '.join(unsafe_stages)} — investigations cannot be modified",
            "current_status": current_status,
            "current_investigations": [],
        }

    # All checks passed — fetch current investigation list
    investigations = investigation_repository.get_by_intake_id_with_columns(
        intake_id,
        columns="id, investigation_type, status, approved_at, approved_by, rejected_at, rejected_by, review_notes, created_at",
    )

    return {
        "eligible": True,
        "reason": "Eligible for update",
        "current_status": current_status,
        "current_investigations": investigations,
    }


def check_update_eligibility(intake_id: str) -> Dict[str, Any]:
    """
    Check whether an approved patient's investigations can be updated.

    Called by: GET /api/investigations/{intake_id}/update-eligibility

    Returns:
        {
            "eligible": bool,
            "reason": str,
            "current_status": str | None,
            "current_investigations": [
                {"id": ..., "investigation_type": ..., "status": "approved"|"rejected"|...},
                ...
            ]
        }
    """
    return _resolve_eligibility(intake_id)


def update_investigations(
    intake_id: str,
    approved_tests: List[str],
    custom_tests: List[str],
    doctor_name: str,
    doctor_notes: Optional[str],
) -> Dict[str, Any]:
    """
    Update investigation decisions for an already-approved case.

    This is NOT a re-call of approve(). It performs its own mutation
    sequence designed to be safe for already-approved investigation sets.

    Pre-checks:
        1. Canonical workflow status must be investigations_approved
        2. Evidence count must be 0
        3. Downstream pipeline stages (lab, imaging, aggregation) must be pending/failed

    Mutation sequence:
        Step 0: Snapshot current investigation state (for audit)
        Step 1: Bulk-reject ALL existing investigations for this intake
        Step 2: Selective-approve each test in approved_tests
        Step 3: Upsert each custom test (update existing or create new)
        Step 4: Audit log with old→new diff
        Step 5: Self-transition APPROVED→APPROVED

    Compensating rollback:
        If Steps 2 or 3 fail after Step 1, restore snapshot states.

    Returns: {"intake_id", "approved_count", "status"}
    Raises: ValueError for eligibility failures (caller maps to HTTP 409)
            Exception for mutation failures (caller maps to HTTP 500)
    """
    from app.services.investigation_registry import normalize_investigation_name

    # ── Pre-checks (independent re-verification, never trusts GET) ──────
    eligibility = _resolve_eligibility(intake_id)
    if not eligibility["eligible"]:
        raise ValueError(eligibility["reason"])

    now = datetime.now(timezone.utc).isoformat()

    # ── Step 0: Snapshot ────────────────────────────────────────────────
    current_investigations = eligibility["current_investigations"]
    old_approved = [
        inv["investigation_type"] for inv in current_investigations
        if inv.get("status") == "approved"
    ]
    old_rejected = [
        inv["investigation_type"] for inv in current_investigations
        if inv.get("status") == "rejected"
    ]
    old_other = [
        inv["investigation_type"] for inv in current_investigations
        if inv.get("status") not in ("approved", "rejected")
    ]

    # Build snapshot for compensating rollback: {investigation_type: {status, ...}}
    snapshot: Dict[str, Dict[str, Any]] = {}
    for inv in current_investigations:
        snapshot[inv["investigation_type"]] = {
            "status": inv.get("status"),
            "approved_at": inv.get("approved_at"),
            "approved_by": inv.get("approved_by"),
            "rejected_at": inv.get("rejected_at"),
            "rejected_by": inv.get("rejected_by"),
            "review_notes": inv.get("review_notes"),
        }

    # ── Step 1: Bulk-reject ALL existing investigations ─────────────────
    # No status_filter — reset the entire set regardless of current status.
    investigation_repository.update_batch_by_intake(
        intake_id,
        updates={
            "status": "rejected",
            "rejected_at": now,
            "rejected_by": doctor_name,
            "review_notes": doctor_notes,
        },
        status_filter=None,
    )

    # ── Steps 2 + 3: Selective approve + upsert custom ──────────────────
    try:
        # Step 2: approve each explicitly selected test
        for test in approved_tests:
            _safe_update(
                intake_id=intake_id,
                investigation_type=test,
                fields={
                    "status": "approved",
                    "approved_at": now,
                    "approved_by": doctor_name,
                    "review_notes": doctor_notes,
                },
            )

        # Step 3: upsert custom tests (NOT blind insert — prevents duplicates)
        for custom_test in (custom_tests or []):
            if custom_test.strip():
                normalized = normalize_investigation_name(custom_test)
                existing = investigation_repository.get_by_intake_and_type(
                    intake_id, normalized, columns="id, status"
                )
                if existing:
                    investigation_repository.update_by_intake_and_type(
                        intake_id, normalized, {
                            "status": "approved",
                            "approved_at": now,
                            "approved_by": doctor_name,
                            "review_notes": doctor_notes,
                        }
                    )
                else:
                    investigation_repository.create({
                        "intake_id": intake_id,
                        "investigation_type": normalized,
                        "status": "approved",
                        "approved_at": now,
                        "approved_by": doctor_name,
                        "review_notes": doctor_notes,
                    })

    except Exception as step_exc:
        # Compensating rollback: restore each investigation to its snapshot state
        logger.error(
            "[PRATHAM/UPDATE] Step 2/3 failed for intake %s: %s. "
            "Compensating: restoring snapshot.",
            intake_id, step_exc,
        )
        try:
            for inv_type, old_fields in snapshot.items():
                investigation_repository.update_by_intake_and_type(
                    intake_id, inv_type, {
                        "status": old_fields["status"] or "rejected",
                        "approved_at": old_fields.get("approved_at"),
                        "approved_by": old_fields.get("approved_by"),
                        "rejected_at": old_fields.get("rejected_at"),
                        "rejected_by": old_fields.get("rejected_by"),
                        "review_notes": old_fields.get("review_notes"),
                    }
                )
        except Exception as rollback_exc:
            logger.error(
                "[PRATHAM/UPDATE] Compensating rollback also failed for intake %s: %s. "
                "Manual intervention required.",
                intake_id, rollback_exc,
            )
        raise  # Re-raise original exception so caller returns HTTP 500

    # ── Step 4: Audit log (AFTER mutation succeeded) ────────────────────
    new_approved = sorted(approved_tests + [
        normalize_investigation_name(c) for c in (custom_tests or []) if c.strip()
    ])
    new_rejected = sorted([
        inv_type for inv_type in snapshot
        if inv_type not in new_approved
    ])

    audit_reason = (
        f"Investigation decision updated. "
        f"Previous: Approved=[{', '.join(sorted(old_approved))}], "
        f"Rejected=[{', '.join(sorted(old_rejected))}]. "
        f"Updated: Approved=[{', '.join(new_approved)}], "
        f"Rejected=[{', '.join(new_rejected)}]. "
        f"Notes: {doctor_notes or 'none'}"
    )

    log_status_transition(
        intake_id=intake_id,
        old_status=WorkflowStatus.APPROVED.value,
        new_status=WorkflowStatus.APPROVED.value,
        actor_type="Doctor",
        actor_name=doctor_name,
        reason=audit_reason,
    )

    # ── Step 5: Self-transition APPROVED→APPROVED ───────────────────────
    wf_ok = update_workflow_status(
        intake_id=intake_id,
        new_status=WorkflowStatus.APPROVED.value,
        actor_type="Doctor",
        actor_name=doctor_name,
        reason=f"Investigations updated: {', '.join(new_approved) or 'none'}",
    )
    if not wf_ok:
        logger.warning(
            "[PRATHAM/UPDATE] Workflow status self-transition failed for intake %s "
            "(investigations already updated — workflow log may be inconsistent).",
            intake_id,
        )

    total = len(approved_tests) + len([c for c in (custom_tests or []) if c.strip()])
    return {
        "intake_id":      intake_id,
        "approved_count": total,
        "status":         WorkflowStatus.APPROVED.value,
    }

