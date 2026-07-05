"""
search.py — Clinical Record Search Router
"""

from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Query
from app.services.clinical_search_service import search_clinical_records

router = APIRouter(tags=["Clinical Search"])


@router.get("/search")
async def search_records(q: str = Query("", description="Search term")) -> Dict[str, Any]:
    """Search patient intake records by symptom, chief complaint, or diagnosis keyword."""
    results = search_clinical_records(q)
    return {
        "query": q,
        "total_results": len(results),
        "results": results,
    }
