"""
PRATHAM AI Repository — Data access for all AI result tables.

Domain Ownership: AI
Tables: nlp_extractions, risk_scores, lab_results, imaging_results, aggregation_results
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from app.db.supabase_client import supabase
from app.domains.shared.exceptions import RepositoryError

logger = logging.getLogger(__name__)


class NLPRepository:
    """Data access for the nlp_extractions table."""

    TABLE = "nlp_extractions"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert NLP extraction results."""
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if not result.data:
                raise RepositoryError("NLP insert returned no data", table=self.TABLE, operation="create")
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to create NLP extraction: {exc}", table=self.TABLE, operation="create") from exc

    def get_by_intake_id(self, intake_id: str) -> Optional[dict[str, Any]]:
        """Fetch NLP extraction for an intake."""
        try:
            result = supabase.table(self.TABLE).select("*").eq("intake_id", intake_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch NLP for intake {intake_id}: {exc}", table=self.TABLE, operation="get_by_intake_id") from exc

    def get_latest(self, intake_id: str, columns: str) -> Optional[dict[str, Any]]:
        """Fetch latest NLP extraction for an intake with specific columns."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("intake_id", intake_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch NLP for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_latest",
            ) from exc


class RiskScoresRepository:
    """Data access for the risk_scores table."""

    TABLE = "risk_scores"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert risk score results."""
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if not result.data:
                raise RepositoryError("Risk scores insert returned no data", table=self.TABLE, operation="create")
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to create risk scores: {exc}", table=self.TABLE, operation="create") from exc

    def get_by_intake_id(self, intake_id: str) -> Optional[dict[str, Any]]:
        """Fetch risk scores for an intake."""
        try:
            result = supabase.table(self.TABLE).select("*").eq("intake_id", intake_id).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch risk scores for intake {intake_id}: {exc}", table=self.TABLE, operation="get_by_intake_id") from exc

    def get_latest(self, intake_id: str, columns: str) -> Optional[dict[str, Any]]:
        """Fetch latest risk scores for an intake with specific columns."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("intake_id", intake_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch risk scores for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_latest",
            ) from exc


class LabResultsRepository:
    """Data access for the lab_results table."""

    TABLE = "lab_results"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert lab analysis results."""
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if not result.data:
                raise RepositoryError("Lab results insert returned no data", table=self.TABLE, operation="create")
            logger.info("[AI] Created lab result for intake %s", data.get("intake_id"))
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to create lab result: {exc}", table=self.TABLE, operation="create") from exc

    def insert_safe(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Insert lab results, returning empty dict on failure (non-fatal).

        Used by endpoints where the prediction should still be returned
        even if the DB write fails.
        """
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if result.data:
                logger.info("[AI] Created lab result for intake %s", data.get("intake_id"))
                return result.data[0]
            return {}
        except Exception as exc:
            logger.error("[AI] lab_results insert failed (non-fatal): %s", exc)
            return {}

    def get_all_for_intake(self, intake_id: str, columns: str) -> list[dict[str, Any]]:
        """Fetch all lab results for an intake with specific columns, newest first."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("intake_id", intake_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch lab results for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_all_for_intake",
            ) from exc

    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]:
        """Fetch all lab results for an intake (may have multiple analyses)."""
        try:
            result = supabase.table(self.TABLE).select("*").eq("intake_id", intake_id).order("created_at", desc=True).execute()
            return result.data or []
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch lab results for intake {intake_id}: {exc}", table=self.TABLE, operation="get_by_intake_id") from exc

    def get_latest(self, intake_id: str, columns: str = "*") -> Optional[dict[str, Any]]:
        """Fetch the latest lab result for an intake with specific columns."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("intake_id", intake_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch lab result for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_latest",
            ) from exc

    def delete_by_intake_id(self, intake_id: str) -> None:
        """Delete all lab results for an intake."""
        try:
            supabase.table(self.TABLE).delete().eq("intake_id", intake_id).execute()
            logger.info("[AI] Deleted lab results for intake %s", intake_id)
        except Exception as exc:
            raise RepositoryError(
                f"Failed to delete lab results for intake {intake_id}: {exc}",
                table=self.TABLE, operation="delete_by_intake_id",
            ) from exc


class ImagingResultsRepository:
    """Data access for the imaging_results table."""

    TABLE = "imaging_results"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert imaging analysis results."""
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if not result.data:
                raise RepositoryError("Imaging results insert returned no data", table=self.TABLE, operation="create")
            logger.info("[AI] Created imaging result for intake %s", data.get("intake_id"))
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to create imaging result: {exc}", table=self.TABLE, operation="create") from exc

    def insert_safe(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Insert imaging results, returning empty dict on failure (non-fatal).

        Used by endpoints where the prediction should still be returned
        even if the DB write fails.
        """
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if result.data:
                logger.info("[AI] Created imaging result for intake %s", data.get("intake_id"))
                return result.data[0]
            return {}
        except Exception as exc:
            logger.error("[AI] imaging_results insert failed (non-fatal): %s", exc)
            return {}

    def get_latest(self, intake_id: str, columns: str) -> Optional[dict[str, Any]]:
        """Fetch the latest imaging result for an intake with specific columns."""
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("intake_id", intake_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch imaging result for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_latest",
            ) from exc

    def get_by_intake_id(self, intake_id: str) -> list[dict[str, Any]]:
        """Fetch all imaging results for an intake."""
        try:
            result = supabase.table(self.TABLE).select("*").eq("intake_id", intake_id).order("created_at", desc=True).execute()
            return result.data or []
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch imaging results for intake {intake_id}: {exc}", table=self.TABLE, operation="get_by_intake_id") from exc

    def delete_by_intake_id(self, intake_id: str) -> None:
        """Delete all imaging results for an intake."""
        try:
            supabase.table(self.TABLE).delete().eq("intake_id", intake_id).execute()
            logger.info("[AI] Deleted imaging results for intake %s", intake_id)
        except Exception as exc:
            raise RepositoryError(
                f"Failed to delete imaging results for intake {intake_id}: {exc}",
                table=self.TABLE, operation="delete_by_intake_id",
            ) from exc


class AggregationResultsRepository:
    """Data access for the aggregation_results table."""

    TABLE = "aggregation_results"

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert aggregation results."""
        try:
            result = supabase.table(self.TABLE).insert(data).execute()
            if not result.data:
                raise RepositoryError("Aggregation insert returned no data", table=self.TABLE, operation="create")
            logger.info("[AI] Created aggregation result for intake %s", data.get("intake_id"))
            return result.data[0]
        except RepositoryError:
            raise
        except Exception as exc:
            raise RepositoryError(f"Failed to create aggregation result: {exc}", table=self.TABLE, operation="create") from exc

    def insert_with_fallback(
        self, db_row: dict[str, Any], fallback_exclude_keys: set[str]
    ) -> dict[str, Any]:
        """
        Insert aggregation results with legacy schema fallback.

        Attempts a full insert first. If it fails due to missing columns
        (migration 006 not applied), retries with the fallback_exclude_keys
        columns removed.

        Returns the inserted row dict, or empty dict if both attempts fail.
        """
        try:
            result = supabase.table(self.TABLE).insert(db_row).execute()
            if result.data:
                logger.info("[AI] Created aggregation result for intake %s", db_row.get("intake_id"))
                return result.data[0]
            return {}
        except Exception as exc:
            err_str = str(exc)
            col_missing = (
                any(c in err_str for c in fallback_exclude_keys)
                or "PGRST204" in err_str
                or "column" in err_str.lower()
            )
            if col_missing:
                logger.warning(
                    "[AI] New columns missing — falling back to legacy schema. "
                    "Run migrations/006_aggregation_results_schema.sql in Supabase."
                )
                legacy_row = {k: v for k, v in db_row.items() if k not in fallback_exclude_keys}
                try:
                    fallback_res = supabase.table(self.TABLE).insert(legacy_row).execute()
                    if fallback_res.data:
                        logger.info("[AI] Legacy persist ok: id=%s", fallback_res.data[0].get("id"))
                        return fallback_res.data[0]
                    return {}
                except Exception as fb_exc:
                    logger.error("[AI] Legacy persist also failed (non-fatal): %s", fb_exc)
                    return {}
            else:
                logger.error("[AI] aggregation_results insert failed (non-fatal): %s", exc)
                return {}

    def get_latest(self, intake_id: str, columns: str) -> Optional[dict[str, Any]]:
        """
        Fetch the latest aggregation result for an intake with specific columns.

        Returns the row dict or None if not found.
        Raises RepositoryError on database errors.
        """
        try:
            result = (
                supabase.table(self.TABLE)
                .select(columns)
                .eq("intake_id", intake_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch aggregation for intake {intake_id}: {exc}",
                table=self.TABLE, operation="get_latest",
            ) from exc

    def get_by_intake_id(self, intake_id: str) -> Optional[dict[str, Any]]:
        """Fetch the latest aggregation result for an intake."""
        try:
            result = supabase.table(self.TABLE).select("*").eq("intake_id", intake_id).order("created_at", desc=True).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as exc:
            raise RepositoryError(f"Failed to fetch aggregation for intake {intake_id}: {exc}", table=self.TABLE, operation="get_by_intake_id") from exc

    def delete_by_intake_id(self, intake_id: str) -> None:
        """Delete all aggregation results for an intake."""
        try:
            supabase.table(self.TABLE).delete().eq("intake_id", intake_id).execute()
            logger.info("[AI] Deleted aggregation results for intake %s", intake_id)
        except Exception as exc:
            raise RepositoryError(
                f"Failed to delete aggregation results for intake {intake_id}: {exc}",
                table=self.TABLE, operation="delete_by_intake_id",
            ) from exc


# Module-level singletons
nlp_repository = NLPRepository()
risk_scores_repository = RiskScoresRepository()
lab_results_repository = LabResultsRepository()
imaging_results_repository = ImagingResultsRepository()
aggregation_results_repository = AggregationResultsRepository()
