"""
POST /intake — Emergency patient intake endpoint (stub)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter
from app.models.patient import PatientCreate, PatientRead, TriageLevel

router = APIRouter()


@router.post("/intake", response_model=PatientRead, status_code=201)
async def create_intake(payload: PatientCreate) -> PatientRead:
    """
    Accept a new emergency patient intake form.

    Returns a stub PatientRead with a generated patient ID and default
    triage level. No database write occurs in this scaffold version.
    """
    return PatientRead(
        **payload.model_dump(),
        id=uuid.uuid4(),
        triage_level=TriageLevel.urgent,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
