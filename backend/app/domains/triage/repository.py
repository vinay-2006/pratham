"""
PRATHAM Triage Repository — Data access for patients, emergency_intake, vitals,
symptoms, and preparation_alerts tables.

Domain Ownership: Triage
Tables: patients, emergency_intake, vitals, symptoms, preparation_alerts
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.db.supabase_client import supabase
from app.domains.shared.exceptions import IntakeNotFoundError, RepositoryError

logger = logging.getLogger(__name__)


class IntakeRepository:
    """Supabase implementation of IntakeRepositoryProtocol."""

    TABLE = "emergency_intake"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a new intake record. Returns the created row."""
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if not result.data:
                raise RepositoryError(
                    "Intake insert returned no data",
                    table=self.TABLE, operation="create",
                )
            logger.info("[Triage] Created intake id=%s", result.data[0].get("id"))
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(
                f"Failed to create intake: {exc}",
                table=self.TABLE, operation="create",
            ) from exc

    def get_by_id(self, intake_id: str, columns: str = "*") -> Optional[dict[str, Any]]:
        """Fetch a single intake by ID with specified columns. Returns None if not found."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("id", intake_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_by_id",
            ) from exc

    def update_status(self, intake_id: str, status: str) -> None:
        """Update the status projection column on emergency_intake."""
        try:
            supabase.table(self.TABLE).update(
                {"status": status}
            ).eq("id", intake_id).execute()
            logger.info("[Triage] Updated intake %s status to %s", intake_id, status)
        except Exception as exc:
            raise RepositoryError(
                f"Failed to update intake status: {exc}",
                table=self.TABLE, operation="update_status",
            ) from exc

    def update_severity(self, intake_id: str, severity_level: str) -> None:
        """Update the severity_level column on emergency_intake."""
        try:
            supabase.table(self.TABLE).update(
                {"severity_level": severity_level}
            ).eq("id", intake_id).execute()
            logger.info("[Triage] Updated intake %s severity to %s", intake_id, severity_level)
        except Exception as exc:
            raise RepositoryError(
                f"Failed to update intake severity: {exc}",
                table=self.TABLE, operation="update_severity",
            ) from exc

    def get_active_intakes(self) -> list[dict[str, Any]]:
        """Fetch all intakes with non-terminal status."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("*, patients(*)")
                .not_.in_("status", ["case_closed", "offline_care"])
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch active intakes: {exc}",
                table=self.TABLE, operation="get_active_intakes",
            ) from exc

    def get_by_patient_id(
        self, patient_id: str, columns: str = "*", order_asc: bool = False
    ) -> list[dict[str, Any]]:
        """Fetch all intakes for a given patient."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("patient_id", patient_id)
                .order("created_at", asc=order_asc)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch intakes for patient {patient_id}: {exc}",
                table=self.TABLE, operation="get_by_patient_id",
            ) from exc

    def count_all(self) -> int:
        """Return total number of intakes."""
        try:
            result = supabase.table(self.TABLE).select("id", count="exact").execute()
            return result.count or len(result.data or [])
        except Exception as exc:
            raise RepositoryError(
                f"Failed to count intakes: {exc}",
                table=self.TABLE, operation="count_all",
            ) from exc

    def list_recent(self, columns: str, limit: int = 20) -> list[dict[str, Any]]:
        """Fetch most recent intakes with specified columns."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to list recent intakes: {exc}",
                table=self.TABLE, operation="list_recent",
            ) from exc

    def list_with_status_filter(
        self, columns: str, status: Optional[str] = None, limit: int = 500
    ) -> list[dict[str, Any]]:
        """Fetch intakes with specified columns, optional status filter, ordered newest-first."""
        try:
            query = supabase.table(self.TABLE).select(columns)
            if status:
                query = query.eq("status", status)
            query = query.order("created_at", desc=True)
            if limit:
                query = query.limit(limit)
            return query.execute().data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to list intakes: {exc}",
                table=self.TABLE, operation="list_with_status_filter",
            ) from exc

    def list_all(self, columns: str, limit: int = 500) -> list[dict[str, Any]]:
        """Fetch all intakes with specified columns (no ordering constraint)."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to list all intakes: {exc}",
                table=self.TABLE, operation="list_all",
            ) from exc

    def search(self, filter_expr: str, columns: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search intakes with an or_ filter expression."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .or_(filter_expr)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to search intakes: {exc}",
                table=self.TABLE, operation="search",
            ) from exc

    def delete(self, intake_id: str) -> None:
        """Delete an intake record (used in compensating rollback)."""
        try:
            supabase.table(self.TABLE).delete().eq("id", intake_id).execute()
            logger.info("[Triage] Deleted intake %s", intake_id)
        except Exception as exc:
            raise RepositoryError(
                f"Failed to delete intake {intake_id}: {exc}",
                table=self.TABLE, operation="delete",
            ) from exc


class VitalsRepository:
    """Supabase implementation of VitalsRepositoryProtocol."""

    TABLE = "vitals"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a vitals record."""
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if not result.data:
                raise RepositoryError(
                    "Vitals insert returned no data",
                    table=self.TABLE, operation="create",
                )
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(
                f"Failed to create vitals: {exc}",
                table=self.TABLE, operation="create",
            ) from exc

    def delete_by_intake_id(self, intake_id: str) -> None:
        """Delete vitals for a given intake (used in compensating rollback)."""
        try:
            supabase.table(self.TABLE).delete().eq("intake_id", intake_id).execute()
            logger.info("[Triage] Deleted vitals for intake %s", intake_id)
        except Exception as exc:
            raise RepositoryError(
                f"Failed to delete vitals for intake {intake_id}: {exc}",
                table=self.TABLE, operation="delete_by_intake_id",
            ) from exc

    def get_by_intake_id(self, intake_id: str) -> Optional[dict[str, Any]]:
        """Fetch vitals for a given intake."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("*")
                .eq("intake_id", intake_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch vitals for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_by_intake_id",
            ) from exc


class SymptomsRepository:
    """Supabase implementation of SymptomsRepositoryProtocol."""

    TABLE = "symptoms"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a symptoms record."""
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if not result.data:
                raise RepositoryError(
                    "Symptoms insert returned no data",
                    table=self.TABLE, operation="create",
                )
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(
                f"Failed to create symptoms: {exc}",
                table=self.TABLE, operation="create",
            ) from exc

    def delete_by_intake_id(self, intake_id: str) -> None:
        """Delete symptoms for a given intake (used in compensating rollback)."""
        try:
            supabase.table(self.TABLE).delete().eq("intake_id", intake_id).execute()
            logger.info("[Triage] Deleted symptoms for intake %s", intake_id)
        except Exception as exc:
            raise RepositoryError(
                f"Failed to delete symptoms for intake {intake_id}: {exc}",
                table=self.TABLE, operation="delete_by_intake_id",
            ) from exc

    def get_by_intake_id(self, intake_id: str) -> Optional[dict[str, Any]]:
        """Fetch symptoms for a given intake."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select("*")
                .eq("intake_id", intake_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch symptoms for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_by_intake_id",
            ) from exc


class PatientsRepository:
    """Data access for the patients table (Triage domain ownership)."""

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
            logger.info("[Triage] Created patient id=%s", result.data[0].get("id"))
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(
                f"Failed to create patient: {exc}",
                table=self.TABLE, operation="create",
            ) from exc

    def get_by_id(self, patient_id: str, columns: str = "*") -> Optional[dict[str, Any]]:
        """Fetch a single patient by ID. Returns None if not found."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
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

    def delete(self, patient_id: str) -> None:
        """Delete a patient record (used in compensating rollback)."""
        try:
            supabase.table(self.TABLE).delete().eq("id", patient_id).execute()
            logger.info("[Triage] Deleted patient %s", patient_id)
        except Exception as exc:
            raise RepositoryError(
                f"Failed to delete patient {patient_id}: {exc}",
                table=self.TABLE, operation="delete",
            ) from exc

    def health_check(self) -> bool:
        """Test database connectivity by selecting a single patient ID."""
        try:
            supabase.table(self.TABLE).select("id").limit(1).execute()
            return True
        except Exception:
            return False


class PreparationAlertsRepository:
    """Data access for the preparation_alerts table."""

    TABLE = "preparation_alerts"

    def create_alert(self, intake_id: str, alert_type: str, status: str = "pending") -> None:
        """Insert a preparation alert record."""
        try:
            supabase.table(self.TABLE).insert({
                "intake_id": intake_id,
                "alert_type": alert_type,
                "status": status,
            }).execute()
            logger.info("[Triage] Created preparation alert type=%s for intake %s", alert_type, intake_id)
        except Exception as exc:
            raise RepositoryError(
                f"Failed to create preparation alert: {exc}",
                table=self.TABLE, operation="create_alert",
            ) from exc

    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]:
        """Fetch all preparation alerts for a given intake."""
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
                f"Failed to fetch preparation alerts for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_by_intake_id",
            ) from exc


# Module-level singletons
intake_repository = IntakeRepository()
vitals_repository = VitalsRepository()
symptoms_repository = SymptomsRepository()
patients_repository = PatientsRepository()
preparation_alerts_repository = PreparationAlertsRepository()
