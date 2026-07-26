"""
InvestigationHistoryService — Business logic for the investigation history view.

Domain: Investigations / Audit History
Responsibility: Return investigation records across all statuses with 72-hour
                retention, optional tab-filter, notification status derivation,
                and audit trail extraction.

Extracted from: api/investigations.py::get_investigation_history (L428–607)

Safety justification:
  ✓ Read-only — zero writes, zero status transitions
  ✓ No awaits — original was async def with 0 await calls
  ✓ Sequential orchestration only
  ✓ Existing repositories (intake, investigation) are sufficient
  ✓ All helpers are now in patient_utils (pure functions)
  ✓ Response dict shape unchanged

Business rules owned here:
  • 72-hour retention filter (cutoff calculation)
  • query_status → db_status mapping (URL param → DB filter)
  • notification_status decision tree (5 branches)
  • Post-filter (ensures each record appears in exactly one tab)
  • Audit trail extraction (first investigation with approved_by / rejected_by)
  • Vitals summary, symptom labels, severity, urgency (via patient_utils)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from app.domains.triage.repository import intake_repository
from app.domains.investigation.repository import investigation_repository
from app.services.workflow_service import resolve_intakes_status
from app.utils.patient_utils import (
    build_display_name,
    compute_age,
    derive_sex,
    extract_arrival_time,
    derive_severity,
    derive_urgency,
    derive_symptom_labels,
    format_vitals,
)

logger = logging.getLogger(__name__)

# Query-param value → DB status filter value
_QUERY_STATUS_MAP: dict[str, str] = {
    "approved":         "investigation_approved",
    "needs_info":       "needs_info",
    "pending_approval": "intake_pending",
}

# URL param values that the endpoint accepts
_VALID_STATUSES: frozenset[str] = frozenset({
    "approved", "rejected", "needs_info", "pending_approval"
})

_INTAKE_COLUMNS = (
    "id, chief_complaint, emergency_description, "
    "ambulance_eta, severity_level, status, created_at, "
    "patients(id, first_name, last_name, gender, date_of_birth, contact_number), "
    "vitals(heart_rate, spo2, bp_systolic, bp_diastolic, temperature, respiratory_rate), "
    "symptoms(chest_pain, breathlessness, trauma, bleeding, unconsciousness, neurological_symptoms), "
    "risk_scores(cardiac_risk, respiratory_risk, trauma_risk, neurological_risk, overall_severity)"
)


def _derive_notification_status(intake_status: str, inv_statuses: List[str]) -> str:
    """
    Map an intake status + investigation statuses to a UI notification label.

    Decision tree (matches original investigations.py logic exactly):
      1. intake_status == "investigation_approved"                → "Approved"
      2. intake_status == "needs_info"                           → "Needs Info"
      3. all investigations are "rejected"                       → "Rejected"
      4. intake_status == "intake_pending" (or anything else)    → "Pending Approval"
    """
    if intake_status == "investigation_approved":
        return "Approved"
    if intake_status == "needs_info":
        return "Needs Info"
    if inv_statuses and all(s == "rejected" for s in inv_statuses):
        return "Rejected"
    return "Pending Approval"


def _extract_audit_info(inv_rows: List[Dict]) -> Dict:
    """
    Return audit metadata from the first investigation that has reviewer data.

    Prefers approved_by; falls back to rejected_by. Returns {} if neither found.
    """
    for inv in inv_rows:
        if inv.get("approved_by"):
            return {
                "reviewedBy":   inv["approved_by"],
                "reviewedAt":   inv.get("approved_at", ""),
                "reviewNotes":  inv.get("review_notes", ""),
            }
        if inv.get("rejected_by"):
            return {
                "reviewedBy":   inv["rejected_by"],
                "reviewedAt":   inv.get("rejected_at", ""),
                "reviewNotes":  inv.get("review_notes", ""),
            }
    return {}


def get_investigation_history(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return investigation history records with 72-hour retention.

    Args:
      status: optional filter — one of "approved", "rejected", "needs_info",
              "pending_approval". Invalid / None values are ignored (all records
              returned subject only to the 72h window).

    Returns a list of patient history dicts (same shape as original endpoint).

    Raises Exception on any repository failure (caller maps to HTTP 500).
    """
    cutoff_dt = datetime.now(timezone.utc) - timedelta(hours=72)

    # Validate and resolve the URL query param
    query_status: Optional[str] = status if status in _VALID_STATUSES else None
    db_status: Optional[str] = _QUERY_STATUS_MAP.get(query_status) if query_status else None

    result_data = intake_repository.list_with_status_filter(
        columns=_INTAKE_COLUMNS,
        status=db_status,
    )

    intakes_resolved = resolve_intakes_status(result_data)

    # Batch-fetch all investigations to avoid N+1 queries
    intake_ids = [item["id"] for item in intakes_resolved]
    investigations_by_intake: Dict[str, List] = {}
    if intake_ids:
        try:
            inv_data = investigation_repository.get_by_intake_ids(
                intake_ids,
                columns=(
                    "id, intake_id, investigation_type, status, "
                    "approved_at, approved_by, rejected_at, rejected_by, "
                    "review_notes, created_at"
                ),
            )
        except Exception:
            # Fallback: fetch without audit columns if schema doesn't support them
            inv_data = investigation_repository.get_by_intake_ids(
                intake_ids,
                columns="id, intake_id, investigation_type, status, created_at",
            )
        for inv in inv_data:
            iid = inv["intake_id"]
            investigations_by_intake.setdefault(iid, []).append(inv)

    patients_data: List[Dict[str, Any]] = []

    for intake in intakes_resolved:
        intake_status = intake.get("status", "")
        created       = intake.get("created_at", "")

        # 72-hour retention: skip non-pending records older than cutoff
        # Use datetime comparison instead of string comparison to handle
        # timezone format differences (Z vs +00:00).
        try:
            created_dt = datetime.fromisoformat(str(created).replace("Z", "+00:00")) if created else None
        except (ValueError, TypeError):
            created_dt = None
        if intake_status != "intake_pending" and created_dt and created_dt < cutoff_dt:
            continue

        inv_rows     = investigations_by_intake.get(intake["id"], [])
        inv_statuses = [r.get("status", "") for r in inv_rows]

        # Supabase returns joined rows as arrays — take first element
        vitals_row  = (intake.get("vitals")     or [None])[0]
        syms_row    = (intake.get("symptoms")   or [None])[0]
        risk_row    = (intake.get("risk_scores") or [None])[0]
        patient_row = intake.get("patients")

        name     = build_display_name(patient_row)
        age      = compute_age((patient_row or {}).get("date_of_birth"))
        sex      = derive_sex((patient_row or {}).get("gender"))
        severity = derive_severity(risk_row)

        symptom_labels              = derive_symptom_labels(syms_row)
        vitals_summary, vitals_dict = format_vitals(vitals_row)
        inv_types                   = [r["investigation_type"] for r in inv_rows]
        ts                          = extract_arrival_time(created)

        notification_status = _derive_notification_status(intake_status, inv_statuses)

        # Post-filter: each intake must appear in exactly one tab
        if query_status == "rejected" and notification_status != "Rejected":
            continue
        if query_status == "pending_approval" and notification_status != "Pending Approval":
            continue

        audit_info = _extract_audit_info(inv_rows)

        patients_data.append({
            "id":                      f"ntf-{intake['id'][:8]}",
            "intake_id":               intake["id"],
            "patientName":             name,
            "age":                     age,
            "sex":                     sex,
            "severity":                severity,
            "symptoms":                symptom_labels,
            "vitalsSummary":           vitals_summary,
            "recommendedInvestigations": inv_types,
            "timestamp":               ts,
            "urgency":                 derive_urgency(severity),
            "status":                  notification_status,
            "emergencyDescription":    intake.get("emergency_description", ""),
            "vitals":                  vitals_dict,
            "audit":                   audit_info,
        })

    return patients_data
