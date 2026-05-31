"""
Aggregation Service — Stub for unified clinical evidence aggregation.

TODO: Query Supabase for patient data and merge across evidence types.
"""

from __future__ import annotations

import uuid


class AggregationService:
    """Aggregates evidence from all sources into a unified clinical report."""

    async def build_report(
        self,
        patient_id: uuid.UUID,
        include_imaging: bool = True,
        include_labs: bool = True,
        include_vitals_summary: bool = True,
    ) -> dict[str, object]:
        """
        Stub: Build a unified evidence report for a patient.

        Args:
            patient_id: UUID of the patient.
            include_imaging: Whether to include imaging results.
            include_labs: Whether to include lab results.
            include_vitals_summary: Whether to include vitals trend.

        Returns:
            Dictionary representing the aggregated evidence report.
        """
        # TODO: Fetch from Supabase and merge imaging, labs, vitals
        return {
            "patient_id": str(patient_id),
            "summary": "Stub: Aggregation not yet implemented.",
            "overall_severity": "unknown",
            "key_findings": [],
            "recommended_actions": [],
        }
