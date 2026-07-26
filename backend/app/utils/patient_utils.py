"""
app/utils/patient_utils.py
──────────────────────────
Shared patient-presentation utility functions.

Ownership justification
─────────────────────────────────────────────────────────────────────────────
These are PURE functions with no side-effects, no domain state, and no
repository calls. They are presentation helpers — they transform data that
has already been fetched and validated by domain services.

They are NOT domain services: they carry no business rules about when or
why a patient changes state. They simply answer "what label do I show?".

They are NOT repository methods: they take plain dicts, not DB row IDs.

A shared utility is the correct classification because:
  • Each function is duplicated verbatim across 2-6 call-sites
    in api/investigations.py and services/lab_analysis_service.py
  • No single domain owns the logic — it is used by investigations,
    lab analysis, and doctor-facing services equally
  • Moving them here removes duplication without introducing any
    architectural coupling between domains

Functions
─────────────────────────────────────────────────────────────────────────────
  compute_age(dob)             → int
  build_display_name(row)      → str
  derive_sex(gender_str)       → "M" | "F"
  extract_arrival_time(ts_str) → "HH:MM" | ""
"""

from __future__ import annotations

from datetime import datetime


# ── Age ──────────────────────────────────────────────────────────────────────

def compute_age(dob: str | None) -> int:
    """
    Derive patient age in whole years from a date_of_birth value.

    Accepts:
      • ISO-8601 date string "YYYY-MM-DD"   (birth year extracted from prefix)
      • Plain integer string "35"           (treated as age directly)
      • None / empty                        → returns 0

    Returns 0 on any parse failure — never raises.

    Duplication sites replaced:
      api/investigations.py L208-221, L504-517, L712-724, L1474-1484, L1579-1589
      services/lab_analysis_service.py (compute_age already present there;
        lab_analysis_service should import this function instead)
    """
    if not dob:
        return 0
    dob_str = str(dob)
    if "-" in dob_str:
        try:
            return max(0, datetime.now().year - int(dob_str.split("-")[0]))
        except (ValueError, IndexError):
            pass
    try:
        return int(dob_str)
    except (TypeError, ValueError):
        return 0


# ── Name ─────────────────────────────────────────────────────────────────────

def build_display_name(patient_row: dict | None) -> str:
    """
    Build a human-readable patient name from a Supabase patients row.

    Logic (matches existing _build_display_name in api/investigations.py):
      • Strips whitespace from first_name and last_name
      • Avoids "John John" when last_name == first_name
      • Falls back to "Unknown" when both are blank

    Duplication sites replaced:
      api/investigations.py L42-49 (_build_display_name module helper)
      api/investigations.py L1336, L1469, L1574 (inline f-string variants)
    """
    row = patient_row or {}
    first = (row.get("first_name") or "").strip()
    last = (row.get("last_name") or "").strip()
    if last and last != first:
        return f"{first} {last}".strip() or "Unknown"
    return first or "Unknown"


# ── Sex ──────────────────────────────────────────────────────────────────────

def derive_sex(gender: str | None) -> str:
    """
    Map a freetext gender string to the binary M/F used by the ML model and UI.

    Returns "M" if gender is exactly "male" (case-insensitive), else "F".

    Duplication sites replaced:
      api/investigations.py L206, L502, L710, L1127, L1472, L1577
    """
    return "M" if (gender or "").strip().lower() == "male" else "F"


# ── Arrival timestamp ────────────────────────────────────────────────────────

def extract_arrival_time(created_at: str | None) -> str:
    """
    Extract the HH:MM portion from an ISO-8601 datetime string.

    "2026-07-19T08:32:00+00:00"  →  "08:32"
    None / short string           →  ""

    Duplication sites replaced:
      api/investigations.py L246, L556, L731, L1112
    """
    s = str(created_at or "")
    return s[11:16] if len(s) >= 16 else ""


# ── Symptom labels ────────────────────────────────────────────────────────────

# Canonical mapping from symptoms row fields to UI display strings.
# Moved here from api/investigations.py::SYMPTOM_LABEL_MAP.
SYMPTOM_LABEL_MAP: dict[str, str] = {
    "chest_pain":             "Chest Pain",
    "breathlessness":         "Breathlessness",
    "trauma":                 "Trauma",
    "bleeding":               "Bleeding",
    "unconsciousness":        "Unconsciousness",
    "neurological_symptoms":  "Neurological Symptoms",
}


def derive_symptom_labels(syms_row: dict | None) -> list[str]:
    """
    Return the list of active symptom display labels from a symptoms DB row.

    Example:
      {"chest_pain": True, "breathlessness": False, ...}  →  ["Chest Pain"]
    """
    row = syms_row or {}
    return [label for field, label in SYMPTOM_LABEL_MAP.items() if row.get(field)]


# ── Severity / Urgency ────────────────────────────────────────────────────────

def derive_severity(risk: dict | None) -> str:
    """
    Map a risk_scores DB row to a severity string.

    Priority:
      1. overall_severity field if it is a known label
      2. Numeric fallback: max of cardiac/respiratory/trauma/neurological scores
         ≥ 70 → critical | ≥ 50 → high | ≥ 30 → moderate | else → low

    Moved from api/investigations.py::_derive_severity.
    """
    if not risk:
        return "moderate"
    overall = (risk.get("overall_severity") or "").lower()
    if overall in ("critical", "high", "moderate", "low"):
        return overall
    top = max(
        risk.get("cardiac_risk", 0) or 0,
        risk.get("respiratory_risk", 0) or 0,
        risk.get("trauma_risk", 0) or 0,
        risk.get("neurological_risk", 0) or 0,
    )
    if top >= 70:
        return "critical"
    if top >= 50:
        return "high"
    if top >= 30:
        return "moderate"
    return "low"


def derive_urgency(severity: str) -> str:
    """
    Map a severity string to a UI urgency label.

    critical → "Critical" | high → "Urgent" | anything else → "Routine"

    Moved from api/investigations.py::_derive_urgency.
    """
    return {"critical": "Critical", "high": "Urgent"}.get(severity, "Routine")


# ── Vitals formatting ─────────────────────────────────────────────────────────

def format_vitals(vitals_row: dict | None) -> tuple[str, dict]:
    """
    Format a vitals DB row into a (summary_string, structured_dict) pair.

    Summary string:
      "HR 72 · SpO₂ 98% · BP 120/80"

    Structured dict:
      {"heartRate": 72, "spo2": 98, "bloodPressure": "120/80",
       "respiratoryRate": 18, "temperature": 37.1}

    Moved pattern from api/investigations.py (duplicated in pending and history).
    """
    row = vitals_row or {}
    hr       = row.get("heart_rate")
    spo2_val = row.get("spo2")
    bp_sys   = row.get("bp_systolic")
    bp_dia   = row.get("bp_diastolic")

    try:
        bp_str   = f"{int(bp_sys)}/{int(bp_dia)}" if bp_sys and bp_dia else "\u2014"
    except (ValueError, TypeError):
        bp_str   = "\u2014"
    spo2_str = f"{spo2_val}%" if spo2_val else "\u2014"
    _em = "\u2014"
    _mid = "\u00b7"
    _spo2 = "SpO\u2082"
    summary  = f"HR {hr or _em} {_mid} {_spo2} {spo2_str} {_mid} BP {bp_str}"

    structured = {
        "heartRate":       hr,
        "spo2":            spo2_val,
        "bloodPressure":   bp_str,
        "respiratoryRate": row.get("respiratory_rate"),
        "temperature":     row.get("temperature"),
    }
    return summary, structured
