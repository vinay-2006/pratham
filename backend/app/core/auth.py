"""
PRATHAM — Authentication & role-based access control.

Identity comes from Supabase Auth. The caller sends the Supabase access token
as ``Authorization: Bearer <jwt>``. The role (nurse | doctor | admin) lives in
the user's ``app_metadata.role`` (only writable with the service-role key, so
users cannot promote themselves).

A single dependency, ``authorize``, is attached to every protected router and
consults ``ACCESS_RULES`` — the one place that says which role may call what.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

from fastapi import Depends, HTTPException, Request

VALID_ROLES = ("nurse", "doctor", "admin")

# token -> (expires_at_monotonic, AuthUser). Avoids a Supabase round-trip per request.
_TOKEN_CACHE: Dict[str, Tuple[float, "AuthUser"]] = {}
_TOKEN_TTL_SECONDS = 60


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str
    role: str
    name: str
    department: str = ""

    def public(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "name": self.name,
            "department": self.department,
        }


# (method or "*", path prefix, allowed roles). First match wins, so list the
# most specific rules first. Anything not matched just needs a valid login.
ALL_STAFF = ("nurse", "doctor", "admin")
ACCESS_RULES: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    # Doctor-only clinical decisions
    ("POST", "/api/investigations/approve", ("doctor",)),
    ("POST", "/api/investigations/reject", ("doctor",)),
    ("POST", "/api/investigations/needs-info", ("doctor",)),
    ("POST", "/api/investigations/return-to-nurse", ("doctor",)),
    ("POST", "/api/investigations/recommend", ("doctor",)),
    ("POST", "/api/investigations/update", ("doctor",)),
    ("POST", "/api/report/", ("doctor",)),  # mark-reviewed
    ("*", "/api/doctor/", ("doctor",)),
    ("*", "/api/report/", ("doctor",)),
    ("*", "/api/explainability", ("doctor",)),
    ("*", "/api/aggregate", ("doctor",)),
    ("*", "/api/aggregation", ("doctor",)),
    ("GET", "/api/lab/results", ("doctor",)),
    ("GET", "/api/imaging/results", ("doctor",)),
    # Nurse intake workflow
    ("POST", "/api/intake/arrival/confirm", ("nurse",)),
    ("POST", "/api/intake/", ("nurse", "doctor")),
    ("POST", "/api/intake", ("nurse", "doctor")),
    ("POST", "/api/investigations/add", ("nurse", "doctor")),
    # Patient-level data: clinical staff only (admins see aggregates, never patients)
    ("*", "/api/investigations", ("nurse", "doctor")),
    ("*", "/api/search", ("nurse", "doctor")),
    ("*", "/api/evidence", ("nurse", "doctor")),
    ("*", "/api/intake", ("nurse", "doctor")),
    ("*", "/api/lab", ("nurse", "doctor")),
    ("*", "/api/imaging", ("nurse", "doctor")),
    ("*", "/evidence", ("nurse", "doctor")),
    ("*", "/nlp", ("nurse", "doctor")),
    ("*", "/risk", ("nurse", "doctor")),
    ("*", "/investigation", ("nurse", "doctor")),
    # Admin-only platform operations
    ("*", "/api/admin", ("admin",)),
    ("*", "/api/demo", ("admin",)),
    ("*", "/api/release", ("admin",)),
    ("*", "/api/platform-metrics", ("admin", "doctor")),
    # Everyone signed in
    ("*", "/api/copilot", ALL_STAFF),
)


def _user_from_supabase(token: str) -> AuthUser:
    from app.db.supabase_client import supabase  # lazy: keeps imports light for tests

    try:
        resp = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please sign in again.")
    user = getattr(resp, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please sign in again.")

    app_meta = user.app_metadata or {}
    user_meta = user.user_metadata or {}
    role = app_meta.get("role")  # trusted: only the service key can set app_metadata
    if role not in VALID_ROLES:
        raise HTTPException(status_code=403, detail="Your account has no clinical role assigned.")
    return AuthUser(
        id=user.id,
        email=user.email or "",
        role=role,
        name=user_meta.get("name") or (user.email or "").split("@")[0],
        department=user_meta.get("department", ""),
    )


def resolve_token(token: str) -> AuthUser:
    now = time.monotonic()
    cached = _TOKEN_CACHE.get(token)
    if cached and cached[0] > now:
        return cached[1]
    user = _user_from_supabase(token)
    if len(_TOKEN_CACHE) > 512:
        _TOKEN_CACHE.clear()
    _TOKEN_CACHE[token] = (now + _TOKEN_TTL_SECONDS, user)
    return user


def clear_token_cache() -> None:
    _TOKEN_CACHE.clear()


def _extract_token(request: Request) -> Optional[str]:
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return None


def allowed_roles_for(method: str, path: str) -> Optional[Iterable[str]]:
    for rule_method, prefix, roles in ACCESS_RULES:
        if rule_method in ("*", method) and path.startswith(prefix):
            return roles
    return None


def get_current_user(request: Request) -> AuthUser:
    """Resolve the caller or raise 401. Result is also stored on request.state."""
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user = resolve_token(token)
    request.state.user = user
    return user


def authorize(request: Request) -> Optional[AuthUser]:
    """Router-level dependency: must be signed in AND allowed by ACCESS_RULES."""
    if request.method == "OPTIONS":
        return None
    user = get_current_user(request)
    roles = allowed_roles_for(request.method, request.url.path)
    if roles is not None and user.role not in roles:
        raise HTTPException(
            status_code=403,
            detail=f"Your role ({user.role}) is not permitted to perform this action.",
        )
    return user


def require_roles(*roles: str):
    """Per-endpoint guard for cases the central table does not cover."""

    def _dep(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires role: {', '.join(roles)}.")
        return user

    return _dep
