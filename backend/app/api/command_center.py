"""
command_center.py — Emergency Department Command Center Router
"""

from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter
from app.services.command_center_service import get_command_center_telemetry

router = APIRouter(prefix="/command-center", tags=["Command Center"])


@router.get("/telemetry")
async def get_telemetry() -> Dict[str, Any]:
    """Returns live ED telemetry, active cases count, and priority queue board."""
    return get_command_center_telemetry()
