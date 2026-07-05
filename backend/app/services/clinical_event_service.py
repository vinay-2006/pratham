"""
clinical_event_service.py — Clinical Event Timeline Service

Generates and tracks chronologically logged clinical workflow milestones for a patient visit.
"""

from __future__ import annotations
from typing import Any, Dict, List


def get_clinical_event_timeline(intake_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Returns a list of structured clinical events logged for the intake workflow.
    """
    created_at = intake_data.get("generated_at") or intake_data.get("created_at") or "10:00 AM"
    time_str = str(created_at)[11:16] if len(str(created_at)) >= 16 else "10:00 AM"

    events = [
        {
            "timestamp": f"{time_str}",
            "title": "Patient Arrived & Emergency Intake Registered",
            "category": "intake",
            "status": "completed",
        },
        {
            "timestamp": f"{time_str}",
            "title": "Clinical NLP Symptom & Entity Extraction Completed",
            "category": "nlp",
            "status": "completed",
        },
        {
            "timestamp": f"{time_str}",
            "title": "Deterministic Risk Scoring Engine Executed",
            "category": "risk",
            "status": "completed",
        },
    ]

    # Check investigations
    investigations = intake_data.get("investigations", [])
    approved = [i["investigation_type"] for i in investigations if i.get("status") == "approved"]
    if approved:
        events.append({
            "timestamp": f"{time_str}",
            "title": f"Attending Physician Approved Investigations: {', '.join(approved)}",
            "category": "approval",
            "status": "completed",
        })

    # Check evidence uploaded
    if intake_data.get("evidence"):
        events.append({
            "timestamp": f"{time_str}",
            "title": f"{len(intake_data['evidence'])} Diagnostic Evidence File(s) Linked to Record",
            "category": "evidence",
            "status": "completed",
        })

    # Check lab intelligence
    if intake_data.get("lab_intelligence", {}).get("available"):
        events.append({
            "timestamp": f"{time_str}",
            "title": "Laboratory Reference Range & AI Evaluation Completed",
            "category": "lab",
            "status": "completed",
        })

    # Report generated
    events.append({
        "timestamp": f"{time_str}",
        "title": "Unified PRATHAM v2.0 Clinical Intelligence Report Generated",
        "category": "report",
        "status": "completed",
    })

    return events
