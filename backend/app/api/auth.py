"""PRATHAM — Login / session endpoints backed by Supabase Auth."""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import create_client

from app.core.auth import VALID_ROLES, AuthUser, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str


def _anon_client():
    # A fresh client per call: sign-in mutates client session state and must never
    # touch the shared service-role singleton.
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])


def _session_payload(session, user) -> dict:
    role = (user.app_metadata or {}).get("role")
    if role not in VALID_ROLES:
        raise HTTPException(status_code=403, detail="Your account has no clinical role assigned.")
    meta = user.user_metadata or {}
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expires_at": session.expires_at,
        "user": AuthUser(
            id=user.id,
            email=user.email or "",
            role=role,
            name=meta.get("name") or (user.email or "").split("@")[0],
            department=meta.get("department", ""),
        ).public(),
    }


def _raise_login_error(exc: Exception):
    """Wrong credentials → 401. Rate limits / outages must not masquerade as a bad password."""
    status = getattr(exc, "status", None) or getattr(exc, "code", None)
    msg = str(exc).lower()
    logger.warning("Supabase sign-in failed (%s): %s", status, exc)
    if status == 429 or "rate limit" in msg or "too many" in msg:
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Wait a minute and try again.")
    if "invalid login" in msg or "invalid_credentials" in msg or status in (400, 401, 422):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    raise HTTPException(status_code=503, detail="Sign-in service is temporarily unavailable. Please retry.")


@router.post("/login", summary="Sign in with email + password")
async def login(req: LoginRequest):
    try:
        res = _anon_client().auth.sign_in_with_password({"email": req.email.strip(), "password": req.password})
    except Exception as exc:
        _raise_login_error(exc)
    if not res.session or not res.user:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return _session_payload(res.session, res.user)


@router.post("/refresh", summary="Exchange a refresh token for a new session")
async def refresh(req: RefreshRequest):
    try:
        res = _anon_client().auth.refresh_session(req.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    if not res.session or not res.user:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    return _session_payload(res.session, res.user)


@router.get("/me", summary="Current signed-in user")
async def me(user: AuthUser = Depends(get_current_user)):
    return user.public()
