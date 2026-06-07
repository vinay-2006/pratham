"""
Patient Pydantic Models — Emergency Intake Data Flow
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Legacy enums kept for compatibility with other routes ─────────────────────

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


class TriageLevel(str, Enum):
    """Emergency Severity Index (ESI) 1–5."""
    immediate = "1_immediate"
    emergent = "2_emergent"
    urgent = "3_urgent"
    less_urgent = "4_less_urgent"
    non_urgent = "5_non_urgent"


# ── Emergency Intake Models ───────────────────────────────────────────────────

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    contact_number: Optional[str] = None
    allergies: Optional[List[str]] = []
    current_medications: Optional[List[str]] = []
    past_medical_history: Optional[List[str]] = []


class VitalsCreate(BaseModel):
    heart_rate: Optional[int] = None
    spo2: Optional[float] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None


class SymptomsCreate(BaseModel):
    chest_pain: bool = False
    breathlessness: bool = False
    trauma: bool = False
    bleeding: bool = False
    unconsciousness: bool = False
    neurological_symptoms: bool = False


class EmergencyIntakeCreate(BaseModel):
    patient: PatientCreate
    vitals: VitalsCreate
    symptoms: SymptomsCreate
    ambulance_eta: Optional[int] = None
    emergency_description: Optional[str] = None
    chief_complaint: Optional[str] = None


class IntakeResponse(BaseModel):
    patient_id: str
    intake_id: str
    status: str
    severity: Optional[str] = None
    risk_scores: Optional[dict] = None
    investigations_recommended: Optional[List[str]] = None
    preparation_alerts: Optional[List[str]] = None
    nlp_summary: Optional[str] = None


# ── Legacy models kept for compatibility with other routes ────────────────────

class PatientBase(BaseModel):
    """Shared patient fields used across create/update/read."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Gender
    contact_number: str = Field(..., pattern=r"^\+?[0-9\s\-]{7,20}$")
    chief_complaint: str = Field(..., min_length=1, max_length=1000)
    allergies: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    past_medical_history: list[str] = Field(default_factory=list)


class PatientRead(PatientBase):
    """Full patient record returned from the API."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    triage_level: TriageLevel | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class PatientSummary(BaseModel):
    """Lightweight patient summary for list views."""
    id: uuid.UUID
    full_name: str
    triage_level: TriageLevel | None
    created_at: datetime
