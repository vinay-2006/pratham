"""
PRATHAM Repository Interfaces — Protocol-based contracts for data access.

Every repository implements a Protocol defined here. This allows:
 - Services to depend on interfaces, not implementations
 - Swapping Supabase for PostgreSQL, FHIR, or Mock without changing services
 - Clear documentation of what each repository must provide

Usage:
    class MyService:
        def __init__(self, repo: PatientRepositoryProtocol):
            self._repo = repo

Domain Ownership: shared (cross-cutting)
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable


# ── Patient Repository ───────────────────────────────────────────────────────

@runtime_checkable
class PatientRepositoryProtocol(Protocol):
    """Data access contract for the patients table."""

    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get_by_id(self, patient_id: str) -> Optional[dict[str, Any]]: ...
    def search(self, query: str, limit: int = 50) -> list[dict[str, Any]]: ...


# ── Triage Repository ────────────────────────────────────────────────────────

@runtime_checkable
class IntakeRepositoryProtocol(Protocol):
    """Data access contract for the emergency_intake table."""

    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get_by_id(self, intake_id: str) -> Optional[dict[str, Any]]: ...
    def update_status(self, intake_id: str, status: str) -> None: ...
    def get_active_intakes(self) -> list[dict[str, Any]]: ...
    def get_by_patient_id(self, patient_id: str) -> list[dict[str, Any]]: ...


@runtime_checkable
class VitalsRepositoryProtocol(Protocol):
    """Data access contract for the vitals table."""

    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get_by_intake_id(self, intake_id: str) -> Optional[dict[str, Any]]: ...


@runtime_checkable
class SymptomsRepositoryProtocol(Protocol):
    """Data access contract for the symptoms table."""

    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get_by_intake_id(self, intake_id: str) -> Optional[dict[str, Any]]: ...


# ── Workflow Repository ──────────────────────────────────────────────────────

@runtime_checkable
class WorkflowRepositoryProtocol(Protocol):
    """Data access contract for the workflow_logs table."""

    def log_transition(
        self,
        intake_id: str,
        old_status: str,
        new_status: str,
        actor_type: str,
        actor_name: str,
        reason: Optional[str] = None,
    ) -> dict[str, Any]: ...

    def get_latest_status(self, intake_id: str) -> Optional[str]: ...
    def get_logs(self, intake_id: str) -> list[dict[str, Any]]: ...
    def get_batch_latest_status(self, intake_ids: list[str]) -> dict[str, str]: ...


# ── Investigation Repository ────────────────────────────────────────────────

@runtime_checkable
class InvestigationRepositoryProtocol(Protocol):
    """Data access contract for the investigation_recommendations table."""

    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def create_batch(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]: ...
    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]: ...
    def update_status(self, recommendation_id: str, updates: dict[str, Any]) -> None: ...
    def update_batch_by_intake(
        self, intake_id: str, updates: dict[str, Any], status_filter: Optional[str] = None
    ) -> None: ...


# ── Evidence Repository ──────────────────────────────────────────────────────

@runtime_checkable
class EvidenceRepositoryProtocol(Protocol):
    """Data access contract for the evidence table."""

    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]: ...
    def get_by_id(self, evidence_id: str) -> Optional[dict[str, Any]]: ...
    def delete(self, evidence_id: str) -> None: ...
    def count_by_intake_id(self, intake_id: str) -> int: ...


# ── AI Results Repositories ──────────────────────────────────────────────────

@runtime_checkable
class NLPRepositoryProtocol(Protocol):
    """Data access contract for the nlp_extractions table."""

    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get_by_intake_id(self, intake_id: str) -> Optional[dict[str, Any]]: ...


@runtime_checkable
class RiskScoresRepositoryProtocol(Protocol):
    """Data access contract for the risk_scores table."""

    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get_by_intake_id(self, intake_id: str) -> Optional[dict[str, Any]]: ...


@runtime_checkable
class LabResultsRepositoryProtocol(Protocol):
    """Data access contract for the lab_results table."""

    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]: ...


@runtime_checkable
class ImagingResultsRepositoryProtocol(Protocol):
    """Data access contract for the imaging_results table."""

    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]: ...


@runtime_checkable
class AggregationResultsRepositoryProtocol(Protocol):
    """Data access contract for the aggregation_results table."""

    def create(self, data: dict[str, Any]) -> dict[str, Any]: ...
    def get_by_intake_id(self, intake_id: str) -> Optional[dict[str, Any]]: ...


# ── Pipeline Repository ──────────────────────────────────────────────────────

@runtime_checkable
class PipelineRepositoryProtocol(Protocol):
    """Data access contract for the pipeline_status table."""

    def initialize(self, intake_id: str, stages: tuple[str, ...]) -> list[dict[str, Any]]: ...
    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]: ...
    def update_stage(self, intake_id: str, stage: str, updates: dict[str, Any]) -> None: ...
    def get_batch_status(self, intake_ids: list[str]) -> list[dict[str, Any]]: ...


# ── Notification Repository ──────────────────────────────────────────────────

@runtime_checkable
class AlertsRepositoryProtocol(Protocol):
    """Data access contract for the preparation_alerts table."""

    def create_batch(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]: ...
    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]: ...
