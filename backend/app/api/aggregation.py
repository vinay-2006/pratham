"""
POST /aggregate — Evidence aggregation endpoint (stub)
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.evidence import AggregatedEvidence, Severity

router = APIRouter()


class AggregationRequest(BaseModel):
    patient_id: uuid.UUID
    include_imaging: bool = True
    include_labs: bool = True
    include_vitals_summary: bool = True


@router.post("/aggregate", response_model=AggregatedEvidence)
async def aggregate_evidence(payload: AggregationRequest) -> AggregatedEvidence:
    """
    Aggregate all available evidence into a unified clinical report.

    Stub response — real aggregation logic and DB queries pending.
    """
    return AggregatedEvidence(
        patient_id=payload.patient_id,
        summary=(
            "Stub: Patient presents with moderate-severity acute presentation. "
            "Chest X-ray shows right lower lobe consolidation. "
            "Labs pending critical flag review. Urgent senior review advised."
        ),
        overall_severity=Severity.moderate,
        imaging_results=[],
        lab_results=[],
        key_findings=[
            "Right lower lobe consolidation on CXR",
            "Elevated inflammatory markers (stub)",
            "SpO₂ trending downward (stub)",
        ],
        recommended_actions=[
            "Commence empirical antibiotics per local protocol",
            "Repeat troponin at 3 hours",
            "Escalate to ICU if SpO₂ < 92% on 4L O₂",
        ],
        generated_at=datetime.utcnow(),
    )
