"""
Evidence Aggregation Engine
===========================
POST /api/aggregate           — Run full heuristic aggregation for an intake
GET  /api/aggregate/{intake_id} — Retrieve latest aggregation result

Pipeline (7 steps):
  1. Gather Evidence      — query nlp_extractions, risk_scores, lab_results, imaging_results
  2. Heuristic Scoring    — deterministic weight table → per-condition raw scores
  3. Raw Scores           — ACS | PE | Pneumonia | Arrhythmia | Other
  4. Confidence Suppression — suppress if sources_present < 2 OR max_score < 3
  5. Probability Distribution — normalize; probabilities sum to 1.0
  6. Persistence          — insert into aggregation_results
  7. Retrieval            — GET returns latest row

Design constraints:
  - NO LLM calls
  - NO ML model inference
  - All logic is deterministic and fully explainable via evidence_breakdown_json
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domains.ai.repository import aggregation_results_repository
from app.services.aggregation_service import run_aggregation

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic models ───────────────────────────────────────────────────────────

class AggregationRequest(BaseModel):
    intake_id: str = Field(..., description="UUID of the emergency_intake row to aggregate.")


class AggregationResponse(BaseModel):
    aggregation_id: str
    intake_id: str
    primary_condition: Optional[str]
    probabilities: dict[str, Optional[float]]
    confidence_suppressed: bool
    suppression_reason: Optional[str]
    raw_scores: dict[str, float]
    evidence_breakdown: dict[str, list[str]]
    source_summary: dict[str, bool]
    created_at: str


# ── Endpoint: POST /api/aggregate ─────────────────────────────────────────────

@router.post(
    "/aggregation/run",
    response_model=AggregationResponse,
    tags=["Aggregation"],
    summary="Run heuristic evidence aggregation for an intake",
)
@router.post(
    "/aggregate",
    response_model=AggregationResponse,
    tags=["Aggregation"],
    summary="Run heuristic evidence aggregation for an intake",
)
async def run_aggregation_endpoint(body: AggregationRequest) -> AggregationResponse:
    """
    Aggregate all available clinical evidence into a condition probability distribution.

    Sources queried (graceful degradation if any are missing):
      - nlp_extractions
      - risk_scores
      - lab_results
      - imaging_results

    Target conditions: ACS, PE, Pneumonia, Arrhythmia, Other.

    All scoring is deterministic and explainable via evidence_breakdown_json.
    No LLM or ML model is used in this pipeline.
    """
    from app.services.pipeline_status_service import (
        mark_running, mark_completed, mark_failed, get_stage_status,
    )

    intake_id = body.intake_id

    # ── Pipeline Dependency Check ────────────────────────────────────────────
    # NLP: must be completed OR failed (fallback mode is acceptable)
    # Risk: must be completed
    # Lab/Imaging: optional
    # Aggregation: must not already be running
    nlp_status = get_stage_status(intake_id, "nlp")
    risk_status = get_stage_status(intake_id, "risk")
    agg_status  = get_stage_status(intake_id, "aggregation")

    if nlp_status not in ("completed", "failed"):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Aggregation cannot run: NLP stage is '{nlp_status}'. "
                "NLP must be completed or failed (fallback mode) before aggregation."
            ),
        )

    if risk_status != "completed":
        raise HTTPException(
            status_code=400,
            detail=(
                f"Aggregation cannot run: Risk stage is '{risk_status}'. "
                "Risk scoring must be completed before aggregation."
            ),
        )

    if agg_status == "running":
        raise HTTPException(
            status_code=400,
            detail="Aggregation is already running for this intake.",
        )

    mark_running(intake_id, "aggregation")

    try:
        result = run_aggregation(intake_id)
        mark_completed(intake_id, "aggregation")
        # Invalidate cached report since aggregation result has changed
        from app.services.report_service import invalidate_report_cache
        invalidate_report_cache(intake_id)
        return AggregationResponse(**result)

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        mark_failed(intake_id, "aggregation", exc)


# ── Endpoint: GET /api/aggregate/{intake_id} ──────────────────────────────────

@router.get(
    "/aggregate/{intake_id}",
    tags=["Aggregation"],
    summary="Retrieve latest aggregation result for an intake",
)
async def get_aggregation(intake_id: str):
    """
    Return the most recent aggregation_results row for the given intake_id.

    Raises 404 if no aggregation has been run yet for this intake.
    Gracefully handles both the new schema (with primary_condition, JSONB
    debug columns) and the legacy schema (if migration 006 hasn't run yet).
    """
    _full_cols = (
        "id, intake_id, primary_condition, "
        "acs_probability, pe_probability, pneumonia_probability, "
        "arrhythmia_probability, other_probability, "
        "confidence_suppressed, suppression_reason, "
        "raw_scores_json, evidence_breakdown_json, source_summary_json, "
        "created_at"
    )
    _legacy_cols = (
        "id, intake_id, "
        "acs_probability, pe_probability, pneumonia_probability, "
        "arrhythmia_probability, other_probability, "
        "confidence_suppressed, suppression_reason, "
        "created_at"
    )

    rows = None
    try:
        row = aggregation_results_repository.get_latest(intake_id, _full_cols)
        rows = [row] if row else []
    except Exception as exc:
        err_str = str(exc)
        _new_cols_names = ["primary_condition", "raw_scores_json", "evidence_breakdown_json", "source_summary_json"]
        if any(c in err_str for c in _new_cols_names) or "42703" in err_str:
            logger.warning("[PRATHAM/AGG] GET: falling back to legacy columns — run migration 006")
            try:
                row2 = aggregation_results_repository.get_latest(intake_id, _legacy_cols)
                rows = [row2] if row2 else []
            except Exception as exc2:
                raise HTTPException(status_code=500, detail=str(exc2))
        else:
            raise HTTPException(status_code=500, detail=err_str)

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No aggregation results found for intake {intake_id!r}. Run POST /api/aggregate first.",
        )

    row = rows[0]

    suppressed = row.get("confidence_suppressed", False)
    probabilities: dict[str, Optional[float]] = {
        "ACS":        row.get("acs_probability"),
        "PE":         row.get("pe_probability"),
        "Pneumonia":  row.get("pneumonia_probability"),
        "Arrhythmia": row.get("arrhythmia_probability"),
        "Other":      row.get("other_probability"),
    }

    return {
        "aggregation_id":        row.get("id"),
        "intake_id":             row.get("intake_id"),
        "primary_condition":     row.get("primary_condition"),
        "probabilities":         probabilities,
        "confidence_suppressed": suppressed,
        "suppression_reason":    row.get("suppression_reason"),
        "raw_scores":            row.get("raw_scores_json") or {},
        "evidence_breakdown":    row.get("evidence_breakdown_json") or {},
        "source_summary":        row.get("source_summary_json") or {},
        "created_at":            row.get("created_at"),
    }
