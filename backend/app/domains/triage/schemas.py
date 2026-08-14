"""
PRATHAM Triage DTOs v1 — Typed models for intake creation and response.

Domain Ownership: Triage
Version: v1
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class IntakeResponseDTO(BaseModel):
    """Response returned after successful intake creation."""

    patient_id: str
    intake_id: str
    case_id: str
    status: str
    severity: Optional[str] = None
    risk_scores: Optional[dict[str, Any]] = None
    investigations_recommended: Optional[List[str]] = None
    preparation_alerts: Optional[List[str]] = None
    nlp_summary: Optional[str] = None


class VitalsDTO(BaseModel):
    """Vitals data as returned by the API."""

    heart_rate: Optional[int] = None
    spo2: Optional[float] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None


class SymptomsDTO(BaseModel):
    """Symptoms data as returned by the API."""

    chest_pain: bool = False
    breathlessness: bool = False
    trauma: bool = False
    bleeding: bool = False
    unconsciousness: bool = False
    neurological_symptoms: bool = False
