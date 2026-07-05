"""
PRATHAM Copilot — Server-Side Session Memory Engine
Maintains conversation state and active context mapping for follow-up resolution.
"""

from typing import Dict, Any, List

_SESSION_CACHE: Dict[str, Dict[str, Any]] = {}


def get_or_create_session(session_id: str, intake_id: str = "INT-100") -> Dict[str, Any]:
    """Retrieve or initialize server-side session memory."""
    if session_id not in _SESSION_CACHE:
        _SESSION_CACHE[session_id] = {
            "session_id": session_id,
            "intake_id": intake_id,
            "active_focus": "Community-Acquired Pneumonia",
            "history": [],
        }
    return _SESSION_CACHE[session_id]


def update_session_history(session_id: str, query: str, answer_obj: Dict[str, Any]) -> None:
    """Record query and structured response in session memory."""
    session = get_or_create_session(session_id)
    session["history"].append({
        "query": query,
        "answer_type": answer_obj.get("answer_type", "NARRATIVE"),
        "answer_summary": answer_obj.get("answer", "")[:100],
    })
    # Update active condition focus if mentioned
    ans_text = answer_obj.get("answer", "").lower()
    if "pneumon" in ans_text:
        session["active_focus"] = "Community-Acquired Pneumonia"
    elif "coronary" in ans_text or "acs" in ans_text:
        session["active_focus"] = "Acute Coronary Syndrome"
    elif "embolism" in ans_text or "pe" in ans_text:
        session["active_focus"] = "Pulmonary Embolism"
    elif "sepsis" in ans_text:
        session["active_focus"] = "Sepsis"
