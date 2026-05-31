"""
Evidence Pydantic Models — Imaging, Labs, and Aggregated Evidence
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ── Shared ────────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    normal = "normal"
    mild = "mild"
    moderate = "moderate"
    severe = "severe"
    critical = "critical"


# ── Imaging ───────────────────────────────────────────────────────────────────

class ImagingModality(str, Enum):
    xray = "xray"
    ct = "ct"
    mri = "mri"
    ultrasound = "ultrasound"
    pet = "pet"


class ImagingFinding(BaseModel):
    """A single finding from an imaging study."""

    region: str = Field(..., description="Anatomical region, e.g. 'right lower lobe'")
    finding: str = Field(..., description="Radiological finding description")
    severity: Severity = Severity.normal


class ImagingRequest(BaseModel):
    """Request payload for image analysis."""

    patient_id: uuid.UUID
    modality: ImagingModality = ImagingModality.xray
    image_url: str | None = Field(None, description="URL to the uploaded image (optional stub)")
    clinical_context: str | None = Field(None, max_length=500)


class ImagingResult(BaseModel):
    """Result from imaging analysis (stub)."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    patient_id: uuid.UUID
    modality: ImagingModality
    findings: list[ImagingFinding] = Field(default_factory=list)
    impression: str
    overall_severity: Severity = Severity.normal
    analysed_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)


# ── Labs ──────────────────────────────────────────────────────────────────────

class LabStatus(str, Enum):
    normal = "normal"
    low = "low"
    high = "high"
    critical_low = "critical_low"
    critical_high = "critical_high"


class LabValue(BaseModel):
    """A single lab test result."""

    test_name: str
    value: float
    unit: str
    reference_range_low: float | None = None
    reference_range_high: float | None = None
    status: LabStatus = LabStatus.normal


class LabRequest(BaseModel):
    """Request payload for lab result processing."""

    patient_id: uuid.UUID
    panel_name: str = Field(..., description="e.g. 'FBC', 'LFT', 'U&E', 'Troponin'")
    results: list[LabValue]


class LabResult(BaseModel):
    """Processed lab result with flags."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    patient_id: uuid.UUID
    panel_name: str
    results: list[LabValue]
    critical_flags: list[str] = Field(default_factory=list)
    processed_at: datetime = Field(default_factory=datetime.utcnow)


# ── Aggregated Evidence ───────────────────────────────────────────────────────

class AggregatedEvidence(BaseModel):
    """Unified evidence report combining vitals, imaging, and labs."""

    patient_id: uuid.UUID
    summary: str
    overall_severity: Severity
    imaging_results: list[ImagingResult] = Field(default_factory=list)
    lab_results: list[LabResult] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
