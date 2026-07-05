"""
longitudinal_history_service.py — Longitudinal Patient History Engine

Aggregates multi-visit patient records from Supabase and performs trajectory analysis.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List
from app.db.supabase_client import supabase
from app.services.trend_analysis_service import analyze_longitudinal_trends

logger = logging.getLogger(__name__)


async def get_patient_longitudinal_history(patient_id: str) -> Dict[str, Any]:
    """
    Fetches all historical visits, vitals, risk scores, and trend trajectories for a given patient_id.
    """
    try:
        intake_res = (
            supabase.table("emergency_intake")
            .select("id, status, created_at, severity_level, chief_complaint, emergency_description")
            .eq("patient_id", patient_id)
            .order("created_at", asc=True)
            .execute()
        )
        visits = intake_res.data or []
    except Exception as exc:
        logger.warning("[Longitudinal Engine] Failed to fetch intakes: %s", exc)
        visits = []

    visit_details: List[Dict[str, Any]] = []

    for v in visits:
        iid = v["id"]
        vitals_res = supabase.table("vitals").select("*").eq("intake_id", iid).limit(1).execute()
        risk_res = supabase.table("risk_scores").select("*").eq("intake_id", iid).limit(1).execute()

        vitals_row = vitals_res.data[0] if vitals_res.data else {}
        risk_row = risk_res.data[0] if risk_res.data else {}

        visit_details.append({
            "intake_id": iid,
            "created_at": v.get("created_at"),
            "chief_complaint": v.get("chief_complaint", ""),
            "severity": v.get("severity_level", "moderate"),
            "vitals": vitals_row,
            "risk_scores": risk_row,
        })

    trend_results = analyze_longitudinal_trends(visit_details)

    return {
        "patient_id": patient_id,
        "total_visits": len(visit_details),
        "visit_history": visit_details,
        "longitudinal_trends": trend_results,
    }
