"""
LabAnalysisService — Business logic for XGBoost cardiac risk inference.

Domain: Lab Analysis
Responsibility: Feature vector construction, inference orchestration, SHAP ranking.

REPOSITORY RULES — this service:
  ✓ Contains calculations (max_hr estimation, feature vector assembly)
  ✓ Contains orchestration (build → infer → rank SHAP → persist)
  ✓ Contains business rules (Tanaka formula, population-median fallbacks)

  ✗ Does NOT contain API routing or HTTP concerns
  ✗ Does NOT contain DTO transformation
  ✗ Does NOT contain repository definitions
  ✗ Does NOT contain workflow decisions
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.domains.ai.repository import lab_results_repository
from app.domains.triage.repository import intake_repository, vitals_repository
from app.ml.lab_model import run_inference
from app.utils.patient_utils import compute_age as _compute_age_base

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal calculations
# ---------------------------------------------------------------------------

def compute_age(dob: str | None) -> int:
    """
    Lab-analysis variant: wraps patient_utils.compute_age but uses 50
    (population median from UCI Heart Disease dataset) instead of 0
    as the fallback when dob is absent or unparseable.
    This preserves the original api/lab_analysis.py _compute_age behaviour.
    """
    raw = _compute_age_base(dob)
    return raw if raw > 0 else 50


def top_n_features(shap_dict: dict[str, float], n: int = 5) -> dict[str, float]:
    """
    Return the N features with the largest absolute SHAP contribution.
    Used for clinical explainability display in the response.
    """
    if not shap_dict:
        return {}
    sorted_items = sorted(shap_dict.items(), key=lambda kv: abs(kv[1]), reverse=True)
    return {k: round(v, 6) for k, v in sorted_items[:n]}


def resolve_max_hr(override_max_hr: Optional[float], heart_rate_from_vitals: Optional[float]) -> float:
    """
    Resolve maximum heart rate (UCI Heart Disease dataset feature).

    Priority order (matches original api/lab_analysis.py behaviour):
      1. Clinician-provided override (most accurate)
      2. vitals.heart_rate from intake — used as proxy when max_hr not supplied
         (NOTE: this is a resting HR proxy; it was the original fallback)

    This is business logic — it encodes the clinical fallback strategy.
    """
    if override_max_hr is not None:
        return float(override_max_hr)
    if heart_rate_from_vitals is not None:
        return float(heart_rate_from_vitals)
    logger.warning(
        "[LabAnalysisService] max_hr and heart_rate_from_vitals both unavailable — using 100 bpm default"
    )
    return 100.0


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------

def fetch_patient_base_data(intake_id: str) -> dict[str, Any]:
    """
    Pull demographics + vitals from the database for the given intake.
    Returns a flat dict keyed to model input field names.

    Raises ValueError when intake is not found (caller converts to HTTPException).
    """
    intake = intake_repository.get_by_id(
        intake_id,
        columns=(
            "id, status, severity_level, "
            "patients(first_name, last_name, gender, date_of_birth)"
        ),
    )
    if not intake:
        raise ValueError(f"Intake {intake_id!r} not found.")

    patient_row = intake.get("patients") or {}
    vitals = vitals_repository.get_by_intake_id(intake_id) or {}

    gender = (patient_row.get("gender") or "").lower()
    sex = "M" if gender == "male" else "F"
    age = compute_age(patient_row.get("date_of_birth"))
    resting_bp = vitals.get("bp_systolic") or 120
    # heart_rate is used as a proxy for max_hr when no override is supplied
    # (matches original api/lab_analysis.py _fetch_patient_data behaviour)
    heart_rate_from_vitals = vitals.get("heart_rate") or 100

    return {
        "age": age,
        "sex": sex,
        "resting_bp": resting_bp,
        "heart_rate_from_vitals": heart_rate_from_vitals,
    }


def build_patient_input(db_data: dict[str, Any], override: Any) -> dict[str, Any]:
    """
    Assemble the 15-feature patient input vector from database data and clinical overrides.

    Matches original api/lab_analysis.py build logic exactly:
      max_hr = override.max_hr  if supplied
             else vitals.heart_rate (resting HR proxy, original fallback)
    """
    max_hr = resolve_max_hr(override.max_hr, db_data.get("heart_rate_from_vitals"))
    return {
        "age":             db_data["age"],
        "sex":             db_data["sex"],
        "resting_bp":      db_data["resting_bp"],
        "chest_pain_type": override.chest_pain_type or "ASY",
        "cholesterol":     override.cholesterol or 0,
        "fasting_bs":      override.fasting_bs or 0,
        "resting_ecg":     override.resting_ecg or "Normal",
        "max_hr":          max_hr,
        "exercise_angina": override.exercise_angina or "N",
        "oldpeak":         override.oldpeak or 0.0,
        "st_slope":        override.st_slope or "Flat",
    }


# ---------------------------------------------------------------------------
# Inference orchestration
# ---------------------------------------------------------------------------

def run_lab_analysis(intake_id: str, override: Any) -> dict[str, Any]:
    """
    Full lab analysis orchestration:
      1. Fetch patient base data from repositories
      2. Build 15-feature patient input vector
      3. Run XGBoost inference + SHAP
      4. Persist result to lab_results table
      5. Return structured result dict

    Raises:
      ValueError  — intake not found (404-worthy)
      RuntimeError — ML model unavailable (503-worthy)
      Exception   — any other DB or inference failure (500-worthy)

    The API layer is responsible for translating these into HTTP responses.
    """
    # 1. Fetch base data
    db_data = fetch_patient_base_data(intake_id)

    # 2. Build patient input vector
    patient_input = build_patient_input(db_data, override)

    # 3. Run inference (XGBoost + SHAP)
    result = run_inference(patient_input)

    risk_probability = result["risk_probability"]
    prediction       = result["prediction"]
    shap_values      = result["shap_values"]
    input_features   = result["input_features"]

    # 4. Rank SHAP features for clinical display
    top_features = top_n_features(shap_values, n=5)

    # 5. Persist to lab_results
    now = datetime.now(timezone.utc).isoformat()
    db_row = {
        "intake_id":        intake_id,
        "model_name":       "task9_xgboost_heart_model",
        "prediction":       prediction,
        "risk_probability": risk_probability,
        "shap_values":      shap_values,
        "input_features":   input_features,
        "created_at":       now,
    }

    lab_result_id = ""
    inserted = lab_results_repository.insert_safe(db_row)
    if inserted:
        lab_result_id = inserted.get("id", "")
        logger.info(
            "[LabAnalysisService] lab_results persisted: id=%s intake=%s prediction=%s prob=%.4f",
            lab_result_id, intake_id, prediction, risk_probability,
        )

    return {
        "intake_id":        intake_id,
        "lab_result_id":    lab_result_id,
        "model_name":       "task9_xgboost_heart_model",
        "risk_probability": risk_probability,
        "prediction":       prediction,
        "top_features":     top_features,
        "shap_values":      shap_values,
        "input_features":   input_features,
        "created_at":       now,
    }
