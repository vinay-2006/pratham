"""
PendingApprovalsService — Business logic for the doctor approvals queue.

Domain: Investigations / Doctor Approval
Responsibility: Retrieve all patients with pending-approval investigations,
                assembled with vitals, symptoms, and risk context.

Extracted from: api/investigations.py::get_pending_approvals (L160–278)

Safety justification:
  ✓ Read-only — zero writes, zero status transitions
  ✓ No awaits — original was async def with 0 await calls
  ✓ Sequential orchestration only
  ✓ Existing repositories (intake, investigation) are sufficient
  ✓ All helpers are now in patient_utils (pure functions)
  ✓ Response dict shape unchanged

Business rules owned here:
  • Vitals summary formatting (vitalsSummary string + structured dict)
  • Symptom label mapping
  • Severity derivation from risk_scores row
  • Urgency derivation from severity string
  • Inline joined-row unpacking (vitals/symptoms/risk are Supabase arrays)
"""

from __future__ import annotations

import logging
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

# Columns fetched from emergency_intake (with joins)
_INTAKE_COLUMNS = (
    "id, chief_complaint, emergency_description, "
    "ambulance_eta, severity_level, status, created_at, "
    "patients(id, first_name, last_name, gender, date_of_birth, contact_number), "
    "vitals(heart_rate, spo2, bp_systolic, bp_diastolic, temperature, respiratory_rate), "
    "symptoms(chest_pain, breathlessness, trauma, bleeding, unconsciousness, neurological_symptoms), "
    "risk_scores(cardiac_risk, respiratory_risk, trauma_risk, neurological_risk, overall_severity)"
)


def get_pending_approvals() -> List[Dict[str, Any]]:
    """
    Return all patients with pending-approval investigations, with full clinical context.

    Reads intakes with status ``intake_pending``, resolves statuses,
    batch-fetches pending investigations, then assembles the display record.

    Returns a list of patient summary dicts (same shape as original endpoint).

    Raises Exception on any repository failure (caller maps to HTTP 500).
    """
    try:
        result_data = intake_repository.list_with_status_filter(
            columns=_INTAKE_COLUMNS,
            status="intake_pending",
        )
    except Exception:
        logger.warning("[Pending] Retrying pending approvals fetch after transient error")
        result_data = intake_repository.list_with_status_filter(
            columns=_INTAKE_COLUMNS,
            status="intake_pending",
        )

    intakes_resolved = resolve_intakes_status(result_data)

    # Batch-fetch pending_approval investigations to avoid N+1 queries
    intake_ids = [item["id"] for item in intakes_resolved]
    investigations_by_intake: Dict[str, List] = {}
    if intake_ids:
        inv_data = investigation_repository.get_by_intake_ids_with_status(
            intake_ids,
            "pending_approval",
            columns="id, intake_id, investigation_type, status",
        )
        for inv in inv_data:
            iid = inv["intake_id"]
            investigations_by_intake.setdefault(iid, []).append(inv)

    patients_data: List[Dict[str, Any]] = []

    for intake in intakes_resolved:
        inv_rows = investigations_by_intake.get(intake["id"], [])

        # Supabase returns joined rows as arrays — take first element
        vitals_row  = (intake.get("vitals")     or [None])[0]
        syms_row    = (intake.get("symptoms")   or [None])[0]
        risk_row    = (intake.get("risk_scores") or [None])[0]
        patient_row = intake.get("patients")

        name     = build_display_name(patient_row)
        age      = compute_age((patient_row or {}).get("date_of_birth"))
        sex      = derive_sex((patient_row or {}).get("gender"))
        severity = derive_severity(risk_row)

        symptom_labels        = derive_symptom_labels(syms_row)
        vitals_summary, vitals_structured = format_vitals(vitals_row)

        inv_types = [r["investigation_type"] for r in inv_rows]
        ts        = extract_arrival_time(intake.get("created_at", ""))

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
            "status":                  "Pending Approval",
            "emergencyDescription":    intake.get("emergency_description", ""),
            "vitals":                  vitals_structured,
        })

    return patients_data
