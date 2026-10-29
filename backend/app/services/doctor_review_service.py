"""
DoctorReviewService — Business logic for doctor clinical worklist.

Domain: Doctor Workflow / Investigations
Responsibility: Aggregate and format the patient worklist shown to doctors
                during the investigation review phase.

Extracted from: api/investigations.py::get_doctor_review_patients (L1406-1507)

Safety justification:
  ✓ Read-only — zero writes, zero state transitions
  ✓ Batch-queries only (get_by_intake_ids, list_recent)
  ✓ No asyncio.gather — sequential reads; no parallel coordination needed
  ✓ No workflow ownership — filter logic reads status, does not change it
  ✓ Existing repositories (intake, investigation) are sufficient
  ✓ Response dict keys and types are unchanged
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from app.domains.triage.repository import intake_repository
from app.domains.investigation.repository import investigation_repository
from app.models.workflow import WorkflowStatus, WORKFLOW_PROGRESS_MAP
from app.services.workflow_service import resolve_intakes_status
from app.utils.patient_utils import compute_age, derive_sex

logger = logging.getLogger(__name__)

# Statuses that appear in the doctor's active review worklist
REVIEW_STATUSES: frozenset[str] = frozenset({
    WorkflowStatus.AWAITING_APPROVAL.value,
    WorkflowStatus.APPROVED.value,
    WorkflowStatus.UPLOAD_PENDING.value,
    WorkflowStatus.ANALYSIS_RUNNING.value,
})


def get_doctor_review_list() -> tuple[List[Dict[str, Any]], float]:
    """
    Return (items, elapsed_ms) for the doctor active-cases worklist.

    Fetches all recent intakes, resolves statuses, filters to REVIEW_STATUSES,
    then batch-fetches investigation recommendations to avoid N+1 queries.

    Returns:
      items       — list of patient summary dicts (same shape as original)
      elapsed_ms  — wall-clock milliseconds for the DB phase (for logging)

    Raises Exception on any repository failure (caller maps to HTTP 500).
    """
    t0 = time.monotonic()

    res_data = intake_repository.list_recent(
        columns=(
            "id, status, created_at, severity_level, chief_complaint, "
            "case_id, arrival_type, ambulance_eta, "
            "patients(first_name, last_name, gender, date_of_birth)"
        ),
        limit=200,
    )

    intakes_resolved = resolve_intakes_status(res_data)

    # Filter to review statuses — no per-patient lifecycle DB calls
    candidate_items = [
        (item, item.get("status", ""))
        for item in intakes_resolved
        if item.get("status", "") in REVIEW_STATUSES
    ]

    # Batch-fetch investigation recommendations to avoid N+1 queries
    candidate_ids = [item["id"] for item, _ in candidate_items]
    inv_map: Dict[str, list] = {iid: [] for iid in candidate_ids}
    if candidate_ids:
        inv_data = investigation_repository.get_by_intake_ids(
            candidate_ids,
            columns=(
                "id, intake_id, status, investigation_type, "
                "approved_at, approved_by, rejected_at, rejected_by, review_notes"
            ),
        )
        for inv in inv_data:
            iid = inv.get("intake_id")
            if iid in inv_map:
                inv_map[iid].append(inv)

    items: List[Dict[str, Any]] = []
    for item, current_status in candidate_items:
        patient = item.get("patients") or {}
        name = (
            f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
            or "Unknown Patient"
        )

        age = compute_age(patient.get("date_of_birth"))
        sex = derive_sex(patient.get("gender"))

        items.append({
            "intake_id":      item["id"],
            "case_id":        item.get("case_id") or f"PRA-2026-{item['id'][:6].upper()}",
            "patient_name":   name,
            "age":            age,
            "sex":            sex,
            "arrival_type":   item.get("arrival_type") or "walk_in",
            "status":         current_status,
            "workflow_status": current_status,
            "created_at":     item.get("created_at"),
            "chief_complaint": item.get("chief_complaint", ""),
            "severity":       (item.get("severity_level") or "moderate").lower(),
            "investigations": inv_map.get(item["id"], []),
            "progress":       WORKFLOW_PROGRESS_MAP.get(current_status, 10),
        })

    elapsed_ms = (time.monotonic() - t0) * 1000
    return items, elapsed_ms
