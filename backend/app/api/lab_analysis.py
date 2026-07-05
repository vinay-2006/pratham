"""
POST /api/lab/analyze — XGBoost cardiac risk inference endpoint.

Workflow:
  1. Fetch patient demographics + vitals from DB via intake_id.
  2. Merge with optional clinical overrides supplied in the request body
     (fields not captured in the general intake form).
  3. Build the 15-feature vector that matches training preprocessing.
  4. Run XGBoost predict_proba + SHAP TreeExplainer.
  5. Persist result to lab_results table.
  6. Return structured JSON response.

DB fields available from intake:
    age         → patients.date_of_birth
    sex         → patients.gender
    resting_bp  → vitals.bp_systolic
    max_hr      → vitals.heart_rate  (best proxy available in intake)

Fields NOT captured during general intake (require clinical_override):
    chest_pain_type, cholesterol, fasting_bs, resting_ecg,
    exercise_angina, oldpeak, st_slope
    If not provided they fall back to safe population-median defaults.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.supabase_client import supabase
from app.ml.lab_model import run_inference

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────

class ClinicalOverride(BaseModel):
    """
    Optional clinical fields not captured during general triage intake.
    Provide these when available from a detailed cardiac workup.
    Defaults match population medians from the UCI Heart Disease dataset.
    """
    chest_pain_type: Optional[str] = Field(
        default="ASY",
        description="ASY (asymptomatic) | ATA (atypical angina) | NAP (non-anginal) | TA (typical angina)",
    )
    cholesterol: Optional[float] = Field(
        default=0,
        description="Serum cholesterol mg/dL. 0 → imputed to 200 (dataset mean).",
    )
    fasting_bs: Optional[int] = Field(
        default=0,
        description="Fasting blood sugar >120 mg/dL → 1, else 0.",
    )
    resting_ecg: Optional[str] = Field(
        default="Normal",
        description="Normal | ST | LVH",
    )
    max_hr: Optional[float] = Field(
        default=None,
        description="Maximum heart rate achieved during exercise. "
                    "If omitted, uses vitals.heart_rate from intake.",
    )
    exercise_angina: Optional[str] = Field(
        default="N",
        description="Exercise-induced angina: Y or N.",
    )
    oldpeak: Optional[float] = Field(
        default=0.0,
        description="ST depression (Oldpeak) induced by exercise relative to rest.",
    )
    st_slope: Optional[str] = Field(
        default="Flat",
        description="Slope of the peak exercise ST segment: Up | Flat | Down.",
    )


class LabAnalyzeRequest(BaseModel):
    intake_id: str = Field(..., description="UUID of the emergency_intake row to analyse.")
    clinical_override: Optional[ClinicalOverride] = Field(
        default=None,
        description="Optional detailed cardiac fields not in general intake.",
    )


class LabAnalyzeResponse(BaseModel):
    intake_id: str
    lab_result_id: str
    model_name: str
    risk_probability: float
    prediction: str
    top_features: dict[str, float]
    shap_values: dict[str, float]
    input_features: dict[str, float]
    created_at: str


# ── Helpers ───────────────────────────────────────────────────────────────

def _compute_age(dob: str | None) -> int:
    """Derive age in years from a date_of_birth string (YYYY-MM-DD or numeric year)."""
    if not dob:
        return 50  # safe default
    if "-" in str(dob):
        try:
            birth_year = int(str(dob).split("-")[0])
            return max(1, datetime.now().year - birth_year)
        except (ValueError, IndexError):
            pass
    try:
        return int(dob)  # age was stored as integer directly
    except (TypeError, ValueError):
        return 50


def _top_n_features(shap_dict: dict[str, float], n: int = 5) -> dict[str, float]:
    """Return the N features with the largest absolute SHAP contribution."""
    if not shap_dict:
        return {}
    sorted_items = sorted(shap_dict.items(), key=lambda kv: abs(kv[1]), reverse=True)
    return {k: round(v, 6) for k, v in sorted_items[:n]}


def _fetch_patient_data(intake_id: str) -> dict[str, Any]:
    """
    Pull demographics + vitals from Supabase for the given intake.
    Returns a flat dict keyed to model input field names.
    Raises HTTPException on not-found.
    """
    # Intake + patient join
    intake_res = (
        supabase.table("emergency_intake")
        .select(
            "id, status, severity_level, "
            "patients(first_name, last_name, gender, date_of_birth)"
        )
        .eq("id", intake_id)
        .execute()
    )
    if not intake_res.data:
        raise HTTPException(status_code=404, detail=f"Intake {intake_id!r} not found.")

    intake = intake_res.data[0]
    patient_row = intake.get("patients") or {}

    # Vitals
    vitals_res = (
        supabase.table("vitals")
        .select("heart_rate, bp_systolic, bp_diastolic")
        .eq("intake_id", intake_id)
        .limit(1)
        .execute()
    )
    vitals = (vitals_res.data or [{}])[0]

    gender = (patient_row.get("gender") or "").lower()
    sex = "M" if gender == "male" else "F"
    age = _compute_age(patient_row.get("date_of_birth"))

    resting_bp = vitals.get("bp_systolic") or 120
    heart_rate  = vitals.get("heart_rate") or 100

    return {
        "age": age,
        "sex": sex,
        "resting_bp": resting_bp,
        "heart_rate_from_vitals": heart_rate,  # used as fallback for max_hr
    }


# ── Endpoint ──────────────────────────────────────────────────────────────

@router.post(
    "/lab/analyze",
    response_model=LabAnalyzeResponse,
    tags=["Lab Analysis"],
    summary="XGBoost cardiac risk inference + SHAP explanation",
)
async def lab_analyze(body: LabAnalyzeRequest) -> LabAnalyzeResponse:
    """
    Run the XGBoost cardiac risk model on a patient identified by intake_id.

    Demographics and vitals are fetched from the database automatically.
    Supply `clinical_override` for detailed cardiac fields not captured
    during general triage (chest pain type, ECG, exercise data, etc.).

    Results are persisted to the `lab_results` table and returned in
    the response.
    """
    from app.services.pipeline_status_service import mark_running, mark_completed, mark_failed

    intake_id = body.intake_id
    override  = body.clinical_override or ClinicalOverride()

    mark_running(intake_id, "lab")

    try:
        # 1. Pull base data from DB
        try:
            db_data = _fetch_patient_data(intake_id)
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("[PRATHAM/ML] DB fetch failed for intake %s: %s", intake_id, exc)
            raise HTTPException(status_code=500, detail=f"Database error: {exc}")

        # 2. Build full patient dict for model
        max_hr = override.max_hr if override.max_hr is not None else db_data["heart_rate_from_vitals"]

        patient_input: dict[str, Any] = {
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

        # 3. Run inference (XGBoost + SHAP)
        try:
            result = run_inference(patient_input)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        except Exception as exc:
            logger.error("[PRATHAM/ML] Inference failed: %s", exc)
            raise HTTPException(status_code=500, detail=f"Inference error: {exc}")

        risk_probability = result["risk_probability"]
        prediction       = result["prediction"]
        shap_values      = result["shap_values"]
        input_features   = result["input_features"]
        top_features     = _top_n_features(shap_values, n=5)

        # 4. Persist to lab_results
        now = datetime.now(timezone.utc).isoformat()
        db_row = {
            "intake_id":        intake_id,
            "model_name":       "task9_xgboost_heart_model",
            "prediction":       prediction,
            "risk_probability": risk_probability,
            "shap_values":      shap_values,         # JSONB
            "input_features":   input_features,      # JSONB
            "created_at":       now,
        }

        lab_result_id = ""
        try:
            insert_res = supabase.table("lab_results").insert(db_row).execute()
            if insert_res.data:
                lab_result_id = insert_res.data[0].get("id", "")
            logger.info(
                "[PRATHAM/ML] lab_results row inserted: id=%s intake=%s prediction=%s prob=%.4f",
                lab_result_id, intake_id, prediction, risk_probability,
            )
        except Exception as db_exc:
            # Non-fatal: still return the prediction even if DB write fails
            logger.error(
                "[PRATHAM/ML] lab_results insert failed (non-fatal): %s", db_exc
            )

        mark_completed(intake_id, "lab")

        return LabAnalyzeResponse(
            intake_id=intake_id,
            lab_result_id=lab_result_id,
            model_name="task9_xgboost_heart_model",
            risk_probability=risk_probability,
            prediction=prediction,
            top_features=top_features,
            shap_values=shap_values,
            input_features=input_features,
            created_at=now,
        )

    except Exception as exc:
        # Mark failed then re-raise (mark_failed re-raises automatically)
        mark_failed(intake_id, "lab", exc)


# ── GET: retrieve stored results ──────────────────────────────────────────

@router.get(
    "/lab/results/{intake_id}",
    tags=["Lab Analysis"],
    summary="Fetch stored lab analysis results for an intake",
)
async def get_lab_results(intake_id: str):
    """
    Return all lab_results rows for the given intake, newest first.
    """
    try:
        res = (
            supabase.table("lab_results")
            .select("id, model_name, prediction, risk_probability, shap_values, input_features, created_at")
            .eq("intake_id", intake_id)
            .order("created_at", desc=True)
            .execute()
        )
        rows = res.data or []
        return {"intake_id": intake_id, "count": len(rows), "results": rows}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
