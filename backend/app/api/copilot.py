"""
PRATHAM FastAPI Router — Role-scoped Clinical Copilot API.
Requires a signed-in user; what the copilot can see depends on that user's role.
"""

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import AuthUser, get_current_user
from app.services.copilot.copilot_orchestrator import run_copilot_query
from app.services.copilot.session_memory import get_or_create_session

router = APIRouter()


class CopilotQueryRequest(BaseModel):
    query: str = Field(..., max_length=2000, description="Natural-language question")
    session_id: Optional[str] = Field("default", max_length=100)
    intake_id: Optional[str] = Field(None, description="Intake UUID or case id (PRA-…) of the selected patient")
    mode: Optional[str] = Field("CLINICAL", description="Kept for UI compatibility")


@router.post("/query", summary="Ask the Copilot")
async def copilot_query_endpoint(req: CopilotQueryRequest, user: AuthUser = Depends(get_current_user)) -> Dict[str, Any]:
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        # Supabase + Groq calls are blocking; keep them off the event loop.
        return await asyncio.to_thread(
            run_copilot_query,
            query=req.query,
            user=user,
            session_id=req.session_id or "default",
            intake_id=req.intake_id,
            mode=req.mode or "CLINICAL",
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Copilot query failed")


@router.get("/history/{session_id}", summary="This user's history for a session")
async def copilot_session_history_endpoint(session_id: str, user: AuthUser = Depends(get_current_user)) -> Dict[str, Any]:
    return get_or_create_session(user.id, session_id)
