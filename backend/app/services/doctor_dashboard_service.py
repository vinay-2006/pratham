"""
DoctorDashboardService — Business logic for doctor dashboard statistics.

Domain: Doctor Workflow
Responsibility: Aggregate patient status counts and 24-hour trend calculations
                for the doctor dashboard header cards.

REPOSITORY RULES — this service:
  ✓ Contains calculations (24h trend window, status categorisation, count aggregation)
  ✓ Contains business rules (which statuses map to which dashboard card)

  ✗ Does NOT contain API routing or HTTP concerns
  ✗ Does NOT contain DTO transformation
  ✗ Does NOT contain repository definitions
  ✗ Does NOT own workflow state transitions

Extracted from: api/investigations.py::get_doctor_dashboard_stats (L1405–1470)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

from app.domains.triage.repository import intake_repository
from app.models.workflow import WorkflowStatus

logger = logging.getLogger(__name__)


def get_dashboard_stats() -> dict:
    """
    Compute live dashboard statistics and 24-hour trends.

    Reads all intakes (capped at 500) and derives counts by status category.
    No per-patient lifecycle calls are made — status is read directly from DB.

    Returns a dict with:
      total_patients, total_patients_trend,
      cases_closed, cases_closed_trend,
      pending_approvals, pending_approvals_trend,
      clinical_reviews_remaining, clinical_reviews_remaining_trend

    Raises Exception on any repository failure (caller maps to HTTP 500).
    """
    res_data = intake_repository.list_all(
        columns="id, status, created_at",
        limit=500,
    )

    total_patients = 0
    cases_closed = 0
    pending_approvals = 0
    clinical_reviews_remaining = 0

    total_trend = 0
    closed_trend = 0
    pending_trend = 0
    reviews_trend = 0

    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)

    for item in res_data:
        current_status = item.get("status", "intake_submitted")
        total_patients += 1

        try:
            created_at_val = datetime.fromisoformat(
                item["created_at"].replace("Z", "+00:00")
            )
        except Exception:
            continue

        if created_at_val >= one_day_ago:
            total_trend += 1

        if current_status == WorkflowStatus.CLOSED.value:
            cases_closed += 1
            if created_at_val >= one_day_ago:
                closed_trend += 1
        elif current_status == WorkflowStatus.AWAITING_APPROVAL.value:
            pending_approvals += 1
            if created_at_val >= one_day_ago:
                pending_trend += 1
        elif current_status in (
            WorkflowStatus.REPORT_READY.value,
            WorkflowStatus.UNDER_REVIEW.value,
        ):
            clinical_reviews_remaining += 1
            if created_at_val >= one_day_ago:
                reviews_trend += 1

    return {
        "total_patients":                    total_patients,
        "total_patients_trend":              total_trend,
        "cases_closed":                      cases_closed,
        "cases_closed_trend":                closed_trend,
        "pending_approvals":                 pending_approvals,
        "pending_approvals_trend":           pending_trend,
        "clinical_reviews_remaining":        clinical_reviews_remaining,
        "clinical_reviews_remaining_trend":  reviews_trend,
    }
