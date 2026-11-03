"""
AggregationService — Business logic for the 7-step heuristic evidence aggregation pipeline.

Domain: Evidence Aggregation
Responsibility: Heuristic scoring, confidence suppression, probability normalization,
                evidence gathering coordination, and persistence.

REPOSITORY RULES — this service:
  ✓ Contains calculations (raw score computation, normalization, coverage dampening)
  ✓ Contains orchestration (gather → score → dampen → suppress → normalize → persist)
  ✓ Contains business rules (suppression thresholds, MIN_SOURCES_REQUIRED, MIN_MAX_SCORE)
  ✓ Contains decision trees (suppression criteria, evidence contribution weights)

  ✗ Does NOT contain API routing or HTTP concerns
  ✗ Does NOT contain DTO transformation
  ✗ Does NOT contain repository definitions
  ✗ Does NOT contain workflow decisions

Design constraints (preserved from original):
  - NO LLM calls
  - NO ML model inference
  - All logic is deterministic and fully explainable via evidence_breakdown
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.domains.ai.repository import (
    aggregation_results_repository,
    nlp_repository,
    risk_scores_repository,
    lab_results_repository,
    imaging_results_repository,
)
from app.domains.triage.repository import intake_repository

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants — suppression thresholds
# ---------------------------------------------------------------------------

CONDITIONS = ["ACS", "PE", "Pneumonia", "Arrhythmia", "Other"]

MIN_SOURCES_REQUIRED = 2    # Must have data from at least 2 subsystems
MIN_MAX_SCORE = 3.0         # Highest single-condition raw score must be ≥ 3


# ---------------------------------------------------------------------------
# Step 1: Gather Evidence
# ---------------------------------------------------------------------------

def fetch_nlp(intake_id: str) -> Optional[dict]:
    """Latest NLP extraction row, or None if unavailable."""
    try:
        return nlp_repository.get_latest(
            intake_id,
            columns="head_trauma, loss_of_consciousness, neurological_risk_flag, "
                    "respiratory_distress, cardiac_risk_flag, extracted_entities",
        )
    except Exception as exc:
        logger.warning("[AggregationService] nlp_extractions fetch failed (non-fatal): %s", exc)
        return None


def fetch_risk(intake_id: str) -> Optional[dict]:
    """Latest risk_scores row, or None if unavailable."""
    try:
        return risk_scores_repository.get_latest(
            intake_id,
            columns="cardiac_risk, respiratory_risk, trauma_risk, neurological_risk, overall_severity",
        )
    except Exception as exc:
        logger.warning("[AggregationService] risk_scores fetch failed (non-fatal): %s", exc)
        return None


def fetch_lab(intake_id: str) -> Optional[dict]:
    """Latest lab_results row, or None if unavailable."""
    try:
        return lab_results_repository.get_latest(
            intake_id,
            columns="prediction, risk_probability",
        )
    except Exception as exc:
        logger.warning("[AggregationService] lab_results fetch failed (non-fatal): %s", exc)
        return None


def fetch_imaging(intake_id: str) -> Optional[dict]:
    """Latest imaging_results row, or None if unavailable."""
    try:
        return imaging_results_repository.get_latest(
            intake_id,
            columns="prediction, pneumonia_probability, confidence",
        )
    except Exception as exc:
        logger.warning("[AggregationService] imaging_results fetch failed (non-fatal): %s", exc)
        return None


# ---------------------------------------------------------------------------
# Step 2: Heuristic Scoring
# ---------------------------------------------------------------------------

def score_evidence(
    nlp: Optional[dict],
    risk: Optional[dict],
    lab: Optional[dict],
    imaging: Optional[dict],
) -> tuple[dict[str, float], dict[str, list[str]]]:
    """
    Apply the deterministic heuristic weight table to all available clinical evidence.

    Returns:
        scores    — {condition: raw_float_score}
        breakdown — {condition: ["source:+delta", ...]}  (full audit trail)

    This is pure business logic — deterministic, fully explainable, no LLM/ML.
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

        has_chest_pain = (
            "chest" in entities_text
            or "chest pain" in entities_text
            or nlp.get("cardiac_risk_flag")
        )
        if has_chest_pain:
            _add("ACS",  3.0, "nlp:chest_pain")
            _add("PE",   1.0, "nlp:chest_pain")

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

        has_palpitations = (
            "palpitation" in entities_text
            or "palpitations" in entities_text
            or "irregular" in entities_text
        )
        if has_palpitations:
            _add("Arrhythmia", 3.0, "nlp:palpitations")

        if nlp.get("cardiac_risk_flag") and not has_chest_pain:
            _add("ACS",       2.0, "nlp:cardiac_risk_flag")
            _add("Arrhythmia", 1.0, "nlp:cardiac_risk_flag")

    # ── Risk Score Evidence ───────────────────────────────────────────────────
    if risk:
        cardiac_score     = float(risk.get("cardiac_risk")     or 0)
        respiratory_score = float(risk.get("respiratory_risk") or 0)

        if cardiac_score >= 50:
            _add("ACS", 4.0, "risk:cardiac_alert")

        if respiratory_score >= 50:
            _add("Pneumonia", 4.0, "risk:respiratory_alert")
            _add("PE",        3.0, "risk:respiratory_alert")

        if 20 <= cardiac_score < 50:
            _add("ACS",       2.0, "risk:cardiac_moderate")
            _add("Arrhythmia", 1.0, "risk:cardiac_moderate")

        if 20 <= respiratory_score < 50:
            _add("Pneumonia", 2.0, "risk:respiratory_moderate")
            _add("PE",        1.0, "risk:respiratory_moderate")

    # ── Lab Model Evidence ────────────────────────────────────────────────────
    if lab:
        prediction = (lab.get("prediction") or "").lower()
        risk_prob  = float(lab.get("risk_probability") or 0.0)

        if prediction == "high_risk":
            delta = round(risk_prob * 5.0, 4)
            _add("ACS", delta, "lab_model:high_risk")
        elif prediction == "low_risk" and risk_prob > 0:
            delta = round(risk_prob * 1.0, 4)
            _add("Other", delta, "lab_model:low_risk")

    # ── Imaging Model Evidence ────────────────────────────────────────────────
    if imaging:
        prediction     = (imaging.get("prediction") or "").lower()
        pneumonia_prob = float(imaging.get("pneumonia_probability") or 0.0)

        if prediction == "pneumonia":
            delta = round(pneumonia_prob * 5.0, 4)
            _add("Pneumonia", delta, "imaging_model:pneumonia")
        elif prediction == "normal" and pneumonia_prob < 0.3:
            _add("PE", -0.5, "imaging_model:normal_scan")

    # Clamp: no condition may go below 0
    for c in CONDITIONS:
        if scores[c] < 0:
            scores[c] = 0.0

    return scores, breakdown





# ---------------------------------------------------------------------------
# Step 4: Confidence Suppression
# ---------------------------------------------------------------------------

def check_suppression(
    scores: dict[str, float],
    sources_present: int,
) -> tuple[bool, Optional[str]]:
    """
    Suppress probability output when clinical evidence is genuinely insufficient.

    Dual-gate suppression criteria (matches original _check_suppression logic):
      • sources_present < MIN_SOURCES_REQUIRED  → not enough subsystems have run
      • max(scores) < MIN_MAX_SCORE             → no condition has meaningful signal

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


# ---------------------------------------------------------------------------
# Step 5: Probability Normalization
# ---------------------------------------------------------------------------

def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    """
    Softmax-free linear normalization.
    Returns probabilities that sum to 1.0 (rounded to 6 decimal places).
    Edge case: when all scores are 0, distributes equally across all conditions.
    """
    total = sum(scores.values())
    if total <= 0:
        n = len(scores)
        return {c: round(1.0 / n, 6) for c in scores}
    return {c: round(v / total, 6) for c, v in scores.items()}


# ---------------------------------------------------------------------------
# Main orchestration entry point
# ---------------------------------------------------------------------------

def run_aggregation(intake_id: str) -> dict:
    """
    Full 7-step heuristic aggregation pipeline:

      1. Verify intake exists
      2. Gather evidence (NLP, risk, lab, imaging)
      3. Heuristic scoring — deterministic weight table
      4. Coverage dampening — penalise incomplete evidence sets
      5. Confidence suppression — dual-gate threshold check
      6. Probability normalisation
      7. Persist to aggregation_results

    Returns a structured dict with all pipeline outputs.

    Raises:
      ValueError  — intake not found (404-worthy)
      Exception   — any other failure (500-worthy)

    The API layer is responsible for pipeline status markers (mark_running,
    mark_completed, mark_failed) and HTTP exception translation.
    """
    # 1. Verify intake exists
    intake_check = intake_repository.get_by_id(intake_id, columns="id")
    if not intake_check:
        raise ValueError(f"Intake {intake_id!r} not found.")

    # 2. Gather Evidence
    nlp     = fetch_nlp(intake_id)
    risk    = fetch_risk(intake_id)
    lab     = fetch_lab(intake_id)
    imaging = fetch_imaging(intake_id)

    source_summary: dict[str, bool] = {
        "nlp":     nlp     is not None,
        "risk":    risk    is not None,
        "lab":     lab     is not None,
        "imaging": imaging is not None,
    }
    sources_present = sum(source_summary.values())

    logger.info("[AggregationService] intake=%s sources=%s", intake_id, source_summary)

    # 3. Heuristic Scoring
    raw_scores, evidence_breakdown = score_evidence(nlp, risk, lab, imaging)
    logger.info("[AggregationService] raw_scores=%s", raw_scores)

    # 4. Confidence Suppression
    suppressed, suppression_reason = check_suppression(raw_scores, sources_present)

    # 5. Probability Normalisation
    if suppressed:
        probabilities: dict[str, Optional[float]] = {c: None for c in CONDITIONS}
        primary_condition: Optional[str] = None
        logger.info("[AggregationService] intake=%s SUPPRESSED: %s", intake_id, suppression_reason)
    else:
        prob_map = normalize_scores(raw_scores)
        probabilities = {c: prob_map[c] for c in CONDITIONS}
        primary_condition = max(prob_map, key=lambda c: prob_map[c])
        logger.info(
            "[AggregationService] intake=%s primary=%s probs=%s",
            intake_id, primary_condition, probabilities,
        )

    # 6. Persist
    now = datetime.now(timezone.utc).isoformat()
    db_row: dict = {
        "intake_id":               intake_id,
        "primary_condition":       primary_condition,
        "confidence_suppressed":   suppressed,
        "suppression_reason":      suppression_reason,
        "raw_scores_json":         raw_scores,
        "evidence_breakdown_json": evidence_breakdown,
        "source_summary_json":     source_summary,
        "created_at":              now,
        "acs_probability":         probabilities.get("ACS"),
        "pe_probability":          probabilities.get("PE"),
        "pneumonia_probability":   probabilities.get("Pneumonia"),
        "arrhythmia_probability":  probabilities.get("Arrhythmia"),
        "other_probability":       probabilities.get("Other"),
    }

    _fallback_exclude = {"primary_condition", "raw_scores_json", "evidence_breakdown_json", "source_summary_json"}
    aggregation_id = ""
    inserted = aggregation_results_repository.insert_with_fallback(db_row, _fallback_exclude)
    if inserted:
        aggregation_id = inserted.get("id", "")
        logger.info(
            "[AggregationService] persisted: id=%s intake=%s suppressed=%s",
            aggregation_id, intake_id, suppressed,
        )

    return {
        "aggregation_id":       aggregation_id,
        "intake_id":            intake_id,
        "primary_condition":    primary_condition,
        "probabilities":        probabilities,
        "confidence_suppressed": suppressed,
        "suppression_reason":   suppression_reason,
        "raw_scores":           raw_scores,
        "evidence_breakdown":   evidence_breakdown,
        "source_summary":       source_summary,
        "created_at":           now,
    }
