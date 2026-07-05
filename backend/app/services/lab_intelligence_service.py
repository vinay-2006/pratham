"""
lab_intelligence_service.py — Generic Analyte-Agnostic Laboratory Engine

Evaluates laboratory panels (CBC, BMP, LFT, Urinalysis, Cardiac Markers)
using the Reference Range Engine and Clinical Context.
"""

from __future__ import annotations
from typing import Any, Dict, List
from app.services.clinical_context_service import ClinicalContext
from app.services.lab_parser_service import parse_lab_values
from app.services.reference_range_service import evaluate_analyte


def evaluate_lab_panel(
    raw_lab_data: Dict[str, Any] | str | None,
    context: ClinicalContext | None = None,
) -> Dict[str, Any]:
    """
    Evaluates all analytes in a lab report against reference ranges.
    Returns a unified laboratory intelligence payload.
    """
    parsed = parse_lab_values(raw_lab_data)
    if not parsed:
        return {
            "available": False,
            "evaluations": [],
            "abnormal_count": 0,
            "critical_count": 0,
            "summary_findings": [],
        }

    evaluations: List[Dict[str, Any]] = []
    abnormal_count = 0
    critical_count = 0
    summary_findings: List[str] = []

    for name, val in parsed.items():
        res = evaluate_analyte(name, val, context)
        evaluations.append(res)

        if res["status"] != "NORMAL":
            abnormal_count += 1
            summary_findings.append(f"{res['analyte']} {res['severity']} {res['status']}: {res['value']} {res['unit']}")

        if res["severity"] == "CRITICAL":
            critical_count += 1

    return {
        "available": True,
        "evaluations": evaluations,
        "abnormal_count": abnormal_count,
        "critical_count": critical_count,
        "summary_findings": summary_findings,
    }
