"""
GET /api/pipeline/status/{intake_id} — Pipeline Status API

Returns the execution state of all 5 AI subsystems for a given intake.
This is the single endpoint used by both Nurse Workspace and Doctor Report
to display live pipeline progress.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.pipeline_status_service import get_pipeline_status

router = APIRouter()


@router.get(
    "/pipeline/status/{intake_id}",
    tags=["Pipeline"],
    summary="Get pipeline execution status for an intake",
)
async def pipeline_status(intake_id: str):
    """
    Return the current execution state of all 5 AI pipeline stages.

    Response shape:
    {
        "intake_id": "...",
        "stages": {
            "nlp":         { "status": "completed", "started_at": ..., "completed_at": ..., "duration_ms": 2145, "error_message": null, "attempt_count": 1 },
            "risk":        { ... },
            "lab":         { ... },
            "imaging":     { ... },
            "aggregation": { ... }
        }
    }
    """
    try:
        result = get_pipeline_status(intake_id)

        # If no stages were found at all, the intake may not exist
        all_empty = all(
            s.get("updated_at") is None
            for s in result["stages"].values()
        )
        if all_empty:
            # Verify intake exists
            from app.domains.triage.repository import intake_repository
            intake_check = intake_repository.get_by_id(intake_id, columns="id")
            if not intake_check:
                raise HTTPException(
                    status_code=404,
                    detail=f"Intake {intake_id!r} not found.",
                )

        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
