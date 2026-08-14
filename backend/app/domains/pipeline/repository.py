"""
PRATHAM Pipeline Repository — Data access for the pipeline_status table.

Domain Ownership: Pipeline
Table: pipeline_status
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.db.supabase_client import supabase
from app.domains.shared.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class PipelineRepository:
    """Supabase implementation of PipelineRepositoryProtocol."""

    TABLE = "pipeline_status"

    def initialize(self, intake_id: str, stages: tuple[str, ...]) -> list[dict[str, Any]]:
        """
        Insert all pipeline stages with status='pending'.
        Called once per intake during creation.
        """
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            {
                "intake_id": intake_id,
                "stage": stage,
                "status": "pending",
                "attempt_count": 0,
                "updated_at": now,
            }
            for stage in stages
        ]
        try:
            result = supabase.table(self.TABLE).insert(rows).execute()
            logger.info("[Pipeline] Initialized %d stages for intake %s", len(stages), intake_id)
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to initialize pipeline for intake {intake_id}: {exc}",
                table=self.TABLE, operation="initialize",
            ) from exc

    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]:
        """Fetch all pipeline stages for an intake."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("*")
                .eq("intake_id", intake_id)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch pipeline status for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_by_intake_id",
            ) from exc

    def get_stage(self, intake_id: str, stage: str) -> dict[str, Any] | None:
        """Fetch a single pipeline stage row for an intake. Returns None if not found."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("*")
                .eq("intake_id", intake_id)
                .eq("stage", stage)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch pipeline stage {stage} for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_stage",
            ) from exc

    def update_stage(self, intake_id: str, stage: str, updates: dict[str, Any]) -> None:
        """Update a specific pipeline stage for an intake."""
        try:
            supabase.table(self.TABLE).update(updates).eq(
                "intake_id", intake_id
            ).eq("stage", stage).execute()
        except Exception as exc:
            raise RepositoryError(
                f"Failed to update pipeline stage {stage} for intake {intake_id}: {exc}",
                table=self.TABLE, operation="update_stage",
            ) from exc

    def get_batch_status(self, intake_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch pipeline status for multiple intakes in a single query."""
        if not intake_ids:
            return []
        try:
            result = (
                supabase.table(self.TABLE)
                .select("intake_id, stage, status, started_at, completed_at, duration_ms, error_message")
                .in_("intake_id", intake_ids)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to batch fetch pipeline status: {exc}",
                table=self.TABLE, operation="get_batch_status",
            ) from exc

    def get_all(self, columns: str) -> list[dict[str, Any]]:
        """Fetch all pipeline status rows with specific columns."""
        try:
            result = supabase.table(self.TABLE).select(columns).execute()
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch all pipeline status: {exc}",
                table=self.TABLE, operation="get_all",
            ) from exc

    def get_completed_durations(self, stage: str) -> list[int]:
        """Fetch duration_ms values for a completed stage (non-null only)."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("duration_ms")
                .eq("stage", stage)
                .eq("status", "completed")
                .not_.is_("duration_ms", "null")
                .execute()
            )
            return [r["duration_ms"] for r in (result.data or []) if r.get("duration_ms")]
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch durations for stage {stage}: {exc}",
                table=self.TABLE, operation="get_completed_durations",
            ) from exc

    def count_by_status(self, status: str) -> int:
        """Count pipeline records with a given status."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("id", count="exact")
                .eq("status", status)
                .execute()
            )
            return result.count or 0
        except Exception as exc:
            raise RepositoryError(
                f"Failed to count pipeline status: {exc}",
                table=self.TABLE, operation="count_by_status",
            ) from exc


# Module-level singleton
pipeline_repository = PipelineRepository()
