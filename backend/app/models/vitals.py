"""
Vitals Pydantic Models
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ConsciousnessLevel(str, Enum):
    alert = "alert"
    voice = "voice"
    pain = "pain"
    unresponsive = "unresponsive"


class RespiratoryPattern(str, Enum):
    normal = "normal"
    tachypnoeic = "tachypnoeic"
    bradypnoeic = "bradypnoeic"
    laboured = "laboured"
    cheyne_stokes = "cheyne_stokes"


class VitalsCreate(BaseModel):
    """Payload for recording a patient's vitals."""

    patient_id: uuid.UUID

    # Haemodynamics
    systolic_bp: int = Field(..., ge=0, le=300, description="Systolic blood pressure (mmHg)")
    diastolic_bp: int = Field(..., ge=0, le=200, description="Diastolic blood pressure (mmHg)")
    heart_rate: int = Field(..., ge=0, le=300, description="Heart rate (bpm)")
    map_value: float | None = Field(None, description="Mean arterial pressure (mmHg)")

    # Oxygenation
    spo2: float = Field(..., ge=0.0, le=100.0, description="Peripheral oxygen saturation (%)")
    respiratory_rate: int = Field(..., ge=0, le=60, description="Breaths per minute")
    respiratory_pattern: RespiratoryPattern = RespiratoryPattern.normal

    # Temperature
    temperature_celsius: float = Field(..., ge=30.0, le=45.0, description="Body temperature (°C)")

    # Neurology
    gcs_score: int = Field(..., ge=3, le=15, description="Glasgow Coma Scale (3–15)")
    consciousness: ConsciousnessLevel = ConsciousnessLevel.alert

    # Pain
    pain_score: int = Field(..., ge=0, le=10, description="NRS pain score (0–10)")

    # Glucose
    blood_glucose_mmol: float | None = Field(None, ge=0.0, le=100.0, description="Blood glucose (mmol/L)")


class VitalsRead(VitalsCreate):
    """Vitals record returned from the API."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    recorded_by: str | None = None

    model_config = {"from_attributes": True}


class VitalsTrend(BaseModel):
    """Aggregate trend data for a patient over time."""

    patient_id: uuid.UUID
    readings: list[VitalsRead]
    trend_alert: str | None = Field(
        None,
        description="Human-readable alert if a deterioration trend is detected",
    )
