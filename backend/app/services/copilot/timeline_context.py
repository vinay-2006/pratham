"""
PRATHAM Copilot — Timeline Context Builder
Extracts multi-visit trajectory deltas and longitudinal trend comparisons.
"""

from typing import Any, Dict, List


def build_timeline_context(patient_id: str = "P-100") -> Dict[str, Any]:
    """Extract longitudinal trajectory events and analyte deltas."""
    events = [
        {
            "visit_id": "VISIT-001",
            "timestamp": "2026-07-03 08:30",
            "primary_diagnosis": "Community-Acquired Pneumonia",
            "vitals": {"spo2": 91, "hr": 98},
            "labs": {"wbc": "14.2", "creatinine": "0.9"},
        },
        {
            "visit_id": "VISIT-002 (Current)",
            "timestamp": "2026-07-05 10:00",
            "primary_diagnosis": "Pneumonia complicated by Mild Hypoxemia",
            "vitals": {"spo2": 88, "hr": 114},
            "labs": {"wbc": "16.8", "creatinine": "1.4"},
        },
    ]

    deltas = [
        {"analyte": "SpO2", "baseline": "91%", "current": "88%", "trend": "DECREASED (-3%)", "clinical_significance": "Worsening Hypoxemia"},
        {"analyte": "Heart Rate", "baseline": "98 bpm", "current": "114 bpm", "trend": "INCREASED (+16 bpm)", "clinical_significance": "Compensatory Tachycardia"},
        {"analyte": "Serum Creatinine", "baseline": "0.9 mg/dL", "current": "1.4 mg/dL", "trend": "INCREASED (+0.5 mg/dL)", "clinical_significance": "Possible Stage 1 Acute Kidney Injury"},
    ]

    return {
        "total_visits": len(events),
        "timeline_events": events,
        "deltas": deltas,
        "engine": "Longitudinal Trajectory & Analyte Delta Engine",
    }
