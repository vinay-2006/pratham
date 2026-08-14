"""
PRATHAM Report DTOs v1 — Typed models for report summary responses.

Domain Ownership: Report
Version: v1
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ReportSummaryDTO(BaseModel):
    """Lightweight report summary for list views."""

    intake_id: str
    patient_id: str
    case_id: str
    display_name: str
    severity: Optional[str] = None
    status: str
    report_generated: bool = False
    generated_at: Optional[str] = None
    report_version: str = "v1"


class ReportQualityDTO(BaseModel):
    """Report quality and completeness metadata."""

    overall_completeness: float = 0.0  # 0.0 - 1.0
    data_sources: dict[str, str] = Field(default_factory=dict)  # source -> provenance
    missing_sections: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
