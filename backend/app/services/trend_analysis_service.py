"""
trend_analysis_service.py — Longitudinal Trend & Comparative Delta Analysis Engine

Evaluates longitudinal trajectory of vitals and laboratory analytes across multiple patient visits.
Generates physician-friendly comparative delta strings (e.g. "SpO₂: 88% → 96% Improved").
"""

from __future__ import annotations
from typing import Any, Dict, List


def analyze_longitudinal_trends(visits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes multi-visit trajectory and returns trend metrics and comparative diffs.
    """
    if not visits or len(visits) < 2:
        return {
            "has_longitudinal_data": False,
            "visit_count": len(visits),
            "comparative_deltas": [],
            "vital_trends": {},
            "overall_trajectory": "STABLE",
        }

    # Sort visits by created_at ascending (oldest first, newest last)
    sorted_visits = sorted(visits, key=lambda x: x.get("created_at") or "")
    prev_v = sorted_visits[-2]
    curr_v = sorted_visits[-1]

    prev_vitals = prev_v.get("vitals", {})
    curr_vitals = curr_v.get("vitals", {})

    deltas: List[Dict[str, Any]] = []

    # 1. SpO2 Trend (Higher is better)
    p_spo2 = prev_vitals.get("spo2")
    c_spo2 = curr_vitals.get("spo2")
    if p_spo2 and c_spo2:
        diff = c_spo2 - p_spo2
        status = "IMPROVED" if diff > 0 else ("DETERIORATED" if diff < 0 else "STABLE")
        deltas.append({
            "parameter": "SpO₂ Saturation",
            "previous_value": f"{p_spo2}%",
            "current_value": f"{c_spo2}%",
            "status": status,
            "display_str": f"SpO₂: {p_spo2}% → {c_spo2}% ({status.title()})",
        })

    # 2. Respiratory Rate (Lower toward 12-18 is better)
    p_rr = prev_vitals.get("respiratory_rate")
    c_rr = curr_vitals.get("respiratory_rate")
    if p_rr and c_rr:
        status = "IMPROVED" if c_rr < p_rr else ("DETERIORATED" if c_rr > p_rr else "STABLE")
        deltas.append({
            "parameter": "Respiratory Rate",
            "previous_value": f"{p_rr}/min",
            "current_value": f"{c_rr}/min",
            "status": status,
            "display_str": f"Respiratory Rate: {p_rr} → {c_rr}/min ({status.title()})",
        })

    # 3. Heart Rate (Lower toward 60-90 is better)
    p_hr = prev_vitals.get("heart_rate")
    c_hr = curr_vitals.get("heart_rate")
    if p_hr and c_hr:
        status = "IMPROVED" if c_hr < p_hr else ("DETERIORATED" if c_hr > p_hr else "STABLE")
        deltas.append({
            "parameter": "Heart Rate",
            "previous_value": f"{p_hr} bpm",
            "current_value": f"{c_hr} bpm",
            "status": status,
            "display_str": f"Heart Rate: {p_hr} → {c_hr} bpm ({status.title()})",
        })

    # 4. Temperature (Lower toward 36.6°C is better)
    p_temp = prev_vitals.get("temperature")
    c_temp = curr_vitals.get("temperature")
    if p_temp and c_temp:
        status = "IMPROVED" if c_temp < p_temp else ("DETERIORATED" if c_temp > p_temp else "STABLE")
        deltas.append({
            "parameter": "Body Temperature",
            "previous_value": f"{p_temp}°C",
            "current_value": f"{c_temp}°C",
            "status": status,
            "display_str": f"Temperature: {p_temp}°C → {c_temp}°C ({status.title()})",
        })

    # Overall Trajectory
    improved_count = sum(1 for d in deltas if d["status"] == "IMPROVED")
    deteriorated_count = sum(1 for d in deltas if d["status"] == "DETERIORATED")

    if improved_count >= 2:
        overall = "CLINICALLY IMPROVING"
    elif deteriorated_count >= 2:
        overall = "CLINICALLY DETERIORATING"
    else:
        overall = "CLINICALLY STABLE"

    return {
        "has_longitudinal_data": True,
        "visit_count": len(visits),
        "comparative_deltas": deltas,
        "overall_trajectory": overall,
    }
