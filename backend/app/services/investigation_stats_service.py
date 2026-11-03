"""
InvestigationStatsService — Business logic for queue statistics aggregation.

Domain: Investigations / Nurse Queue
Responsibility: Count total patients and pending-approval investigations
                for sidebar badge display.

REPOSITORY RULES — this service:
  ✓ Contains aggregation logic (deduplication of intake_ids)
  ✓ Coordinates two separate repository reads for a composite answer

  ✗ Does NOT contain API routing or HTTP concerns
  ✗ Does NOT contain workflow state transitions
  ✗ Does NOT contain repository definitions

Extracted from: api/investigations.py::get_queue_stats (L804–826)
"""

from __future__ import annotations

import logging

from app.domains.triage.repository import intake_repository
from app.domains.investigation.repository import investigation_repository

logger = logging.getLogger(__name__)


def get_queue_stats() -> dict:
    """
    Compute lightweight queue stats for sidebar badges.

    Returns:
      total_patients            — total intake count (capped at 500)
      pending_approval_patients — distinct intakes with ≥1 pending_approval investigation

    Raises Exception on any unrecovered repository failure (caller maps to HTTP 500).
    """
    try:
        intake_data = intake_repository.list_all(columns="id", limit=500)
        total = len(intake_data)
        pending_data = investigation_repository.get_by_status(
            "pending_approval", columns="intake_id"
        )
        pending_intake_ids = {r["intake_id"] for r in pending_data}
        return {
            "total_patients": total,
            "pending_approval_patients": len(pending_intake_ids),
        }
    except Exception:
        logger.warning("[Stats] Retrying queue stats after transient error")
        intake_data = intake_repository.list_all(columns="id", limit=500)
        total = len(intake_data)
        pending_data = investigation_repository.get_by_status(
            "pending_approval", columns="intake_id"
        )
        pending_intake_ids = {r["intake_id"] for r in pending_data}
        return {
            "total_patients": total,
            "pending_approval_patients": len(pending_intake_ids),
        }
