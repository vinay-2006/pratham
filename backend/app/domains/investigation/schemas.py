"""
PRATHAM Investigation DTOs v1 — Typed models for investigation responses.

Domain Ownership: Investigation
Version: v1
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class InvestigationDTO(BaseModel):
    """A single investigation recommendation."""

    id: Optional[str] = None
    intake_id: str
    investigation_type: str
    canonical_name: Optional[str] = None
    status: str = "pending_approval"
    analysis_type: Optional[str] = None  # "lab" | "imaging" | None

    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[str] = None
    review_notes: Optional[str] = None

    created_at: Optional[str] = None
    source: str = "system"  # "system" | "doctor"


class InvestigationSummaryDTO(BaseModel):
    """Summary of investigations for an intake."""

    intake_id: str
    total: int = 0
    approved: int = 0
    rejected: int = 0
    pending: int = 0
    investigations: list[InvestigationDTO] = Field(default_factory=list)
