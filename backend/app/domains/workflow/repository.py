"""
PRATHAM Workflow Repository — Data access for the workflow_logs table.

Domain Ownership: Workflow
Table: workflow_logs (append-only audit log — SSOT for patient status per ADR-001)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.db.supabase_client import supabase
from app.domains.shared.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class WorkflowRepository:
    """Supabase implementation of WorkflowRepositoryProtocol."""

    TABLE = "workflow_logs"

    def log_transition(
        self,
        intake_id: str,
        old_status: Optional[str],
        new_status: str,
        actor_type: str,
        actor_name: str,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Append a workflow transition event to the audit log.
        This is the primary write operation — all status changes go through here.
        """
        try:
            row = {
                "intake_id": intake_id,
                "old_status": old_status,
                "new_status": new_status,
                "actor_type": actor_type,
                "actor_name": actor_name,
                "reason": reason,
                "changed_at": datetime.now(timezone.utc).isoformat(),
            }
            result = supabase.table(self.TABLE).insert(row).execute()
            if not result.data:
                raise RepositoryError(
                    "Workflow log insert returned no data",
                    table=self.TABLE, operation="log_transition",
                )
            logger.info(
                "[Workflow] Logged transition %s -> %s for intake %s by %s",
                old_status, new_status, intake_id, actor_name,
            )
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(
                f"Failed to log workflow transition: {exc}",
                table=self.TABLE, operation="log_transition",
            ) from exc

    def get_latest_status(self, intake_id: str) -> Optional[str]:
        """
        Derive the current status from the latest workflow log entry.
        Returns None if no log entries exist for this intake.
        """
        try:
            result = (
                supabase.table(self.TABLE)
                .select("new_status")
                .eq("intake_id", intake_id)
                .order("changed_at", desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]["new_status"]
            return None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to get latest status for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_latest_status",
            ) from exc

    def get_logs(self, intake_id: str) -> list[dict[str, Any]]:
        """Fetch all workflow log entries for an intake, ordered chronologically."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("*")
                .eq("intake_id", intake_id)
                .order("changed_at", desc=False)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to get workflow logs for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_logs",
            ) from exc

    def get_batch_latest_status(self, intake_ids: list[str]) -> dict[str, str]:
        """
        Resolve current status for multiple intakes in a single query.
        Returns {intake_id: latest_status} for all provided IDs.
        """
        if not intake_ids:
            return {}
        try:
            result = (
                supabase.table(self.TABLE)
                .select("intake_id, new_status, changed_at")
                .in_("intake_id", intake_ids)
                .order("changed_at", desc=True)
                .execute()
            )
            # For each intake, pick the first (most recent) log entry
            status_map: dict[str, str] = {}
            for row in (result.data or []):
                iid = row["intake_id"]
                if iid not in status_map:
                    status_map[iid] = row["new_status"]
            return status_map
        except Exception as exc:
            raise RepositoryError(
                f"Failed to batch resolve workflow status: {exc}",
                table=self.TABLE, operation="get_batch_latest_status",
            ) from exc

    def get_logs_by_intake_ids(
        self, intake_ids: list[str], status_filter: str | None = None, columns: str = "*"
    ) -> list[dict[str, Any]]:
        """Batch-fetch workflow logs for multiple intakes, optionally filtered by new_status."""
        if not intake_ids:
            return []
        try:
            query = supabase.table(self.TABLE).select(columns).in_("intake_id", intake_ids)
            if status_filter:
                query = query.eq("new_status", status_filter)
            return query.execute().data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to batch fetch workflow logs: {exc}",
                table=self.TABLE, operation="get_logs_by_intake_ids",
            ) from exc


# Module-level singleton
workflow_repository = WorkflowRepository()
