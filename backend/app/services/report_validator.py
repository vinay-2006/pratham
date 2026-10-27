"""
report_validator.py — Post-Generation Report Quality Validator

Runs after get_complete_report() to catch quality issues before the report
is served to clinicians or rendered as PDF.

This validator is NON-BLOCKING: it logs errors and attaches validation
results to the report dict for debugging, but never prevents the report
from being returned.

Checks:
  1. No Python exceptions or stack traces in string values
  2. No duplicate evidence entries
  3. No placeholder or mock text in narrative fields
  4. No empty mandatory sections
  5. No raw JSON fragments in narrative fields
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ── Patterns that should never appear in clinician-facing text ────────────────

_EXCEPTION_PATTERNS = [
    re.compile(r"Traceback \(most recent call", re.IGNORECASE),
    re.compile(r"^\s*File \".*\", line \d+", re.MULTILINE),
    re.compile(r"(?:Error|Exception):\s+\S+", re.IGNORECASE),
    re.compile(r"raise \w+Error", re.IGNORECASE),
]

_STACK_TRACE_PATTERNS = [
    re.compile(r"File \".*\.py\",\s*line\s*\d+"),
    re.compile(r"in\s+<module>"),
    re.compile(r"^\s+\^\s*$", re.MULTILINE),
]

_PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bPLACEHOLDER\b", re.IGNORECASE),
    re.compile(r"\bLorem ipsum\b", re.IGNORECASE),
    re.compile(r"\bmock[_\s]?data\b", re.IGNORECASE),
    re.compile(r"\bfixme\b", re.IGNORECASE),
]

_JSON_FRAGMENT_PATTERN = re.compile(r'\{"[a-z_]+"\s*:\s*')

# ── Narrative fields to scan ─────────────────────────────────────────────────

NARRATIVE_KEYS = [
    "clinical_overview",
    "overall_impression",
    "cardiac_summary",
    "respiratory_summary",
    "laboratory_summary",
    "imaging_summary",
    "monitoring_narrative",
    "precautions_narrative",
    "alternative_considerations_narrative",
    "limitations_narrative",
]

# ── Mandatory sections that must be non-empty ────────────────────────────────

MANDATORY_SECTIONS = [
    "patient_summary",
    "vitals",
    "clinical_conclusions",
]


# ── Core validator ───────────────────────────────────────────────────────────

def validate_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a complete report dict for quality issues.

    Returns:
        {
            "valid": bool,
            "errors": [{"check": str, "detail": str, "severity": "ERROR"}],
            "warnings": [{"check": str, "detail": str, "severity": "WARNING"}],
        }
    """
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    _check_python_exceptions(report, errors)
    _check_stack_traces(report, errors)
    _check_duplicate_evidence(report, errors)
    _check_placeholder_text(report, warnings)
    _check_empty_mandatory_sections(report, warnings)
    _check_json_in_narratives(report, warnings)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ── Individual checks ────────────────────────────────────────────────────────

def _collect_string_values(obj: Any, path: str = "") -> List[tuple[str, str]]:
    """Recursively collect all (path, string_value) pairs from a nested structure."""
    results: List[tuple[str, str]] = []
    if isinstance(obj, str):
        results.append((path, obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            results.extend(_collect_string_values(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            results.extend(_collect_string_values(v, f"{path}[{i}]"))
    return results


def _check_python_exceptions(report: Dict, errors: List[Dict[str, str]]) -> None:
    """Scan all string values for Python exception patterns."""
    for path, value in _collect_string_values(report):
        # Skip known-safe fields that may legitimately contain technical text
        if any(skip in path for skip in ("pipeline_status", "validation", "error_message")):
            continue
        for pattern in _EXCEPTION_PATTERNS:
            if pattern.search(value):
                errors.append({
                    "check": "no_python_exceptions",
                    "detail": f"Python exception pattern found at '{path}': {value[:120]}",
                    "severity": "ERROR",
                })
                break  # One match per field is enough


def _check_stack_traces(report: Dict, errors: List[Dict[str, str]]) -> None:
    """Scan all string values for stack trace patterns."""
    for path, value in _collect_string_values(report):
        if any(skip in path for skip in ("pipeline_status", "validation", "error_message")):
            continue
        for pattern in _STACK_TRACE_PATTERNS:
            if pattern.search(value):
                errors.append({
                    "check": "no_stack_traces",
                    "detail": f"Stack trace pattern found at '{path}': {value[:120]}",
                    "severity": "ERROR",
                })
                break


def _check_duplicate_evidence(report: Dict, errors: List[Dict[str, str]]) -> None:
    """Verify the evidence list has no duplicate (file_name, evidence_type, file_size) tuples."""
    evidence = report.get("evidence", [])
    if not evidence:
        return

    seen: set[tuple[str, str, Any]] = set()
    for ev in evidence:
        key = (
            ev.get("file_name", ""),
            ev.get("evidence_type", ""),
            ev.get("file_size"),
        )
        if key in seen:
            errors.append({
                "check": "no_duplicate_evidence",
                "detail": f"Duplicate evidence entry: file_name={key[0]!r}, type={key[1]!r}",
                "severity": "ERROR",
            })
        else:
            seen.add(key)


def _check_placeholder_text(report: Dict, warnings: List[Dict[str, str]]) -> None:
    """Check narrative fields for placeholder or mock text."""
    interp = report.get("clinical_interpretation", {})
    if not isinstance(interp, dict):
        return

    for key in NARRATIVE_KEYS:
        value = interp.get(key, "")
        if not isinstance(value, str) or not value:
            continue
        for pattern in _PLACEHOLDER_PATTERNS:
            if pattern.search(value):
                warnings.append({
                    "check": "no_placeholder_text",
                    "detail": f"Placeholder text found in '{key}': matched '{pattern.pattern}'",
                    "severity": "WARNING",
                })
                break


def _check_empty_mandatory_sections(report: Dict, warnings: List[Dict[str, str]]) -> None:
    """Verify mandatory sections are non-empty."""
    for section in MANDATORY_SECTIONS:
        value = report.get(section)
        if value is None:
            warnings.append({
                "check": "no_empty_mandatory_sections",
                "detail": f"Mandatory section '{section}' is missing",
                "severity": "WARNING",
            })
        elif isinstance(value, dict) and not value:
            warnings.append({
                "check": "no_empty_mandatory_sections",
                "detail": f"Mandatory section '{section}' is empty",
                "severity": "WARNING",
            })


def _check_json_in_narratives(report: Dict, warnings: List[Dict[str, str]]) -> None:
    """Scan narrative fields for raw JSON fragments that shouldn't be in clinical text."""
    interp = report.get("clinical_interpretation", {})
    if not isinstance(interp, dict):
        return

    for key in NARRATIVE_KEYS:
        value = interp.get(key, "")
        if not isinstance(value, str) or not value:
            continue
        if _JSON_FRAGMENT_PATTERN.search(value):
            warnings.append({
                "check": "no_json_in_narratives",
                "detail": f"Raw JSON fragment found in '{key}'",
                "severity": "WARNING",
            })
