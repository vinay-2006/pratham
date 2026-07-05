"""
GET /api/report/{intake_id}     — Consolidated Clinical Intelligence Report (JSON)
GET /api/report/{intake_id}/pdf — PDF export of the same report

Both endpoints use report_service.get_complete_report() as the
single source of truth.  The PDF endpoint never re-queries the database.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.services.report_service import get_complete_report
from app.services.pdf_generator import generate_pdf

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/report/{intake_id}", tags=["Clinical Report"])
async def get_clinical_report(intake_id: str):
    """
    Consolidated Clinical Intelligence Report (JSON).
    Returns all data needed for the doctor's full-page report in a single call.
    """
    try:
        return await get_complete_report(intake_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[PRATHAM] Report endpoint error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{intake_id}/pdf", tags=["Clinical Report"])
async def get_clinical_report_pdf(intake_id: str):
    """
    PDF export of the Clinical Intelligence Report.
    Uses the same data source as the JSON endpoint.
    """
    try:
        report = await get_complete_report(intake_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("[PRATHAM] Report PDF - data fetch error: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch report data: {e}")

    try:
        pdf_bytes = generate_pdf(report)
    except Exception as e:
        logger.error("[PRATHAM] Report PDF - generation error: %s", e)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    # Build filename: pratham_report_Ravi_Kumar_2026-07-04.pdf
    patient_name = report.get("patient_summary", {}).get("name", "patient")
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", patient_name).strip("_")
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"pratham_report_{safe_name}_{date_str}.pdf"

    import io
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
