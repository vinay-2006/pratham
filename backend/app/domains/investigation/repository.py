"""
PRATHAM Investigation Repository — Data access for investigation_recommendations table.

Domain Ownership: Investigation
Table: investigation_recommendations
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.db.supabase_client import supabase
from app.domains.shared.exceptions import InvestigationNotFoundError, RepositoryError

logger = logging.getLogger(__name__)


class InvestigationRepository:
    """Supabase implementation of InvestigationRepositoryProtocol."""

    TABLE = "investigation_recommendations"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a single investigation recommendation."""
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if not result.data:
                raise RepositoryError(
                    "Investigation insert returned no data",
                    table=self.TABLE, operation="create",
                )
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(
                f"Failed to create investigation: {exc}",
                table=self.TABLE, operation="create",
            ) from exc

    def create_batch(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Insert multiple investigation recommendations in a single call."""
        if not records:
            return []
        try:
            result = supabase.table(self.TABLE).insert(records).execute()
            logger.info("[Investigation] Created %d recommendations", len(result.data or []))
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to batch create investigations: {exc}",
                table=self.TABLE, operation="create_batch",
            ) from exc

    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]:
        """Fetch all investigation recommendations for an intake."""
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
                f"Failed to fetch investigations for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_by_intake_id",
            ) from exc

    def update_status(self, recommendation_id: str, updates: dict[str, Any]) -> None:
        """Update a single investigation recommendation."""
        try:
            supabase.table(self.TABLE).update(updates).eq("id", recommendation_id).execute()
        except Exception as exc:
            raise RepositoryError(
                f"Failed to update investigation {recommendation_id}: {exc}",
                table=self.TABLE, operation="update_status",
            ) from exc

    def update_batch_by_intake(
        self,
        intake_id: str,
        updates: dict[str, Any],
        status_filter: Optional[str] = None,
    ) -> None:
        """
        Update all investigation recommendations for an intake,
        optionally filtered by current status.
        """
        try:
            query = supabase.table(self.TABLE).update(updates).eq("intake_id", intake_id)
            if status_filter:
                query = query.eq("status", status_filter)
            query.execute()
            logger.info(
                "[Investigation] Batch updated intake %s (filter=%s)",
                intake_id, status_filter,
            )
        except Exception as exc:
            raise RepositoryError(
                f"Failed to batch update investigations: {exc}",
                table=self.TABLE, operation="update_batch_by_intake",
            ) from exc

    def count_by_intake_and_status(self, intake_id: str, status: str) -> int:
        """Count investigations for an intake with a given status."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("id", count="exact")
                .eq("intake_id", intake_id)
                .eq("status", status)
                .execute()
            )
            return result.count if result.count is not None else len(result.data or [])
        except Exception as exc:
            raise RepositoryError(
                f"Failed to count investigations: {exc}",
                table=self.TABLE, operation="count_by_intake_and_status",
            ) from exc

    def get_by_intake_id_with_columns(
        self, intake_id: str, columns: str
    ) -> list[dict[str, Any]]:
        """Fetch investigations for an intake with specific columns."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("intake_id", intake_id)
                .order("created_at")
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch investigations for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_by_intake_id_with_columns",
            ) from exc
    def get_by_intake_ids(
        self, intake_ids: list[str], columns: str = "*"
    ) -> list[dict[str, Any]]:
        """Batch-fetch investigations for multiple intakes."""
        if not intake_ids:
            return []
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .in_("intake_id", intake_ids)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to batch fetch investigations: {exc}",
                table=self.TABLE, operation="get_by_intake_ids",
            ) from exc

    def get_by_intake_ids_with_status(
        self, intake_ids: list[str], status: str, columns: str = "*"
    ) -> list[dict[str, Any]]:
        """Batch-fetch investigations for multiple intakes filtered by status."""
        if not intake_ids:
            return []
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .in_("intake_id", intake_ids)
                .eq("status", status)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to batch fetch investigations by status: {exc}",
                table=self.TABLE, operation="get_by_intake_ids_with_status",
            ) from exc

    def get_by_status(self, status: str, columns: str = "*") -> list[dict[str, Any]]:
        """Fetch all investigations with a given status."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("status", status)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch investigations by status: {exc}",
                table=self.TABLE, operation="get_by_status",
            ) from exc

    def get_by_intake_and_type(
        self, intake_id: str, investigation_type: str, columns: str = "id, status"
    ) -> list[dict[str, Any]]:
        """Fetch investigations for an intake filtered by investigation_type."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("intake_id", intake_id)
                .eq("investigation_type", investigation_type)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch investigations by type: {exc}",
                table=self.TABLE, operation="get_by_intake_and_type",
            ) from exc

    def update_by_intake_and_type(
        self, intake_id: str, investigation_type: str, updates: dict[str, Any]
    ) -> None:
        """Update investigations matching intake_id + investigation_type."""
        try:
            (
                supabase.table(self.TABLE)
                .update(updates)
                .eq("intake_id", intake_id)
                .eq("investigation_type", investigation_type)
                .execute()
            )
        except Exception as exc:
            raise RepositoryError(
                f"Failed to update investigation by type: {exc}",
                table=self.TABLE, operation="update_by_intake_and_type",
            ) from exc


# Module-level singleton
investigation_repository = InvestigationRepository()
