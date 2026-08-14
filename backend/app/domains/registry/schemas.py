"""
PRATHAM Registry DTOs v1 — Typed response models for the case registry.

Domain Ownership: Registry
Version: v1
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class RegistryPatientDTO(BaseModel):
    """A single case in the permanent registry view."""

    intake_id: str
    patient_id: str
    case_id: str
    display_name: str
    age: Optional[int] = None
    gender: Optional[str] = None

    severity: Optional[str] = None
    arrival_type: str = "walk_in"
    chief_complaint: Optional[str] = None
    created_at: Optional[str] = None

    status: str
    status_label: str

    closed_by: Optional[str] = None
    closed_at: Optional[str] = None
    closure_reason: Optional[str] = None


class RegistryStatsDTO(BaseModel):
    """Aggregate statistics for the registry."""

    total_cases: int = 0
    total_closed: int = 0
    total_offline: int = 0
    average_case_duration_hours: Optional[float] = None
