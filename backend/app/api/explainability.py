"""
explainability.py — Diagnostic Explainability Router
"""

from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter
from app.services.explainability_service import build_explainability_tree
from app.services.report_service import get_complete_report

router = APIRouter(prefix="/explainability", tags=["Explainability"])


@router.get("/tree/{intake_id}")
async def get_explainability_tree(intake_id: str) -> Dict[str, Any]:
    """Returns interactive evidence tree and subsystem agreement breakdown for an intake."""
    try:
        report_data = await get_complete_report(intake_id)
        return build_explainability_tree(report_data)
    except Exception:
        # Demo fallback tree
        return build_explainability_tree({})
