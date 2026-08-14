"""
PRATHAM Workflow DTOs v1 — Typed models for workflow state and timeline.

Domain Ownership: Workflow
Version: v1
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class WorkflowStateDTO(BaseModel):
    """Current resolved workflow state for a patient."""

    intake_id: str
    current_status: str
    status_label: str
    is_terminal: bool = False
    last_changed_at: Optional[str] = None
    last_actor: Optional[str] = None


class TimelineEventDTO(BaseModel):
    """A single event in the patient timeline."""

    event: str
    timestamp: str
    icon: str = "circle"
    type: str = "status"
    actor: Optional[str] = None
    details: Optional[str] = None


class TimelineDTO(BaseModel):
    """Complete patient timeline."""

    intake_id: str
    events: list[TimelineEventDTO] = Field(default_factory=list)
