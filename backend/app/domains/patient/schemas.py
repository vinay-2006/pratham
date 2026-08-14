"""
PRATHAM Patient DTOs v1 — Typed models for patient data responses.

Domain Ownership: Patient
Version: v1
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PatientDTO(BaseModel):
    """Patient record as returned by the API."""

    id: str
    first_name: str
    last_name: str
    display_name: str
    date_of_birth: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    contact_number: Optional[str] = None
    allergies: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    past_medical_history: list[str] = Field(default_factory=list)
    created_at: Optional[str] = None


class PatientSummaryDTO(BaseModel):
    """Lightweight patient summary for list views."""

    id: str
    display_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
