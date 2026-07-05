"""
PRATHAM FastAPI Router — Evidence-Aware Clinical & System Copilot API
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.copilot.copilot_orchestrator import run_copilot_query
from app.services.copilot.session_memory import get_or_create_session

router = APIRouter()


class CopilotQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question from clinician or system admin")
    session_id: Optional[str] = Field("SESSION-DEFAULT", description="Session tracking ID")
    intake_id: Optional[str] = Field("INT-100", description="Emergency intake ID")
    mode: Optional[str] = Field("CLINICAL", description="CLINICAL or SYSTEM assistant mode")
    patient_data: Optional[Dict[str, Any]] = Field(None, description="Optional inline patient profile")


@router.post("/query", summary="Execute Copilot Clinical / System Query")
async def copilot_query_endpoint(req: CopilotQueryRequest) -> Dict[str, Any]:
    """Execute query through Copilot 4-tier pipeline and return Structured Response Object."""
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        response = run_copilot_query(
            query=req.query,
            session_id=req.session_id or "SESSION-DEFAULT",
            intake_id=req.intake_id or "INT-100",
            mode=req.mode or "CLINICAL",
            patient_data=req.patient_data,
        )
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Copilot query failed: {exc}")


@router.get("/history/{session_id}", summary="Get Copilot Session History")
async def copilot_session_history_endpoint(session_id: str) -> Dict[str, Any]:
    """Retrieve session memory history."""
    session = get_or_create_session(session_id)
    return session
