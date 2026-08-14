"""
PRATHAM Notification Repository — Data access for the preparation_alerts table.

Domain Ownership: Notification
Table: preparation_alerts
"""

from __future__ import annotations

import logging
from typing import Any

from app.db.supabase_client import supabase
from app.domains.shared.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class AlertsRepository:
    """Supabase implementation of AlertsRepositoryProtocol."""

    TABLE = "preparation_alerts"

    def create_batch(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Insert multiple preparation alerts."""
        if not records:
            return []
        try:
            result = supabase.table(self.TABLE).insert(records).execute()
            logger.info("[Notification] Created %d alerts", len(result.data or []))
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to create alerts: {exc}",
                table=self.TABLE, operation="create_batch",
            ) from exc

    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]:
        """Fetch all alerts for an intake."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("*")
                .eq("intake_id", intake_id)
                .order("created_at", desc=False)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch alerts for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_by_intake_id",
            ) from exc


# Module-level singleton
alerts_repository = AlertsRepository()
