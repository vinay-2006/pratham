"""
Pipeline Status Service — Central source of truth for AI pipeline execution.

Every AI subsystem (NLP, Risk, Lab, Imaging, Aggregation) must use this
service to record its execution state.  No subsystem should write to the
pipeline_status table directly.

State machine per stage:
    pending  →  running  →  completed
                         →  failed  →  running  (retry)

Key behaviours:
  · initialize_pipeline()  — inserts 5 rows all `pending`; mandatory at intake
  · mark_running()         — sets status + started_at; increments attempt_count
  · mark_completed()       — sets status + completed_at + auto-computed duration_ms
  · mark_failed()          — stores error_message then RE-RAISES the exception
  · reset_stage()          — resets a stage back to `pending` (used on evidence deletion)
  · get_pipeline_status()  — returns dict of all 5 stages with full metadata

Persistence: All pipeline_status table access is delegated to PipelineRepository (R1.2).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.domains.pipeline.repository import pipeline_repository

logger = logging.getLogger(__name__)

STAGES = ("nlp", "risk", "lab", "imaging", "aggregation")


# ── Initialize ───────────────────────────────────────────────────────────────

def initialize_pipeline(intake_id: str) -> None:
    """
    Insert all 5 pipeline stages with status='pending'.

    This MUST be called immediately after a successful intake creation.
    If this fails, the caller must abort the intake (rollback).

    Raises Exception on failure — never swallowed.
    """
    try:
        result = pipeline_repository.initialize(intake_id, STAGES)
        if len(result) < len(STAGES):
            raise RuntimeError(
                f"pipeline_status insert returned {len(result)} rows, expected {len(STAGES)}"
            )
        logger.info("[PRATHAM/PIPELINE] Initialized pipeline for intake %s", intake_id)
    except Exception as exc:
        logger.error("[PRATHAM/PIPELINE] initialize_pipeline FAILED for intake %s: %s", intake_id, exc)
        raise


# ── Mark Running ─────────────────────────────────────────────────────────────

def mark_running(intake_id: str, stage: str) -> None:
    """
    Transition a stage to 'running'.

    Sets started_at to now, clears completed_at/duration_ms/error_message,
    and increments attempt_count.

    Supports retries: a 'failed' stage can transition back to 'running'.
    """
    if stage not in STAGES:
        raise ValueError(f"Invalid pipeline stage: {stage!r}")

    now = datetime.now(timezone.utc).isoformat()

    try:
        # Fetch current attempt_count via repository
        current_row = pipeline_repository.get_stage(intake_id, stage)
        current_count = 0
        if current_row:
            current_count = current_row.get("attempt_count", 0) or 0

        pipeline_repository.update_stage(intake_id, stage, {
            "status": "running",
            "started_at": now,
            "completed_at": None,
            "duration_ms": None,
            "error_message": None,
            "attempt_count": current_count + 1,
            "updated_at": now,
        })

        logger.info(
            "[PRATHAM/PIPELINE] %s → running (attempt %d) for intake %s",
            stage, current_count + 1, intake_id,
        )

        try:
            from app.services.workflow_service import update_workflow_status, get_workflow_status
            from app.domains.shared.enums import WorkflowStatus
            # Only attempt the transition if the patient has progressed past
            # doctor approval (approved / upload_pending).  Earlier states
            # (en_route, arrived, awaiting_doctor_approval) correctly reject
            # analysis_running but produce noisy log warnings.
            from app.domains.triage.repository import intake_repository
            intake_row = intake_repository.get_by_id(intake_id, columns="status")
            cur_status = get_workflow_status(
                intake_id,
                (intake_row.get("status") if intake_row else None)
            ) if intake_row else None
            eligible_states = {
                WorkflowStatus.APPROVED.value,
                WorkflowStatus.UPLOAD_PENDING.value,
                WorkflowStatus.ANALYSIS_RUNNING.value,  # self-transition OK
            }
            if cur_status in eligible_states:
                update_workflow_status(
                    intake_id=intake_id,
                    new_status=WorkflowStatus.ANALYSIS_RUNNING.value,
                    actor_type="System",
                    actor_name="AI Pipeline Engine",
                    reason=f"AI pipeline stage '{stage}' started."
                )
        except Exception as e:
            logger.warning("[PRATHAM/PIPELINE] Status update on stage start failed: %s", e)
    except Exception as exc:
        logger.error("[PRATHAM/PIPELINE] mark_running(%s) failed: %s", stage, exc)
        raise


# ── Mark Completed ───────────────────────────────────────────────────────────

def mark_completed(intake_id: str, stage: str) -> None:
    """
    Transition a stage to 'completed'.

    Automatically computes duration_ms from started_at to now.
    """
    if stage not in STAGES:
        raise ValueError(f"Invalid pipeline stage: {stage!r}")

    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    try:
        # Fetch started_at to compute duration via repository
        row = pipeline_repository.get_stage(intake_id, stage)

        duration_ms = None
        if row and row.get("started_at"):
            started_str = row["started_at"]
            try:
                started_at = datetime.fromisoformat(started_str.replace("Z", "+00:00"))
                duration_ms = int((now - started_at).total_seconds() * 1000)
            except (ValueError, TypeError):
                pass

        pipeline_repository.update_stage(intake_id, stage, {
            "status": "completed",
            "completed_at": now_iso,
            "duration_ms": duration_ms,
            "error_message": None,
            "updated_at": now_iso,
        })

        logger.info(
            "[PRATHAM/PIPELINE] %s → completed (%s ms) for intake %s",
            stage, duration_ms, intake_id,
        )

        if stage == "aggregation":
            try:
                from app.services.workflow_service import update_workflow_status
                from app.domains.shared.enums import WorkflowStatus
                update_workflow_status(
                    intake_id=intake_id,
                    new_status=WorkflowStatus.REPORT_READY.value,
                    actor_type="System",
                    actor_name="AI Pipeline Engine",
                    reason="Evidence aggregation completed. Clinical report is now ready."
                )
            except Exception as e:
                logger.warning("[PRATHAM/PIPELINE] Status update on aggregation complete failed: %s", e)
    except Exception as exc:
        logger.error("[PRATHAM/PIPELINE] mark_completed(%s) failed: %s", stage, exc)
        raise


# ── Mark Failed ──────────────────────────────────────────────────────────────

def mark_failed(intake_id: str, stage: str, error: Exception) -> None:
    """
    Transition a stage to 'failed' and store the error message.

    IMPORTANT: This method RE-RAISES the exception after recording it.
    It never swallows failures.
    """
    if stage not in STAGES:
        raise ValueError(f"Invalid pipeline stage: {stage!r}")

    now = datetime.now(timezone.utc).isoformat()
    error_msg = str(error)

    try:
        pipeline_repository.update_stage(intake_id, stage, {
            "status": "failed",
            "error_message": error_msg,
            "updated_at": now,
        })

        logger.error(
            "[PRATHAM/PIPELINE] %s → failed for intake %s: %s",
            stage, intake_id, error_msg,
        )
    except Exception as db_exc:
        # Even if the DB update fails, we still re-raise the original error
        logger.error(
            "[PRATHAM/PIPELINE] mark_failed(%s) DB update also failed: %s",
            stage, db_exc,
        )

    raise error


# ── Reset Stage ──────────────────────────────────────────────────────────────

def reset_stage(intake_id: str, stage: str) -> None:
    """
    Reset a stage back to 'pending'.

    Used when evidence is deleted and downstream results are invalidated.
    Clears started_at, completed_at, duration_ms, error_message.
    Does NOT reset attempt_count (preserves history).
    """
    if stage not in STAGES:
        raise ValueError(f"Invalid pipeline stage: {stage!r}")

    now = datetime.now(timezone.utc).isoformat()

    try:
        pipeline_repository.update_stage(intake_id, stage, {
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "duration_ms": None,
            "error_message": None,
            "updated_at": now,
        })

        logger.info("[PRATHAM/PIPELINE] %s → pending (reset) for intake %s", stage, intake_id)
    except Exception as exc:
        logger.error("[PRATHAM/PIPELINE] reset_stage(%s) failed: %s", stage, exc)
        # Non-fatal: don't break the deletion flow
        pass


# ── Get Pipeline Status ──────────────────────────────────────────────────────

def get_pipeline_status(intake_id: str) -> dict:
    """
    Return the full pipeline status for an intake.

    Returns:
        {
            "intake_id": "...",
            "stages": {
                "nlp":         { "status": "completed", "started_at": ..., ... },
                "risk":        { ... },
                "lab":         { ... },
                "imaging":     { ... },
                "aggregation": { ... }
            }
        }
    """
    try:
        rows = pipeline_repository.get_by_intake_id(intake_id)
    except Exception as exc:
        logger.error("[PRATHAM/PIPELINE] get_pipeline_status failed for intake %s: %s", intake_id, exc)
        raise

    stages: dict = {}
    for row in rows:
        stages[row["stage"]] = {
            "status": row.get("status", "pending"),
            "started_at": row.get("started_at"),
            "completed_at": row.get("completed_at"),
            "duration_ms": row.get("duration_ms"),
            "error_message": row.get("error_message"),
            "attempt_count": row.get("attempt_count", 0),
            "updated_at": row.get("updated_at"),
        }

    # Fill any missing stages with defaults (safety net)
    for stage in STAGES:
        if stage not in stages:
            stages[stage] = {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "duration_ms": None,
                "error_message": None,
                "attempt_count": 0,
                "updated_at": None,
            }

    return {
        "intake_id": intake_id,
        "stages": stages,
    }


def get_stage_status(intake_id: str, stage: str) -> str:
    """Return the status string for a single stage. Defaults to 'pending'."""
    if stage not in STAGES:
        raise ValueError(f"Invalid pipeline stage: {stage!r}")
    try:
        row = pipeline_repository.get_stage(intake_id, stage)
        if row:
            return row.get("status", "pending")
        return "pending"
    except Exception:
        return "pending"


def get_pipeline_status_flat(intake_id: str) -> dict[str, str]:
    """
    Return a flat {stage: status} dict for a single intake.

    This is the shape both the nurse workspace and queue expect:
        {"nlp": "completed", "risk": "running", "lab": "pending", ...}

    Reads via PipelineRepository (R1.2).
    """
    data = get_pipeline_status(intake_id)
    return {stage: info["status"] for stage, info in data["stages"].items()}


def get_batch_pipeline_status(intake_ids: list[str]) -> dict[str, dict[str, str]]:
    """
    Batch-fetch pipeline status for multiple intakes in a single query.

    Returns:
        {
            "intake-1": {"nlp": "completed", "risk": "pending", ...},
            "intake-2": {"nlp": "running",   "risk": "failed",  ...},
            ...
        }

    Intakes with no rows in pipeline_status get all-pending defaults.
    """
    if not intake_ids:
        return {}

    default = {s: "pending" for s in STAGES}

    try:
        rows = pipeline_repository.get_batch_status(intake_ids)
    except Exception as exc:
        try:
            logger.warning("[PRATHAM/PIPELINE] Retrying get_batch_pipeline_status after transient error: %s", exc)
            rows = pipeline_repository.get_batch_status(intake_ids)
        except Exception as retry_exc:
            logger.error("[PRATHAM/PIPELINE] get_batch_pipeline_status failed: %s", retry_exc)
            # Graceful fallback — return all-pending for every intake
            return {iid: dict(default) for iid in intake_ids}

    # Build lookup
    out: dict[str, dict[str, str]] = {iid: dict(default) for iid in intake_ids}
    for row in rows:
        iid = row.get("intake_id")
        stage = row.get("stage")
        if iid in out and stage in default:
            out[iid][stage] = row.get("status", "pending")

    return out
