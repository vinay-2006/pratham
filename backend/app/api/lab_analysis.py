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
    max_hr      → override.max_hr if supplied by clinician,
                   else estimated as 220 - age (Tanaka formula),
                   else 150 bpm (population median fallback when age unavailable)

Fields NOT captured during general intake (require clinical_override):
    chest_pain_type, cholesterol, fasting_bs, resting_ecg,
    exercise_angina, oldpeak, st_slope
    If not provided they fall back to safe population-median defaults.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.ai.repository import lab_results_repository
from app.services.lab_analysis_service import run_lab_analysis

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
        description="Maximum heart rate achieved during exercise stress testing. "
                    "If omitted, estimated as 220 − age (Tanaka formula). "
                    "If age is also unavailable, defaults to 150 bpm (population median).",
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
        result = run_lab_analysis(intake_id, override)
        mark_completed(intake_id, "lab")
        return LabAnalyzeResponse(**result)

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        mark_failed(intake_id, "lab", exc)
    except Exception as exc:
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
        _cols = "id, model_name, prediction, risk_probability, shap_values, input_features, created_at"
        rows = lab_results_repository.get_all_for_intake(intake_id, _cols)
        return {"intake_id": intake_id, "count": len(rows), "results": rows}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
