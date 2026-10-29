"""
Evidence Upload API
POST /api/evidence/upload      — Upload file → Supabase Storage + evidence table
GET  /api/evidence/{intake_id} — List all evidence rows for an intake

INVESTIGATION_EVIDENCE_MAP lives here so the backend is the single source of truth
for how investigation types map to evidence categories.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

import logging
from app.db.supabase_client import supabase
from app.domains.evidence.repository import evidence_repository
from app.domains.ai.repository import (
    imaging_results_repository,
    lab_results_repository,
    aggregation_results_repository,
)
from app.services.workflow_service import update_status_on_evidence_upload

logger = logging.getLogger(__name__)
router = APIRouter()

VALID_EVIDENCE_TYPES = {"xray", "lab_report", "ecg", "clinical_notes"}
BUCKET = "evidence"
SIGNED_URL_EXPIRY = 7 * 24 * 60 * 60  # 7 days in seconds

# ── Investigation → Evidence type mapping ──────────────────────────────────────
# Imported from shared utility — single source of truth lives in
# app/domains/shared/utils/evidence_mapping.py (P5 — Phase 3.1).
# Re-exported here so callers that import from this module are unaffected.
from app.domains.shared.utils.evidence_mapping import (  # noqa: E402
    INVESTIGATION_EVIDENCE_MAP,
    get_evidence_type,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_extension(filename: str, content_type: str) -> str:
    """Derive a safe file extension from filename or MIME type."""
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in {"jpg", "jpeg", "png", "pdf", "txt"}:
            return ext
    mime_map = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "application/pdf": "pdf",
        "text/plain": "txt",
    }
    return mime_map.get(content_type or "", "bin")


def _insert_evidence_row(payload: dict) -> dict:
    """
    Insert an evidence row.
    Gracefully falls back without 'investigation_id' if the column
    has not been added to the table yet (PGRST204 error).
    """
    return evidence_repository.create_with_fallback(payload)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/evidence/upload", tags=["Evidence Upload"])
async def upload_evidence(
    intake_id: str = Form(..., description="UUID of the emergency intake"),
    evidence_type: str = Form(
        ..., description="One of: xray, lab_report, ecg, clinical_notes"
    ),
    investigation_id: str = Form(
        default="",
        description="UUID of the investigation_recommendations row (optional but strongly recommended)",
    ),
    file: UploadFile = File(..., description="File (JPEG/PNG/PDF/TXT ≤ 10 MB)"),
):
    """
    Upload a clinical evidence file to Supabase Storage.

    Workflow:
    1. Validate evidence_type
    2. Generate storage path: {intake_id}/{evidence_type}_{uuid}.{ext}
    3. Upload to private 'evidence' bucket
    4. Generate 7-day signed URL
    5. Insert row in evidence table (with investigation_id if provided)
    6. Return evidence metadata
    """
    # 1. Validate evidence_type
    if evidence_type not in VALID_EVIDENCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid evidence_type '{evidence_type}'. "
                f"Must be one of: {', '.join(sorted(VALID_EVIDENCE_TYPES))}"
            ),
        )

    # 2. Read & size-check file
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > 10:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum is 10 MB.",
        )

    # 3. Generate storage path
    file_uuid = str(uuid.uuid4())
    ext = _get_extension(file.filename or "", file.content_type or "")
    storage_path = f"{intake_id}/{evidence_type}_{file_uuid}.{ext}"
    original_name = file.filename or f"{evidence_type}_{file_uuid}.{ext}"

    # 4. Upload to Supabase Storage
    try:
        supabase.storage.from_(BUCKET).upload(
            path=storage_path,
            file=content,
            file_options={
                "content-type": file.content_type or "application/octet-stream",
                "upsert": "false",
            },
        )
    except Exception as upload_err:
        raise HTTPException(
            status_code=500,
            detail=f"Storage upload failed: {upload_err}",
        )

    # 5. Generate 7-day signed URL
    file_url = ""
    try:
        signed = supabase.storage.from_(BUCKET).create_signed_url(
            storage_path, SIGNED_URL_EXPIRY
        )
        file_url = signed.get("signedURL") or signed.get("signed_url") or ""
    except Exception as sign_err:
        logger.warning("[PRATHAM] Warning: Could not generate signed URL: %s", sign_err)

    # 6. Insert row into evidence table
    insert_payload: dict = {
        "intake_id": intake_id,
        "evidence_type": evidence_type,
        "file_url": file_url,
        "file_name": original_name,
    }
    if investigation_id and investigation_id.strip():
        insert_payload["investigation_id"] = investigation_id.strip()

    try:
        evidence_row = _insert_evidence_row(insert_payload)
        evidence_id = evidence_row.get("id")
        update_status_on_evidence_upload(intake_id)
        # Invalidate cached report since evidence has changed
        from app.services.report_service import invalidate_report_cache
        invalidate_report_cache(intake_id)
    except Exception as db_err:
        # Best-effort: remove uploaded file if DB insert fails
        try:
            supabase.storage.from_(BUCKET).remove([storage_path])
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Database insert failed: {db_err}",
        )

    # 7. Return metadata
    return {
        "evidence_id": evidence_id,
        "intake_id": intake_id,
        "evidence_type": evidence_type,
        "investigation_id": investigation_id or None,
        "file_name": original_name,
        "file_url": file_url,
        "storage_path": storage_path,
    }


@router.get("/evidence/{intake_id}", tags=["Evidence Upload"])
async def get_evidence(intake_id: str):
    """
    Retrieve all uploaded evidence for a given intake.
    Returns evidence rows ordered newest-first.
    """
    try:
        # Try with investigation_id column first; fall back if column doesn't exist
        try:
            rows = evidence_repository.get_by_intake_id_with_columns(
                intake_id,
                columns="id, intake_id, evidence_type, file_url, file_name, uploaded_at, investigation_id",
                order_by="uploaded_at",
                desc=True,
            )
        except Exception:
            rows = evidence_repository.get_by_intake_id_with_columns(
                intake_id,
                columns="id, intake_id, evidence_type, file_url, file_name, uploaded_at",
                order_by="uploaded_at",
                desc=True,
            )


        return {
            "intake_id": intake_id,
            "count": len(rows),
            "evidence": [
                {
                    "evidence_id": row.get("id"),
                    "intake_id": row.get("intake_id"),
                    "evidence_type": row.get("evidence_type"),
                    "investigation_id": row.get("investigation_id"),
                    "file_name": row.get("file_name"),
                    "file_url": row.get("file_url", ""),
                    "uploaded_at": row.get("uploaded_at"),
                }
                for row in rows
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evidence-map", tags=["Evidence Upload"])
async def get_evidence_map():
    """
    Returns the investigation_type → evidence_type mapping as JSON.
    Frontend uses this to display expected evidence categories.
    Backend is the single source of truth for this mapping.
    """
    return {
        "map": INVESTIGATION_EVIDENCE_MAP,
        "valid_evidence_types": sorted(VALID_EVIDENCE_TYPES),
    }


def cleanup_ai_results(intake_id: str, evidence_type: str, evidence_id: str):
    """
    Cascade delete AI analysis results when evidence is removed.
    
    1. Checks if other evidence of the same type still exists for the intake.
    2. If no other evidence of that type exists, deletes corresponding results in
       imaging_results (for xray) or lab_results (for lab_report).
    3. Always invalidates aggregation_results for the intake since inputs changed.
    4. Resets corresponding pipeline_status stages back to 'pending'.
    """
    from app.services.pipeline_status_service import reset_stage

    if not intake_id:
        return

    try:
        # Check if other evidence of same type still exists for the intake
        all_of_type = evidence_repository.get_by_intake_id_and_type(intake_id, evidence_type)
        other_evidence = [r for r in all_of_type if r.get("id") != evidence_id]
        
        if not other_evidence:
            # Delete corresponding AI results and reset pipeline stage
            if evidence_type == "xray":
                logger.info("[PRATHAM] Cleaning up imaging results for intake %s (no remaining xrays)", intake_id)
                imaging_results_repository.delete_by_intake_id(intake_id)
                reset_stage(intake_id, "imaging")
            elif evidence_type == "lab_report":
                logger.info("[PRATHAM] Cleaning up lab results for intake %s (no remaining lab reports)", intake_id)
                lab_results_repository.delete_by_intake_id(intake_id)
                reset_stage(intake_id, "lab")
                
        # Always invalidate aggregation_results and reset aggregation pipeline
        logger.info("[PRATHAM] Invalidating aggregation results for intake %s", intake_id)
        aggregation_results_repository.delete_by_intake_id(intake_id)
        reset_stage(intake_id, "aggregation")
    except Exception as exc:
        logger.warning("[PRATHAM] Error during AI results cleanup: %s", exc)


@router.delete("/evidence/{evidence_id}", tags=["Evidence Upload"], status_code=204)
async def delete_evidence(evidence_id: str):
    """
    Delete a single evidence file.

    1. Fetch the evidence row to get storage path info.
    2. Remove the file from Supabase Storage.
    3. Clean up any related AI results and aggregation results.
    4. Delete the evidence row from the DB.
    5. Return 204 No Content.
    """
    # 1. Fetch existing row
    try:
        row = evidence_repository.get_by_id_with_columns(
            evidence_id,
            columns="id, intake_id, evidence_type, file_url, file_name",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"DB error fetching evidence: {exc}")

    if not row:
        raise HTTPException(status_code=404, detail=f"Evidence {evidence_id!r} not found.")



    # 2. Resolve storage path from file_url and remove from storage
    file_url = row.get("file_url", "") or ""
    storage_path = ""
    if "/evidence/" in file_url:
        path_part = file_url.split("/evidence/", 1)[-1]
        if "?" in path_part:
            path_part = path_part.split("?", 1)[0]
        storage_path = path_part

    if not storage_path:
        # Fallback: reconstruct from naming convention
        intake_id = row.get("intake_id", "")
        file_name = row.get("file_name", "")
        ev_type = row.get("evidence_type", "")
        if intake_id and file_name:
            storage_path = f"{intake_id}/{file_name}"

    if storage_path:
        try:
            rm_res = supabase.storage.from_(BUCKET).remove([storage_path])
            logger.info("[PRATHAM] Storage delete storage_path=%r res=%r", storage_path, rm_res)
        except Exception as rm_err:
            logger.warning("[PRATHAM] Storage delete warning (non-fatal): %s", rm_err)

    # 3. Clean up downstream AI results and invalidate aggregation
    intake_id = row.get("intake_id", "")
    evidence_type = row.get("evidence_type", "")
    if intake_id and evidence_type:
        cleanup_ai_results(intake_id, evidence_type, evidence_id)

    # 4. Delete the DB row
    try:
        evidence_repository.delete(evidence_id)
    except Exception as db_err:
        raise HTTPException(status_code=500, detail=f"DB delete failed: {db_err}")

    # 5. Invalidate cached report since evidence has changed
    if intake_id:
        from app.services.report_service import invalidate_report_cache
        invalidate_report_cache(intake_id)

    # 6. Return 204
    return None
