"""
Risk Service — Stub for patient risk scoring.

TODO: Load and run PyTorch/scikit-learn risk model from ml_models/.
"""

from __future__ import annotations


class RiskService:
    """Computes composite patient risk scores."""

    async def compute_risk_score(
        self,
        vitals: dict[str, float | int],
        age: int,
        comorbidities: list[str],
        symptoms: list[str],
    ) -> tuple[float, str]:
        """
        Stub: Compute a 0–100 risk score and category.

        Args:
            vitals: Dictionary of vital sign measurements.
            age: Patient age in years.
            comorbidities: List of known comorbidities.
            symptoms: List of extracted symptom terms.

        Returns:
            Tuple of (risk_score, risk_category_string).
        """
        # TODO: Load model from ml_models/risk_model.pt and run inference
        return 0.0, "unknown"
