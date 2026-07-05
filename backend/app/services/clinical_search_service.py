"""
clinical_search_service.py — Clinical Record & Diagnosis Search Engine

Searches patient records by symptoms, chief complaints, diagnostic findings, or lab analytes.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List
from app.db.supabase_client import supabase

logger = logging.getLogger(__name__)


def search_clinical_records(query: str) -> List[Dict[str, Any]]:
    """
    Searches patient intakes matching a query string across chief complaint, description, and severity.
    """
    if not query or not query.strip():
        return []

    q = query.strip().lower()
    results: List[Dict[str, Any]] = []

    try:
        res = (
            supabase.table("emergency_intake")
            .select("id, chief_complaint, emergency_description, severity_level, created_at, patients(first_name, last_name)")
            .or_(f"chief_complaint.ilike.%{q}%,emergency_description.ilike.%{q}%")
            .limit(20)
            .execute()
        )
        data = res.data or []

        for item in data:
            p_name = "Unknown"
            p_row = item.get("patients")
            if p_row:
                p_name = f"{p_row.get('first_name', '')} {p_row.get('last_name', '')}".strip()

            results.append({
                "intake_id": item["id"],
                "patient_name": p_name,
                "chief_complaint": item.get("chief_complaint", "General evaluation"),
                "severity": item.get("severity_level", "moderate"),
                "arrival_time": str(item.get("created_at"))[:10] if item.get("created_at") else "Recent",
                "matched_query": q,
            })
    except Exception as exc:
        logger.warning("[Clinical Search Engine] Search query failed: %s", exc)

    return results
