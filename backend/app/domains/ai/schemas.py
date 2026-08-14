"""
PRATHAM AI DTOs v1 — Typed models for AI analysis result responses.

Domain Ownership: AI
Version: v1
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class NLPExtractionDTO(BaseModel):
    """NLP clinical signal extraction results."""

    intake_id: str
    cardiac_risk_flag: bool = False
    respiratory_distress: bool = False
    neurological_concern: bool = False
    trauma_flag: bool = False
    infection_flag: bool = False
    raw_summary: Optional[str] = None
    provenance: str = "llm"  # llm | rule-based | fallback | mock


class RiskScoresDTO(BaseModel):
    """Risk assessment scores."""

    intake_id: str
    cardiac_risk: int = 0
    respiratory_risk: int = 0
    trauma_risk: int = 0
    neurological_risk: int = 0
    overall_severity: str = "low"
    provenance: str = "rule-based"


class LabResultDTO(BaseModel):
    """Lab analysis ML result."""

    id: Optional[str] = None
    intake_id: str
    model_name: str = "task9_xgboost_heart_model"
    prediction: Optional[str] = None
    probability: Optional[float] = None
    risk_level: Optional[str] = None
    feature_importance: Optional[dict[str, Any]] = None
    created_at: Optional[str] = None


class ImagingResultDTO(BaseModel):
    """Imaging analysis ML result."""

    id: Optional[str] = None
    intake_id: str
    model_name: str = "task10_efficientnetb0_pneumonia"
    prediction: Optional[str] = None
    confidence: Optional[float] = None
    findings: Optional[str] = None
    gradcam_url: Optional[str] = None
    created_at: Optional[str] = None


class AggregationResultDTO(BaseModel):
    """Clinical aggregation result."""

    intake_id: str
    overall_risk_level: Optional[str] = None
    confidence_score: Optional[float] = None
    clinical_summary: Optional[str] = None
    key_findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    created_at: Optional[str] = None
