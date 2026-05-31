"""
POST /risk/assess — Patient risk assessment endpoint (stub)
"""

from __future__ import annotations

import uuid
from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.vitals import VitalsCreate

router = APIRouter()


class RiskCategory(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class RiskFactor(BaseModel):
    factor: str
    contribution_score: float = Field(..., ge=0.0, le=1.0)
    description: str


class RiskRequest(BaseModel):
    patient_id: uuid.UUID
    vitals: VitalsCreate
    symptom_entities: list[str] = Field(default_factory=list)
    age: int = Field(..., ge=0, le=130)
    comorbidities: list[str] = Field(default_factory=list)


class RiskResponse(BaseModel):
    patient_id: uuid.UUID
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_category: RiskCategory
    risk_factors: list[RiskFactor]
    recommendation: str
    confidence: float = Field(..., ge=0.0, le=1.0)


@router.post("/assess", response_model=RiskResponse)
async def assess_risk(payload: RiskRequest) -> RiskResponse:
    """
    Calculate a composite risk score for a patient.

    Stub response — ML risk model integration pending.
    """
    return RiskResponse(
        patient_id=payload.patient_id,
        risk_score=72.5,
        risk_category=RiskCategory.high,
        risk_factors=[
            RiskFactor(
                factor="elevated_heart_rate",
                contribution_score=0.35,
                description="Heart rate above 100 bpm indicates potential haemodynamic compromise.",
            ),
            RiskFactor(
                factor="low_spo2",
                contribution_score=0.40,
                description="SpO₂ below 94% suggests respiratory insufficiency.",
            ),
            RiskFactor(
                factor="chest_pain_complaint",
                contribution_score=0.25,
                description="Chest pain as chief complaint with cardiac risk profile.",
            ),
        ],
        recommendation="Immediate ECG, troponin, and senior clinician review required.",
        confidence=0.0,  # Stub: no model loaded
    )
