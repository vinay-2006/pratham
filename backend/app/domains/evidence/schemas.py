"""
PRATHAM Evidence DTOs v1 — Typed models for evidence responses.

Domain Ownership: Evidence
Version: v1
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class EvidenceItemDTO(BaseModel):
    """A single evidence file record."""

    id: str
    intake_id: str
    investigation_id: Optional[str] = None
    investigation_type: Optional[str] = None
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_at: Optional[str] = None
    analysis_status: Optional[str] = None  # pending | completed | failed


class EvidenceCompletenessDTO(BaseModel):
    """Evidence upload completeness for an intake."""

    intake_id: str
    total_required: int = 0
    total_uploaded: int = 0
    completeness: float = 0.0  # 0.0 - 1.0
    missing: list[str] = Field(default_factory=list)
