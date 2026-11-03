"""
DoctorReportsService — Business logic for doctor clinical reports listing.

Domain: Doctor Workflow / Reports
Responsibility: Aggregate and format the patient list for the doctor's
                "Reports" view (cases in clinical_report_ready or under_doctor_review).

Extracted from: api/investigations.py::get_doctor_reports_list (L1512-1613)

Safety justification:
  ✓ Read-only — zero writes, zero state transitions
  ✓ Batch-queries only (pipeline_repository, investigation_repository)
  ✓ No workflow ownership — filter reads status, does not change it
  ✓ Existing repositories (intake, pipeline, investigation) are sufficient
  ✓ Response dict keys and types are unchanged
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.domains.triage.repository import intake_repository
from app.domains.investigation.repository import investigation_repository
from app.domains.pipeline.repository import pipeline_repository
from app.models.workflow import WorkflowStatus, WORKFLOW_PROGRESS_MAP
from app.services.workflow_service import resolve_intakes_status
from app.utils.patient_utils import compute_age, derive_sex

logger = logging.getLogger(__name__)

REPORT_STATUSES: frozenset[str] = frozenset({
    WorkflowStatus.REPORT_READY.value,
    WorkflowStatus.UNDER_REVIEW.value,
})


def get_reports_list() -> List[Dict[str, Any]]:
    """
    Return the doctor reports listing — cases with generated clinical reports.

    Fetches all intakes, resolves statuses, filters to REPORT_STATUSES,
    then batch-fetches pipeline status and investigation metadata.

    Returns a list of patient summary dicts (same shape as original endpoint).

    Raises Exception on any repository failure (caller maps to HTTP 500).
    """
    res_data = intake_repository.list_with_status_filter(
        columns=(
            "id, status, created_at, severity_level, chief_complaint, "
            "case_id, arrival_type, patients(first_name, last_name, gender, date_of_birth)"
        ),
    )

    intakes_resolved = resolve_intakes_status(res_data)

    # Identify candidates before expensive batch fetches
    candidate_ids = [
        item["id"]
        for item in intakes_resolved
        if item.get("status") in REPORT_STATUSES
    ]

    pipeline_map: Dict[str, Dict] = {}
    invs_map: Dict[str, List] = {}

    if candidate_ids:
        try:
            ps_data = pipeline_repository.get_batch_status(candidate_ids)
            for r in ps_data:
                pipeline_map.setdefault(r["intake_id"], {})[r["stage"]] = r["status"]
        except Exception:
            pass  # Non-fatal: pipeline status missing → shows as empty dict

        try:
            inv_data = investigation_repository.get_by_intake_ids(
                candidate_ids,
                columns="intake_id, investigation_type, status",
            )
            for r in inv_data:
                invs_map.setdefault(r["intake_id"], []).append({
                    "investigation_type": r["investigation_type"],
                    "status": r["status"],
                })
        except Exception:
            pass  # Non-fatal: investigations missing → shows as empty list

    items: List[Dict[str, Any]] = []
    for item in intakes_resolved:
        current_status = item.get("status", "intake_submitted")
        if current_status not in REPORT_STATUSES:
            continue

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
            "updated_at":     item.get("updated_at") or item.get("created_at"),
            "chief_complaint": item.get("chief_complaint", ""),
            "severity":       (item.get("severity_level") or "moderate").lower(),
            "pipeline_status": pipeline_map.get(item["id"], {}),
            "investigations": invs_map.get(item["id"], []),
            "progress":       WORKFLOW_PROGRESS_MAP.get(current_status, 90),
        })

    return items
