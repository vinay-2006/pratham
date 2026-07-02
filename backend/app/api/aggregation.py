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

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.supabase_client import supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Constants ─────────────────────────────────────────────────────────────────

CONDITIONS = ["ACS", "PE", "Pneumonia", "Arrhythmia", "Other"]

# Suppression thresholds (Modification 1)
MIN_SOURCES_REQUIRED = 2      # must have data from at least 2 subsystems
MIN_MAX_SCORE = 3.0           # highest single-condition raw score must be ≥ 3


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


# ── Step 1: Gather Evidence ───────────────────────────────────────────────────

def _fetch_nlp(intake_id: str) -> Optional[dict]:
    """Latest NLP extraction row, or None if unavailable."""
    try:
        res = (
            supabase.table("nlp_extractions")
            .select(
                "head_trauma, loss_of_consciousness, neurological_risk_flag, "
                "respiratory_distress, cardiac_risk_flag, extracted_entities"
            )
            .eq("intake_id", intake_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        data = res.data or []
        return data[0] if data else None
    except Exception as exc:
        logger.warning("[PRATHAM/AGG] nlp_extractions fetch failed (non-fatal): %s", exc)
        return None


def _fetch_risk(intake_id: str) -> Optional[dict]:
    """Latest risk_scores row, or None if unavailable."""
    try:
        res = (
            supabase.table("risk_scores")
            .select("cardiac_risk, respiratory_risk, trauma_risk, neurological_risk, overall_severity")
            .eq("intake_id", intake_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        data = res.data or []
        return data[0] if data else None
    except Exception as exc:
        logger.warning("[PRATHAM/AGG] risk_scores fetch failed (non-fatal): %s", exc)
        return None


def _fetch_lab(intake_id: str) -> Optional[dict]:
    """Latest lab_results row, or None if unavailable."""
    try:
        res = (
            supabase.table("lab_results")
            .select("prediction, risk_probability")
            .eq("intake_id", intake_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        data = res.data or []
        return data[0] if data else None
    except Exception as exc:
        logger.warning("[PRATHAM/AGG] lab_results fetch failed (non-fatal): %s", exc)
        return None


def _fetch_imaging(intake_id: str) -> Optional[dict]:
    """Latest imaging_results row, or None if unavailable."""
    try:
        res = (
            supabase.table("imaging_results")
            .select("prediction, pneumonia_probability, confidence")
            .eq("intake_id", intake_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        data = res.data or []
        return data[0] if data else None
    except Exception as exc:
        logger.warning("[PRATHAM/AGG] imaging_results fetch failed (non-fatal): %s", exc)
        return None


# ── Step 2: Heuristic Scoring ─────────────────────────────────────────────────

def _score_evidence(
    nlp: Optional[dict],
    risk: Optional[dict],
    lab: Optional[dict],
    imaging: Optional[dict],
) -> tuple[dict[str, float], dict[str, list[str]]]:
    """
    Apply the deterministic weight table.

    Returns:
        scores      — {condition: raw_float_score}
        breakdown   — {condition: ["source:+delta", ...]}  (full audit trail)
    """
    scores: dict[str, float] = {c: 0.0 for c in CONDITIONS}
    breakdown: dict[str, list[str]] = {c: [] for c in CONDITIONS}

    def _add(condition: str, delta: float, label: str) -> None:
        scores[condition] += delta
        sign = f"+{delta:.1f}" if delta >= 0 else f"{delta:.1f}"
        breakdown[condition].append(f"{label}:{sign}")

    # ── NLP Evidence ──────────────────────────────────────────────────────────
    if nlp:
        entities: list[str] = [
            str(e).lower() for e in (nlp.get("extracted_entities") or [])
        ]
        entities_text = " ".join(entities)

        # Chest pain signals
        has_chest_pain = (
            "chest" in entities_text
            or "chest pain" in entities_text
            or nlp.get("cardiac_risk_flag")
        )
        if has_chest_pain:
            _add("ACS",  3.0, "nlp:chest_pain")
            _add("PE",   1.0, "nlp:chest_pain")

        # Breathlessness / respiratory distress signals
        has_breathlessness = (
            "breath" in entities_text
            or "dyspnoe" in entities_text
            or "dyspnoea" in entities_text
            or "shortness" in entities_text
            or nlp.get("respiratory_distress")
        )
        if has_breathlessness:
            _add("PE",        3.0, "nlp:breathlessness")
            _add("Pneumonia", 2.0, "nlp:breathlessness")
            _add("ACS",       1.0, "nlp:breathlessness")

        # Palpitations / arrhythmia signals
        has_palpitations = (
            "palpitation" in entities_text
            or "palpitations" in entities_text
            or "irregular" in entities_text
        )
        if has_palpitations:
            _add("Arrhythmia", 3.0, "nlp:palpitations")

        # Cardiac risk flag (flag alone, not already counted via chest_pain)
        if nlp.get("cardiac_risk_flag") and not has_chest_pain:
            _add("ACS",       2.0, "nlp:cardiac_risk_flag")
            _add("Arrhythmia", 1.0, "nlp:cardiac_risk_flag")

    # ── Risk Score Evidence ───────────────────────────────────────────────────
    if risk:
        cardiac_score = float(risk.get("cardiac_risk") or 0)
        respiratory_score = float(risk.get("respiratory_risk") or 0)

        # cardiac_alert: cardiac_risk >= 50
        if cardiac_score >= 50:
            _add("ACS", 4.0, "risk:cardiac_alert")

        # respiratory_alert: respiratory_risk >= 50
        if respiratory_score >= 50:
            _add("Pneumonia", 4.0, "risk:respiratory_alert")
            _add("PE",        3.0, "risk:respiratory_alert")

        # Moderate cardiac signal: 20–49
        if 20 <= cardiac_score < 50:
            _add("ACS",       2.0, "risk:cardiac_moderate")
            _add("Arrhythmia", 1.0, "risk:cardiac_moderate")

        # Moderate respiratory signal: 20–49
        if 20 <= respiratory_score < 50:
            _add("Pneumonia", 2.0, "risk:respiratory_moderate")
            _add("PE",        1.0, "risk:respiratory_moderate")

    # ── Lab Model Evidence ────────────────────────────────────────────────────
    if lab:
        prediction = (lab.get("prediction") or "").lower()
        risk_prob = float(lab.get("risk_probability") or 0.0)

        if prediction == "high_risk":
            delta = round(risk_prob * 5.0, 4)
            _add("ACS", delta, "lab_model:high_risk")
        elif prediction == "low_risk" and risk_prob > 0:
            # Low-risk lab result nudges Other slightly
            delta = round(risk_prob * 1.0, 4)
            _add("Other", delta, "lab_model:low_risk")

    # ── Imaging Model Evidence ────────────────────────────────────────────────
    if imaging:
        prediction = (imaging.get("prediction") or "").lower()
        pneumonia_prob = float(imaging.get("pneumonia_probability") or 0.0)

        if prediction == "pneumonia":
            delta = round(pneumonia_prob * 5.0, 4)
            _add("Pneumonia", delta, "imaging_model:pneumonia")
        elif prediction == "normal" and pneumonia_prob < 0.3:
            # Normal imaging slightly reduces PE (PE vs. Pneumonia disambiguation)
            _add("PE", -0.5, "imaging_model:normal_scan")

    # Ensure no condition goes below 0
    for c in CONDITIONS:
        if scores[c] < 0:
            scores[c] = 0.0

    return scores, breakdown


# ── Step 4: Confidence Suppression ────────────────────────────────────────────

def _check_suppression(
    scores: dict[str, float],
    sources_present: int,
) -> tuple[bool, Optional[str]]:
    """
    Suppress probability output when evidence is genuinely insufficient.

    Suppression criteria (Modification 1 — source-count + max-score dual gate):
      • sources_present < 2  → not enough subsystems have run
      • max(scores) < 3.0    → no condition has meaningful signal

    Returns (suppressed: bool, reason: str | None).
    """
    if sources_present < MIN_SOURCES_REQUIRED:
        return True, (
            f"Insufficient data sources: only {sources_present} subsystem(s) "
            f"available (minimum {MIN_SOURCES_REQUIRED} required)"
        )

    max_score = max(scores.values()) if scores else 0.0
    if max_score < MIN_MAX_SCORE:
        return True, (
            f"Insufficient signal strength: highest condition score is "
            f"{max_score:.2f} (minimum {MIN_MAX_SCORE} required)"
        )

    return False, None


# ── Step 5: Probability Distribution ─────────────────────────────────────────

def _normalize(scores: dict[str, float]) -> dict[str, float]:
    """Softmax-free linear normalization. Returns probabilities summing to 1.0."""
    total = sum(scores.values())
    if total <= 0:
        # Edge case: distribute equally
        n = len(scores)
        return {c: round(1.0 / n, 6) for c in scores}
    return {c: round(v / total, 6) for c, v in scores.items()}


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
async def run_aggregation(body: AggregationRequest) -> AggregationResponse:
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
    intake_id = body.intake_id

    # Verify intake exists
    try:
        intake_check = (
            supabase.table("emergency_intake")
            .select("id")
            .eq("id", intake_id)
            .limit(1)
            .execute()
        )
        if not intake_check.data:
            raise HTTPException(status_code=404, detail=f"Intake {intake_id!r} not found.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")

    # ── Step 1: Gather Evidence ──────────────────────────────────────────────
    nlp     = _fetch_nlp(intake_id)
    risk    = _fetch_risk(intake_id)
    lab     = _fetch_lab(intake_id)
    imaging = _fetch_imaging(intake_id)

    source_summary: dict[str, bool] = {
        "nlp":     nlp is not None,
        "risk":    risk is not None,
        "lab":     lab is not None,
        "imaging": imaging is not None,
    }
    sources_present = sum(source_summary.values())

    logger.info(
        "[PRATHAM/AGG] intake=%s sources=%s",
        intake_id, source_summary
    )

    # ── Step 2 & 3: Score + Raw Scores ──────────────────────────────────────
    raw_scores, evidence_breakdown = _score_evidence(nlp, risk, lab, imaging)

    logger.info("[PRATHAM/AGG] raw_scores=%s", raw_scores)

    # ── Step 4: Confidence Suppression ──────────────────────────────────────
    suppressed, suppression_reason = _check_suppression(raw_scores, sources_present)

    # ── Step 5: Probability Distribution ────────────────────────────────────
    probabilities: dict[str, Optional[float]]
    primary_condition: Optional[str]

    if suppressed:
        probabilities = {c: None for c in CONDITIONS}
        primary_condition = None
        logger.info(
            "[PRATHAM/AGG] intake=%s SUPPRESSED: %s",
            intake_id, suppression_reason
        )
    else:
        prob_map = _normalize(raw_scores)
        probabilities = {c: prob_map[c] for c in CONDITIONS}
        primary_condition = max(prob_map, key=lambda c: prob_map[c])
        logger.info(
            "[PRATHAM/AGG] intake=%s primary=%s probs=%s",
            intake_id, primary_condition, probabilities
        )

    # ── Step 6: Persist ──────────────────────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()

    db_row: dict = {
        "intake_id":              intake_id,
        "primary_condition":      primary_condition,
        "confidence_suppressed":  suppressed,
        "suppression_reason":     suppression_reason,
        "raw_scores_json":        raw_scores,
        "evidence_breakdown_json": evidence_breakdown,
        "source_summary_json":    source_summary,
        "created_at":             now,
    }

    # Populate probability columns (NULL when suppressed)
    db_row["acs_probability"]        = probabilities.get("ACS")
    db_row["pe_probability"]         = probabilities.get("PE")
    db_row["pneumonia_probability"]  = probabilities.get("Pneumonia")
    db_row["arrhythmia_probability"] = probabilities.get("Arrhythmia")
    db_row["other_probability"]      = probabilities.get("Other")

    aggregation_id = ""
    try:
        insert_res = supabase.table("aggregation_results").insert(db_row).execute()
        if insert_res.data:
            aggregation_id = insert_res.data[0].get("id", "")
        logger.info(
            "[PRATHAM/AGG] persisted: id=%s intake=%s suppressed=%s",
            aggregation_id, intake_id, suppressed,
        )
    except Exception as db_exc:
        err_str = str(db_exc)
        # Graceful fallback: new columns may not exist if migration 006 hasn't run yet.
        # Retry with the minimal guaranteed columns (original schema).
        _new_cols = {"primary_condition", "raw_scores_json", "evidence_breakdown_json", "source_summary_json"}
        col_missing = any(c in err_str for c in _new_cols) or "PGRST204" in err_str or "column" in err_str.lower()
        if col_missing:
            logger.warning(
                "[PRATHAM/AGG] New columns missing — falling back to legacy schema. "
                "Run migrations/006_aggregation_results_schema.sql in Supabase."
            )
            legacy_row = {
                k: v for k, v in db_row.items()
                if k not in _new_cols
            }
            try:
                fallback_res = supabase.table("aggregation_results").insert(legacy_row).execute()
                if fallback_res.data:
                    aggregation_id = fallback_res.data[0].get("id", "")
                logger.info("[PRATHAM/AGG] legacy persist ok: id=%s", aggregation_id)
            except Exception as fb_exc:
                logger.error("[PRATHAM/AGG] legacy persist also failed (non-fatal): %s", fb_exc)
        else:
            logger.error("[PRATHAM/AGG] aggregation_results insert failed (non-fatal): %s", db_exc)

    return AggregationResponse(
        aggregation_id=aggregation_id,
        intake_id=intake_id,
        primary_condition=primary_condition,
        probabilities=probabilities,
        confidence_suppressed=suppressed,
        suppression_reason=suppression_reason,
        raw_scores=raw_scores,
        evidence_breakdown=evidence_breakdown,
        source_summary=source_summary,
        created_at=now,
    )


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
    # Attempt 1: full new schema select
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
        res = (
            supabase.table("aggregation_results")
            .select(_full_cols)
            .eq("intake_id", intake_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = res.data or []
    except Exception as exc:
        err_str = str(exc)
        # Column missing — fall back to legacy columns (migration 006 not yet applied)
        _new_cols_names = ["primary_condition", "raw_scores_json", "evidence_breakdown_json", "source_summary_json"]
        if any(c in err_str for c in _new_cols_names) or "42703" in err_str:
            logger.warning("[PRATHAM/AGG] GET: falling back to legacy columns — run migration 006")
            try:
                res2 = (
                    supabase.table("aggregation_results")
                    .select(_legacy_cols)
                    .eq("intake_id", intake_id)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )
                rows = res2.data or []
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

    # Reconstruct probabilities dict from individual columns
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
        "primary_condition":     row.get("primary_condition"),   # None on legacy schema
        "probabilities":         probabilities,
        "confidence_suppressed": suppressed,
        "suppression_reason":    row.get("suppression_reason"),
        "raw_scores":            row.get("raw_scores_json") or {},
        "evidence_breakdown":    row.get("evidence_breakdown_json") or {},
        "source_summary":        row.get("source_summary_json") or {},
        "created_at":            row.get("created_at"),
    }
