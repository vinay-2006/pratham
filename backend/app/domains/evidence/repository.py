"""
PRATHAM Evidence Repository — Data access for the evidence table + Supabase Storage.

Domain Ownership: Evidence
Table: evidence
Storage: Supabase Storage bucket
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.db.supabase_client import supabase
from app.domains.shared.exceptions import EvidenceNotFoundError, EvidenceUploadError, RepositoryError

logger = logging.getLogger(__name__)


class EvidenceRepository:
    """Supabase implementation of EvidenceRepositoryProtocol."""

    TABLE = "evidence"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert an evidence metadata record."""
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if not result.data:
                raise RepositoryError(
                    "Evidence insert returned no data",
                    table=self.TABLE, operation="create",
                )
            logger.info("[Evidence] Created evidence id=%s", result.data[0].get("id"))
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(
                f"Failed to create evidence: {exc}",
                table=self.TABLE, operation="create",
            ) from exc

    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]:
        """Fetch all evidence records for an intake."""
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
                f"Failed to fetch evidence for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_by_intake_id",
            ) from exc

    def get_by_id(self, evidence_id: str) -> Optional[dict[str, Any]]:
        """Fetch a single evidence record by ID."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("*")
                .eq("id", evidence_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch evidence {evidence_id}: {exc}",
                table=self.TABLE, operation="get_by_id",
            ) from exc

    def create_with_fallback(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Insert an evidence row with investigation_id fallback.

        If the insert fails because the investigation_id column doesn't
        exist yet (PGRST204), retries without that field.
        Raises on all other errors.
        """
        try:
            result = supabase.table(self.TABLE).insert(payload).execute()
            if result.data:
                return result.data[0]
            raise RepositoryError(
                "Evidence insert returned empty data",
                table=self.TABLE, operation="create_with_fallback",
            )
        except RepositoryError:
            raise
        except Exception as e:
            err_str = str(e)
            # Column doesn't exist yet — retry without it
            if "investigation_id" in err_str and (
                "PGRST204" in err_str or "column" in err_str.lower()
            ):
                payload_fallback = {k: v for k, v in payload.items() if k != "investigation_id"}
                try:
                    result = supabase.table(self.TABLE).insert(payload_fallback).execute()
                    if result.data:
                        return result.data[0]
                    raise RepositoryError(
                        "Evidence insert (fallback) returned empty data",
                        table=self.TABLE, operation="create_with_fallback",
                    )
                except RepositoryError:
                    raise
                except Exception as fb_exc:
                    raise RepositoryError(
                        f"Evidence insert fallback failed: {fb_exc}",
                        table=self.TABLE, operation="create_with_fallback",
                    ) from fb_exc
            raise RepositoryError(
                f"Failed to create evidence: {e}",
                table=self.TABLE, operation="create_with_fallback",
            ) from e

    def get_by_intake_id_and_type(
        self, intake_id: str, evidence_type: str
    ) -> list[dict[str, Any]]:
        """Fetch all evidence IDs for an intake with a given evidence_type."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("id")
                .eq("intake_id", intake_id)
                .eq("evidence_type", evidence_type)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch evidence by type for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_by_intake_id_and_type",
            ) from exc

    def delete(self, evidence_id: str) -> None:
        """Delete an evidence record."""
        try:
            supabase.table(self.TABLE).delete().eq("id", evidence_id).execute()
            logger.info("[Evidence] Deleted evidence id=%s", evidence_id)
        except Exception as exc:
            raise RepositoryError(
                f"Failed to delete evidence {evidence_id}: {exc}",
                table=self.TABLE, operation="delete",
            ) from exc

    def count_by_intake_id(self, intake_id: str) -> int:
        """Count evidence records for an intake."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("id", count="exact")
                .eq("intake_id", intake_id)
                .execute()
            )
            return result.count if result.count is not None else len(result.data or [])
        except Exception as exc:
            raise RepositoryError(
                f"Failed to count evidence for intake {intake_id}: {exc}",
                table=self.TABLE, operation="count_by_intake_id",
            ) from exc

    def get_by_intake_id_with_columns(
        self, intake_id: str, columns: str, order_by: str = "uploaded_at", desc: bool = True
    ) -> list[dict[str, Any]]:
        """Fetch evidence for an intake with specific columns."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("intake_id", intake_id)
                .order(order_by, desc=desc)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch evidence for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_by_intake_id_with_columns",
            ) from exc

    def get_by_id_with_columns(self, evidence_id: str, columns: str) -> Optional[dict[str, Any]]:
        """Fetch a single evidence record by ID with specific columns."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("id", evidence_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch evidence {evidence_id}: {exc}",
                table=self.TABLE, operation="get_by_id_with_columns",
            ) from exc

    def get_by_intake_ids(
        self, intake_ids: list[str], columns: str = "*"
    ) -> list[dict[str, Any]]:
        """Batch-fetch evidence for multiple intakes."""
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
                f"Failed to batch fetch evidence: {exc}",
                table=self.TABLE, operation="get_by_intake_ids",
            ) from exc


# Module-level singleton
evidence_repository = EvidenceRepository()
