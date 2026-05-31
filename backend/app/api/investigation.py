"""
POST /investigation/recommend — Investigation recommendation endpoint (stub)
"""

from __future__ import annotations

import uuid
from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class InvestigationCategory(str, Enum):
    bloods = "bloods"
    imaging = "imaging"
    ecg = "ecg"
    urine = "urine"
    microbiology = "microbiology"
    other = "other"


class Investigation(BaseModel):
    name: str
    category: InvestigationCategory
    urgency: str = Field(..., description="e.g. 'stat', 'urgent', 'routine'")
    rationale: str
    estimated_turnaround_minutes: int | None = None


class InvestigationRequest(BaseModel):
    patient_id: uuid.UUID
    risk_score: float = Field(..., ge=0.0, le=100.0)
    chief_complaint: str
    symptom_entities: list[str] = Field(default_factory=list)
    age: int = Field(..., ge=0, le=130)
    existing_comorbidities: list[str] = Field(default_factory=list)


class InvestigationResponse(BaseModel):
    patient_id: uuid.UUID
    recommended_investigations: list[Investigation]
    clinical_reasoning: str
    generated_at: str


@router.post("/recommend", response_model=InvestigationResponse)
async def recommend_investigations(payload: InvestigationRequest) -> InvestigationResponse:
    """
    Recommend an investigation panel based on patient presentation and risk.

    Stub response — clinical decision logic pending.
    """
    from datetime import datetime

    return InvestigationResponse(
        patient_id=payload.patient_id,
        recommended_investigations=[
            Investigation(
                name="12-Lead ECG",
                category=InvestigationCategory.ecg,
                urgency="stat",
                rationale="Rule out acute coronary syndrome given chest pain presentation.",
                estimated_turnaround_minutes=5,
            ),
            Investigation(
                name="High-sensitivity Troponin I",
                category=InvestigationCategory.bloods,
                urgency="stat",
                rationale="Serial troponins required for NSTEMI rule-in/rule-out protocol.",
                estimated_turnaround_minutes=60,
            ),
            Investigation(
                name="Chest X-Ray (PA)",
                category=InvestigationCategory.imaging,
                urgency="urgent",
                rationale="Assess cardiac silhouette, pulmonary oedema, pneumothorax.",
                estimated_turnaround_minutes=30,
            ),
            Investigation(
                name="Full Blood Count",
                category=InvestigationCategory.bloods,
                urgency="urgent",
                rationale="Evaluate for anaemia, infection, or haematological abnormality.",
                estimated_turnaround_minutes=45,
            ),
        ],
        clinical_reasoning=(
            "Stub: Based on risk score and chief complaint, ACS workup protocol recommended."
        ),
        generated_at=datetime.utcnow().isoformat(),
    )
