"""
POST /evidence/labs — Lab result processing endpoint (stub)
"""

from __future__ import annotations

from fastapi import APIRouter
from app.models.evidence import LabRequest, LabResult, LabStatus

from app.core.logging_service import log_event
import logging

router = APIRouter()


@router.post("/labs", response_model=LabResult, deprecated=True)
async def process_labs(payload: LabRequest) -> LabResult:
    """
    Process a lab panel and return flagged results.

    [DEPRECATED] Stub response — lab anomaly detection model pending.
    """
    log_event("Deprecated /evidence/labs stub endpoint invoked", level=logging.WARNING, pipeline_stage="DEPRECATED")
    import uuid
    from datetime import datetime

    critical_flags: list[str] = []
    for lab in payload.results:
        if lab.status in (LabStatus.critical_high, LabStatus.critical_low):
            critical_flags.append(
                f"CRITICAL: {lab.test_name} = {lab.value} {lab.unit} ({lab.status.value})"
            )

    return LabResult(
        id=uuid.uuid4(),
        patient_id=payload.patient_id,
        panel_name=payload.panel_name,
        results=payload.results,
        critical_flags=critical_flags or ["Stub: No critical values detected"],
        processed_at=datetime.utcnow(),
    )
