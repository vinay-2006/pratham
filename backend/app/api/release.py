"""
PRATHAM Release Version API Router
Exposes project release tags and metadata.
"""

from fastapi import APIRouter
from typing import Dict

router = APIRouter()

@router.get("", summary="Get Platform Release Information")
async def get_release_info() -> Dict[str, str]:
    """Return platform metadata release parameters."""
    return {
        "project": "PRATHAM",
        "version": "5.0.0",
        "build_date": "2026-07-05",
        "git_commit": "c5f08bd",
        "branch": "feature/copilot",
        "release_status": "Stable",
        "copyright": "© 2026 PRATHAM Medical AI"
    }
