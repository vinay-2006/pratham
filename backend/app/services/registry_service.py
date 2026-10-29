"""
RegistryService — Business logic for the permanent historical patient registry.

Domain: Patient Lifecycle / Registry
Responsibility: Build the all-time patient registry list, including
                report-availability flag and who closed each closed case.

Extracted from: api/investigations.py::get_registry (L1294-1361)

Safety justification:
  ✓ Read-only — zero writes, zero state transitions
  ✓ Batch-queries only (list_with_status_filter, get_logs_by_intake_ids)
  ✓ No workflow ownership — queries audit logs, does not modify them
  ✓ Existing repositories (intake, workflow) are sufficient
  ✓ Response dict keys and types are unchanged

Logic owned here:
  • closed_by_map batch-lookup (one sorted-log scan to find latest actor)
  • report_available derivation (which statuses imply a report exists)
  • case_id fallback format "PRA-2026-{id[:6].upper()}"
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.domains.triage.repository import intake_repository
from app.domains.workflow.repository import workflow_repository
from app.models.workflow import WorkflowStatus
from app.services.workflow_service import resolve_intakes_status
from app.utils.patient_utils import build_display_name

logger = logging.getLogger(__name__)

# Statuses for which a clinical report is considered available to the doctor
REPORT_AVAILABLE_STATUSES: frozenset[str] = frozenset({
    WorkflowStatus.REPORT_READY.value,
    WorkflowStatus.UNDER_REVIEW.value,
    WorkflowStatus.CLOSED.value,
})


def get_patient_registry() -> List[Dict[str, Any]]:
    """
    Return the full historical patient registry list.

    Fetches all intakes (no status filter), resolves statuses,
    batch-fetches the closing actor for every closed case,
    and returns a flat list of registry entries.

    Returns a list of registry dicts (same shape as original endpoint).

    Raises Exception on any repository failure (caller maps to HTTP 500).
    """
    res_data = intake_repository.list_with_status_filter(
        columns=(
            "id, case_id, arrival_type, status, created_at, "
            "patients(first_name, last_name, gender, date_of_birth)"
        ),
    )

    intakes_resolved = resolve_intakes_status(res_data)

    # Batch-fetch the closing actor for all closed cases
    closed_intake_ids = [
        item["id"]
        for item in intakes_resolved
        if item.get("status") == WorkflowStatus.CLOSED.value
    ]
    closed_by_map: Dict[str, str] = {}
    if closed_intake_ids:
        try:
            log_data = workflow_repository.get_logs_by_intake_ids(
                closed_intake_ids,
                status_filter=WorkflowStatus.CLOSED.value,
                columns="intake_id, actor_name, changed_at",
            )
            # Sort descending by changed_at; first entry per intake = latest actor
            sorted_logs = sorted(
                log_data,
                key=lambda x: x.get("changed_at", ""),
                reverse=True,
            )
            for log in sorted_logs:
                iid = log["intake_id"]
                if iid not in closed_by_map:
                    closed_by_map[iid] = log["actor_name"]
        except Exception:
            pass  # Non-fatal: closed_by will be None for all closed cases

    registry_items: List[Dict[str, Any]] = []
    for item in intakes_resolved:
        current_status = item.get("status", "intake_submitted")
        patient = item.get("patients") or {}
        name = build_display_name(patient)

        report_available = current_status in REPORT_AVAILABLE_STATUSES
        closed_by = (
            closed_by_map.get(item["id"])
            if current_status == WorkflowStatus.CLOSED.value
            else None
        )

        registry_items.append({
            "intake_id":     item["id"],
            "case_id":       item.get("case_id") or f"PRA-2026-{item['id'][:6].upper()}",
            "patient_name":  name,
            "created_at":    item.get("created_at"),
            "updated_at":    item.get("updated_at") or item.get("created_at"),
            "arrival_type":  item.get("arrival_type") or "walk_in",
            "status":        current_status,
            "report_available": report_available,
            "closed_by":     closed_by,
        })

    return registry_items
