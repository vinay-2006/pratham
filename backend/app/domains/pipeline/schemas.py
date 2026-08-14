"""
PRATHAM Pipeline DTOs v1 — Typed models for pipeline status responses.

Domain Ownership: Pipeline
Version: v1
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class StageStatusDTO(BaseModel):
    """Status of a single pipeline stage."""

    stage: str
    status: str  # pending | running | completed | failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    attempt_count: int = 0


class PipelineStatusDTO(BaseModel):
    """Complete pipeline status for an intake."""

    intake_id: str
    stages: dict[str, StageStatusDTO]
    overall_progress: float = 0.0  # 0.0 - 1.0
    is_complete: bool = False
    has_failures: bool = False
