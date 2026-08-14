"""
PRATHAM Dashboard DTOs v1 — Typed response models for queue and dashboard views.

These DTOs match the CURRENT API response shapes exactly.
They are prepared for future migration but do not replace existing
response construction yet.

Domain Ownership: Dashboard
Version: v1
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Nurse Queue ──────────────────────────────────────────────────────────────

class QueuePatientDTO(BaseModel):
    """A single patient in the nurse queue view."""

    # Patient identity
    intake_id: str
    patient_id: str
    case_id: str
    display_name: str
    age: Optional[int] = None
    gender: Optional[str] = None

    # Visit info
    arrival_type: str = "walk_in"
    chief_complaint: Optional[str] = None
    severity: Optional[str] = None
    created_at: Optional[str] = None

    # Workflow
    status: str
    status_label: str

    # Progress
    investigation_count: int = 0
    evidence_count: int = 0
    approved_count: int = 0
    pipeline_progress: Optional[dict[str, Any]] = None

    # Vitals summary
    heart_rate: Optional[int] = None
    spo2: Optional[float] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None


class QueueStatsDTO(BaseModel):
    """Aggregate statistics for the nurse queue."""

    total_active: int = 0
    en_route: int = 0
    awaiting_approval: int = 0
    investigations_approved: int = 0
    evidence_pending: int = 0
    analysis_running: int = 0
    report_ready: int = 0
    under_review: int = 0
    case_closed_today: int = 0


# ── Doctor Dashboard ─────────────────────────────────────────────────────────

class DoctorDashboardStatsDTO(BaseModel):
    """Aggregate statistics for the doctor dashboard."""

    total_patients: int = 0
    pending_approvals: int = 0
    cases_closed: int = 0
    reports_ready: int = 0
    under_review: int = 0
    average_turnaround_hours: Optional[float] = None


class DoctorReviewPatientDTO(BaseModel):
    """A patient in the doctor review worklist."""

    intake_id: str
    patient_id: str
    case_id: str
    display_name: str
    age: Optional[int] = None
    gender: Optional[str] = None

    severity: Optional[str] = None
    chief_complaint: Optional[str] = None
    arrival_type: str = "walk_in"
    created_at: Optional[str] = None

    status: str
    status_label: str

    investigations: list[dict[str, Any]] = Field(default_factory=list)
    investigation_count: int = 0


class DoctorReportItemDTO(BaseModel):
    """A report item in the doctor reports list."""

    intake_id: str
    patient_id: str
    case_id: str
    display_name: str
    age: Optional[int] = None
    gender: Optional[str] = None

    severity: Optional[str] = None
    status: str
    status_label: str

    created_at: Optional[str] = None
    report_ready: bool = False


# ── Command Center ───────────────────────────────────────────────────────────

class CommandCenterDTO(BaseModel):
    """Real-time command center overview data."""

    total_active_patients: int = 0
    total_en_route: int = 0
    total_awaiting_approval: int = 0
    total_under_analysis: int = 0
    total_reports_ready: int = 0
    average_pipeline_duration_ms: Optional[float] = None
    system_status: str = "OPERATIONAL"
