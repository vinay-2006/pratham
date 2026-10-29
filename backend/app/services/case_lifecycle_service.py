"""
CaseLifecycleService — Orchestration for patient case lifecycle transitions.

Domain: Intake / Case Lifecycle
Responsibility: Orchestrate the three nurse/doctor lifecycle mutations:
                arrival confirmation, case closure, and return-to-nurse.

Extracted from: api/investigations.py
  • confirm_arrival      (L930–959)
  • close_case           (L994–1011)
  • return_to_nurse      (L1067–1085)

Ownership map per mutation:
─────────────────────────────────────────────────────────────────────────────
  HTTP concern      → remains in API layer (routing, path params, HTTP 400/500)
  Orchestration     → this service
  Business rules    → this service (double-step arrival, guard states)
  Persistence       → delegated to intake_repository via workflow_service
  Audit logging     → delegated to workflow_service.update_workflow_status
                      (which calls log_status_transition → workflow_repository)
─────────────────────────────────────────────────────────────────────────────

Transaction boundaries (unchanged from original):
  • confirm_arrival : two sequential update_workflow_status calls
                      (ARRIVED then AWAITING_APPROVAL). No DB transaction.
  • close_case      : one update_workflow_status call.
  • return_to_nurse : one update_workflow_status call.

Rollback behaviour:
  • None of the original mutations have explicit rollback.
  • confirm_arrival: if step 1 fails → returns False (HTTP 400). Step 2 is
    only called after step 1 succeeds. If step 2 fails it is silently
    swallowed by update_workflow_status (logs error, returns False).
    Preserved identically — the original does not check step 2's return value.

Return value semantics:
  • Returns True/False from update_workflow_status. Caller converts False → HTTP 400.
"""

from __future__ import annotations

import logging

from app.models.workflow import WorkflowStatus
from app.services.workflow_service import update_workflow_status

logger = logging.getLogger(__name__)


def confirm_arrival(intake_id: str, actor_name: str) -> bool:
    """
    Manually confirm patient arrival with a two-step workflow transition.

    Step 1: any current state  →  ARRIVED
    Step 2: ARRIVED            →  AWAITING_APPROVAL

    Returns False if step 1 transition is rejected by state machine (invalid transition).
    Step 2 failure is not surfaced — matches original behaviour where its return
    value is not checked.

    Raises Exception on unexpected failure.
    """
    # Step 1: transition to ARRIVED
    success = update_workflow_status(
        intake_id=intake_id,
        new_status=WorkflowStatus.ARRIVED.value,
        actor_type="Nurse",
        actor_name=actor_name,
        reason="Manual arrival confirmation",
    )
    if not success:
        return False

    # Step 2: immediately advance to AWAITING_APPROVAL
    update_workflow_status(
        intake_id=intake_id,
        new_status=WorkflowStatus.AWAITING_APPROVAL.value,
        actor_type="System",
        actor_name="Triage Pipeline",
        reason="Patient checked in for clinical triage.",
    )
    return True


def close_case(intake_id: str, actor_name: str, reason: str) -> bool:
    """
    Close a patient case from the Doctor report page.

    Returns False if the transition is rejected by state machine (invalid transition).

    Raises Exception on unexpected failure.
    """
    return update_workflow_status(
        intake_id=intake_id,
        new_status=WorkflowStatus.CLOSED.value,
        actor_type="Doctor",
        actor_name=actor_name,
        reason=reason,
    )


def return_to_nurse(intake_id: str, actor_name: str, reason: str) -> bool:
    """
    Return a case to the Nurse for re-upload or details correction.

    Transitions: AWAITING_APPROVAL → EVIDENCE_UPLOAD_PENDING

    The target state UPLOAD_PENDING must be reachable from the current state
    via the VALID_TRANSITIONS state machine. If not, returns False.

    Returns False if the transition is rejected by state machine.

    Raises Exception on unexpected failure.
    """
    return update_workflow_status(
        intake_id=intake_id,
        new_status=WorkflowStatus.UPLOAD_PENDING.value,
        actor_type="Doctor",
        actor_name=actor_name,
        reason=f"Returned to Nurse: {reason}",
    )
