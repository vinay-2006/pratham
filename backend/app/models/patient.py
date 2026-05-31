"""
Patient Pydantic Models
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


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


class PatientCreate(PatientBase):
    """Payload for creating a new patient record."""
    pass


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
