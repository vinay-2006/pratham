"""
POST /api/imaging/analyze  — EfficientNetB0 pneumonia inference endpoint.
GET  /api/imaging/results/{intake_id} — Retrieve latest imaging result.

Workflow:
  1. Receive intake_id + evidence_id.
  2. Fetch the evidence record from DB to get the image storage path.
  3. Download the image from Supabase Storage to a temp file.
  4. Run EfficientNetB0 prediction (raw pixels — no normalisation).
  5. Persist result to imaging_results table.
  6. Return structured JSON response.
"""

from __future__ import annotations

import logging
import os
import tempfile
import uuid as _uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.supabase_client import supabase
from app.ml.imaging_model import run_imaging_inference, generate_gradcam, MODEL_NAME

logger = logging.getLogger(__name__)
router = APIRouter()

BUCKET = "evidence"


# ── Request / Response models ─────────────────────────────────────────────

class ImagingAnalyzeRequest(BaseModel):
    intake_id: str = Field(..., description="UUID of the emergency_intake row.")
    evidence_id: str = Field(..., description="UUID of the evidence row containing the chest X-ray.")


class ImagingAnalyzeResponse(BaseModel):
    imaging_result_id: str
    intake_id: str
    evidence_id: str
    model_name: str
    prediction: str
    pneumonia_probability: float
    confidence: float
    created_at: str


# ── Helpers ───────────────────────────────────────────────────────────────

def _fetch_evidence_record(evidence_id: str) -> dict:
    """Fetch a single evidence row by ID. Raises HTTPException on not-found."""
    try:
        res = (
            supabase.table("evidence")
            .select("id, intake_id, evidence_type, file_url, file_name")
            .eq("id", evidence_id)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error fetching evidence: {exc}")

    if not res.data:
        raise HTTPException(status_code=404, detail=f"Evidence {evidence_id!r} not found.")
    return res.data[0]


def _resolve_storage_path(evidence_row: dict) -> str:
    """
    Derive the Supabase Storage path for the evidence file.

    The evidence upload endpoint stores files at:
        {intake_id}/{evidence_type}_{uuid}.{ext}

    We reconstruct this from the file_url or fall back to a query.
    """
    file_url = evidence_row.get("file_url", "") or ""

    # The storage path is embedded in the signed URL after /object/sign/evidence/
    # e.g.  ...supabase.co/storage/v1/object/sign/evidence/{intake_id}/xray_{uuid}.jpg?token=...
    if "/evidence/" in file_url:
        # Extract path after /evidence/
        path_part = file_url.split("/evidence/", 1)[-1]
        # Remove query params
        if "?" in path_part:
            path_part = path_part.split("?", 1)[0]
        if path_part:
            return path_part

    # Fallback: construct from known naming convention
    intake_id = evidence_row.get("intake_id", "")
    file_name = evidence_row.get("file_name", "")
    evidence_type = evidence_row.get("evidence_type", "xray")

    if file_name:
        return f"{intake_id}/{file_name}"

    raise HTTPException(
        status_code=500,
        detail=f"Cannot resolve storage path for evidence {evidence_row.get('id')}",
    )


def _download_image_to_temp(storage_path: str) -> str:
    """
    Download an image from Supabase Storage to a temporary file.
    Returns the absolute path to the temp file.
    """
    try:
        file_bytes = supabase.storage.from_(BUCKET).download(storage_path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download image from storage ({storage_path}): {exc}",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=500,
            detail=f"Downloaded empty file from storage ({storage_path}).",
        )

    # Determine extension from storage path
    ext = ".jpg"
    if storage_path.lower().endswith(".png"):
        ext = ".png"

    # Write to a temp file
    fd, temp_path = tempfile.mkstemp(suffix=ext, prefix="pratham_xray_")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(file_bytes)
    except Exception:
        os.close(fd)
        raise

    return temp_path


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.post(
    "/imaging/analyze",
    response_model=ImagingAnalyzeResponse,
    tags=["Imaging Analysis"],
    summary="EfficientNetB0 pneumonia inference from chest X-ray",
)
async def imaging_analyze(body: ImagingAnalyzeRequest) -> ImagingAnalyzeResponse:
    """
    Run the EfficientNetB0 pneumonia classification model on a chest X-ray
    identified by evidence_id.

    The image is downloaded from Supabase Storage, run through the model,
    and the result is persisted to the `imaging_results` table.
    """
    from app.services.pipeline_status_service import mark_running, mark_completed, mark_failed

    intake_id = body.intake_id
    evidence_id = body.evidence_id

    mark_running(intake_id, "imaging")

    try:
        # 1. Verify intake exists
        try:
            intake_res = (
                supabase.table("emergency_intake")
                .select("id")
                .eq("id", intake_id)
                .limit(1)
                .execute()
            )
            if not intake_res.data:
                raise HTTPException(status_code=404, detail=f"Intake {intake_id!r} not found.")
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Database error: {exc}")

        # 2. Fetch evidence record
        evidence_row = _fetch_evidence_record(evidence_id)

        # 3. Download image from Supabase Storage
        storage_path = _resolve_storage_path(evidence_row)
        temp_path = _download_image_to_temp(storage_path)

        # 4. Run EfficientNetB0 inference
        try:
            result = run_imaging_inference(temp_path)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        except Exception as exc:
            logger.error("[PRATHAM/ML] Imaging inference failed: %s", exc)
            raise HTTPException(status_code=500, detail=f"Inference error: {exc}")
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except OSError:
                pass

        # 5. Generate Grad-CAM heatmap (non-fatal if it fails)
        gradcam_url = ""
        try:
            gradcam_temp = temp_path.replace(".jpg", "_gradcam.png").replace(".jpeg", "_gradcam.png")
            if gradcam_temp == temp_path:  # edge case
                gradcam_temp = temp_path + "_gradcam.png"
            # Re-download image since temp_path may have been cleaned up
            temp_path_gc = _download_image_to_temp(storage_path)
            gradcam_local = generate_gradcam(temp_path_gc, gradcam_temp)
            if gradcam_local:
                # Upload to Supabase Storage
                gc_storage_path = f"{intake_id}/gradcam_{_uuid.uuid4()}.png"
                with open(gradcam_local, "rb") as gc_file:
                    supabase.storage.from_(BUCKET).upload(
                        path=gc_storage_path,
                        file=gc_file.read(),
                        file_options={"content-type": "image/png", "upsert": "false"},
                    )
                # Generate signed URL
                signed = supabase.storage.from_(BUCKET).create_signed_url(
                    gc_storage_path, 7 * 24 * 60 * 60
                )
                gradcam_url = signed.get("signedURL") or signed.get("signed_url") or ""
                logger.info("[PRATHAM/ML] Grad-CAM uploaded: %s", gc_storage_path)
            # Cleanup temp files
            for f in (temp_path_gc, gradcam_temp, gradcam_local):
                try:
                    if f and os.path.exists(f):
                        os.unlink(f)
                except OSError:
                    pass
        except Exception as gc_err:
            logger.warning("[PRATHAM/ML] Grad-CAM pipeline failed (non-fatal): %s", gc_err)

        # 6. Persist to imaging_results
        now = datetime.now(timezone.utc).isoformat()
        db_row = {
            "intake_id": intake_id,
            "evidence_id": evidence_id,
            "model_name": MODEL_NAME,
            "prediction": result["prediction"],
            "pneumonia_probability": result["pneumonia_probability"],
            "confidence": result["confidence"],
            "created_at": now,
        }
        if gradcam_url:
            db_row["gradcam_url"] = gradcam_url

        imaging_result_id = ""
        try:
            insert_res = supabase.table("imaging_results").insert(db_row).execute()
            if insert_res.data:
                imaging_result_id = insert_res.data[0].get("id", "")
            logger.info(
                "[PRATHAM/ML] imaging_results row inserted: id=%s intake=%s prediction=%s prob=%.4f",
                imaging_result_id, intake_id, result["prediction"], result["pneumonia_probability"],
            )
        except Exception as db_exc:
            # Non-fatal: still return the prediction even if DB write fails
            logger.error("[PRATHAM/ML] imaging_results insert failed (non-fatal): %s", db_exc)

        mark_completed(intake_id, "imaging")

        # 7. Return response
        return ImagingAnalyzeResponse(
            imaging_result_id=imaging_result_id,
            intake_id=intake_id,
            evidence_id=evidence_id,
            model_name=MODEL_NAME,
            prediction=result["prediction"],
            pneumonia_probability=result["pneumonia_probability"],
            confidence=result["confidence"],
            created_at=now,
        )

    except Exception as exc:
        # Mark failed then re-raise (mark_failed re-raises automatically)
        mark_failed(intake_id, "imaging", exc)


@router.get(
    "/imaging/results/{intake_id}",
    tags=["Imaging Analysis"],
    summary="Fetch latest imaging analysis result for an intake",
)
async def get_imaging_results(intake_id: str):
    """
    Return the latest imaging_results row for the given intake_id.
    """
    try:
        res = (
            supabase.table("imaging_results")
            .select("id, intake_id, evidence_id, model_name, prediction, pneumonia_probability, confidence, created_at")
            .eq("intake_id", intake_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No imaging results found for intake {intake_id!r}.",
            )

        latest = rows[0]
        return {
            "imaging_result_id": latest.get("id"),
            "intake_id": latest.get("intake_id"),
            "evidence_id": latest.get("evidence_id"),
            "model_name": latest.get("model_name"),
            "prediction": latest.get("prediction"),
            "pneumonia_probability": latest.get("pneumonia_probability"),
            "confidence": latest.get("confidence"),
            "created_at": latest.get("created_at"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
