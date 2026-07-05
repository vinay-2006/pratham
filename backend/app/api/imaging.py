"""
POST /evidence/xray — X-Ray imaging analysis endpoint (stub)
"""

from __future__ import annotations

from fastapi import APIRouter
from app.models.evidence import ImagingRequest, ImagingResult, ImagingFinding, Severity

from app.core.logging_service import log_event
import logging

router = APIRouter()


@router.post("/xray", response_model=ImagingResult, deprecated=True)
async def analyse_xray(payload: ImagingRequest) -> ImagingResult:
    """
    Analyse a chest X-ray and return structured radiology findings.

    [DEPRECATED] Stub response — PyTorch CXR model integration pending.
    """
    log_event("Deprecated /evidence/xray stub endpoint invoked", level=logging.WARNING, pipeline_stage="DEPRECATED")
    import uuid
    from datetime import datetime

    return ImagingResult(
        id=uuid.uuid4(),
        patient_id=payload.patient_id,
        modality=payload.modality,
        findings=[
            ImagingFinding(
                region="right lower lobe",
                finding="Increased opacity consistent with consolidation",
                severity=Severity.moderate,
            ),
            ImagingFinding(
                region="cardiac silhouette",
                finding="Normal cardiothoracic ratio",
                severity=Severity.normal,
            ),
        ],
        impression=(
            "Stub: Probable right lower lobe consolidation. "
            "Clinical correlation advised. No pneumothorax detected."
        ),
        overall_severity=Severity.moderate,
        analysed_at=datetime.utcnow(),
        confidence_score=0.0,
    )
