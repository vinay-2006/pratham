"""
clinical_context_service.py — Upstream Patient Clinical Context Engine

Extracts and structures patient demographic, visit, and risk context
prior to reference range evaluation and lab intelligence processing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ClinicalContext:
    age: int = 0
    age_group: str = "adult"  # 'pediatric' (<18), 'adult' (18-64), 'elderly' (>=65)
    sex: str = "unknown"      # 'male', 'female', 'unknown'
    visit_type: str = "emergency"  # 'routine' or 'emergency'
    chief_complaint: str = ""
    description: str = ""
    is_pregnant: bool = False
    active_risk_domains: List[str] = field(default_factory=list)
    overall_severity: str = "moderate"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "age": self.age,
            "age_group": self.age_group,
            "sex": self.sex,
            "visit_type": self.visit_type,
            "chief_complaint": self.chief_complaint,
            "description": self.description,
            "is_pregnant": self.is_pregnant,
            "active_risk_domains": self.active_risk_domains,
            "overall_severity": self.overall_severity,
        }


def build_clinical_context(
    patient_data: Dict[str, Any],
    vitals_data: Dict[str, Any],
    symptoms_data: Dict[str, Any] | List[str],
    risk_scores: Dict[str, Any] | None = None,
    chief_complaint: str | None = None,
    description: str | None = None,
    visit_type: str | None = None,
) -> ClinicalContext:
    """
    Constructs a standardized ClinicalContext object for a patient.
    """
    age = int(patient_data.get("age") or patient_data.get("date_of_birth") or 0)
    if age < 18 and age > 0:
        age_group = "pediatric"
    elif age >= 65:
        age_group = "elderly"
    else:
        age_group = "adult"

    raw_sex = (patient_data.get("gender") or patient_data.get("sex") or "").lower().strip()
    if raw_sex in ("m", "male"):
        sex = "male"
    elif raw_sex in ("f", "female"):
        sex = "female"
    else:
        sex = "unknown"

    cc = chief_complaint or patient_data.get("chief_complaint") or ""
    desc = description or patient_data.get("emergency_description") or ""

    # Pregnancy detection in notes or medical history
    history_str = " ".join([
        str(cc), str(desc),
        str(patient_data.get("past_medical_history") or "")
    ]).lower()
    is_pregnant = sex == "female" and any(w in history_str for w in ["pregnant", "pregnancy", "gestation", "trimester"])

    # Determine visit type
    v_type = visit_type or ("routine" if "routine" in history_str or "checkup" in history_str else "emergency")

    # Determine active risk domains
    active_domains: List[str] = []
    if risk_scores:
        for domain in ["cardiac", "respiratory", "trauma", "neurological"]:
            if (risk_scores.get(f"{domain}_risk") or risk_scores.get(domain) or 0) >= 30:
                active_domains.append(domain)

    severity = ((risk_scores and risk_scores.get("overall_severity")) or patient_data.get("severity") or "moderate").lower()

    return ClinicalContext(
        age=age,
        age_group=age_group,
        sex=sex,
        visit_type=v_type,
        chief_complaint=cc,
        description=desc,
        is_pregnant=is_pregnant,
        active_risk_domains=active_domains,
        overall_severity=severity,
    )
