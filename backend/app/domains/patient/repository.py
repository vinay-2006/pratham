"""
PRATHAM Patient Repository — Data access for the patients table.

Domain Ownership: Patient
Table: patients
Operations: create, get_by_id, search
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.db.supabase_client import supabase
from app.domains.shared.exceptions import PatientNotFoundError, RepositoryError

logger = logging.getLogger(__name__)


class PatientRepository:
    """Supabase implementation of PatientRepositoryProtocol."""

    TABLE = "patients"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a new patient record. Returns the created row."""
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if not result.data:
                raise RepositoryError(
                    "Patient insert returned no data",
                    table=self.TABLE, operation="create",
                )
            logger.info("[Patient] Created patient id=%s", result.data[0].get("id"))
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(
                f"Failed to create patient: {exc}",
                table=self.TABLE, operation="create",
            ) from exc

    def get_by_id(self, patient_id: str) -> Optional[dict[str, Any]]:
        """Fetch a single patient by ID. Returns None if not found."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("*")
                .eq("id", patient_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch patient {patient_id}: {exc}",
                table=self.TABLE, operation="get_by_id",
            ) from exc

    def search(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Search patients by name (case-insensitive partial match)."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("*")
                .or_(f"first_name.ilike.%{query}%,last_name.ilike.%{query}%")
                .limit(limit)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to search patients: {exc}",
                table=self.TABLE, operation="search",
            ) from exc


# Module-level singleton for convenience
patient_repository = PatientRepository()
