"""
PRATHAM Copilot — server-side session memory.

Sessions are namespaced by user id, so one user can never read or continue
another user's conversation, even by guessing the session id.
"""

from __future__ import annotations

from typing import Any, Dict, List

MAX_TURNS_KEPT = 20
MAX_SESSIONS = 500

_SESSION_CACHE: Dict[str, Dict[str, Any]] = {}


def _key(user_id: str, session_id: str) -> str:
    return f"{user_id}::{session_id}"


def get_or_create_session(user_id: str, session_id: str, intake_id: str = "") -> Dict[str, Any]:
    k = _key(user_id, session_id)
    if k not in _SESSION_CACHE:
        if len(_SESSION_CACHE) >= MAX_SESSIONS:
            _SESSION_CACHE.pop(next(iter(_SESSION_CACHE)))
        _SESSION_CACHE[k] = {"session_id": session_id, "intake_id": intake_id, "history": []}
    return _SESSION_CACHE[k]


def recent_turns(user_id: str, session_id: str, n: int = 6) -> List[Dict[str, str]]:
    """Last n turns as [{'query','answer'}] — used to resolve follow-up questions."""
    session = _SESSION_CACHE.get(_key(user_id, session_id))
    return session["history"][-n:] if session else []


def update_session_history(user_id: str, session_id: str, intake_id: str, query: str, answer: str) -> None:
    session = get_or_create_session(user_id, session_id, intake_id)
    session["intake_id"] = intake_id
    session["history"].append({"query": query, "answer": answer[:600]})
    del session["history"][:-MAX_TURNS_KEPT]


def clear_sessions() -> None:
    _SESSION_CACHE.clear()
