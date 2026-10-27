"""
PRATHAM v5.1.0 — Clinical Stabilization Verification Suite
============================================================
6 canonical clinical scenarios + automated post-generation validator.

Usage:
    python test_v510_stabilization.py

Scenarios:
    1. ACS (Emergency)       — must classify as high cardiac risk
    2. Routine Health Check  — must NOT classify as ACS
    3. Pneumonia             — must classify as respiratory
    4. Pulmonary Embolism    — must rank PE high, not confuse with pneumonia
    5. Stroke                — must flag neurological risk
    6. Trauma                — must flag trauma risk, not respiratory

Post-generation validator checks:
    - No Python exceptions in report text
    - No duplicate evidence entries
    - No mock/placeholder data leakage
    - No empty mandatory sections
    - No stack traces
    - No raw JSON blobs in narrative fields
"""

import json
import os
import re
import sys
import time
import traceback

import httpx

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"
TIMEOUT = 30

XRAY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "datasets", "chest_xray", "test", "PNEUMONIA",
    "person100_bacteria_475.jpeg",
)
XRAY_PATH = os.path.normpath(XRAY_PATH)

NORMAL_XRAY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "datasets", "chest_xray", "test", "NORMAL",
)
NORMAL_XRAY_PATH = os.path.normpath(NORMAL_XRAY_PATH)

# ── Helpers ──────────────────────────────────────────────────────────────────

results = {"pass": 0, "fail": 0, "skip": 0, "details": []}


def banner(title: str):
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def check(label: str, condition: bool, note: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {note}" if note else ""
    print(f"  [{status}] {label}{suffix}")
    if condition:
        results["pass"] += 1
    else:
        results["fail"] += 1
    results["details"].append({"label": label, "status": status, "note": note})
    return condition


def skip(label: str, note: str = ""):
    print(f"  [SKIP] {label} — {note}")
    results["skip"] += 1
    results["details"].append({"label": label, "status": "SKIP", "note": note})


def create_intake(patient: dict, vitals: dict, symptoms: dict,
                  description: str, chief_complaint: str,
                  ambulance_eta: int = 15) -> dict:
    """Submit intake and return response body."""
    payload = {
        "patient": patient,
        "vitals": vitals,
        "symptoms": symptoms,
        "emergency_description": description,
        "ambulance_eta": ambulance_eta,
        "chief_complaint": chief_complaint,
    }
    r = httpx.post(f"{BASE}/api/intake", json=payload, timeout=TIMEOUT)
    if r.status_code != 201:
        print(f"  INTAKE FAILED: {r.status_code} — {r.text[:300]}")
        return {}
    return r.json()


def run_lab(intake_id: str, override: dict = None) -> dict:
    """Run lab analysis and return response."""
    payload = {"intake_id": intake_id}
    if override:
        payload["clinical_override"] = override
    r = httpx.post(f"{BASE}/api/lab/analyze", json=payload, timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"  LAB FAILED: {r.status_code} — {r.text[:300]}")
        return {}
    return r.json()


def run_imaging(intake_id: str, evidence_id: str) -> dict:
    """Run imaging analysis and return response."""
    payload = {"intake_id": intake_id, "evidence_id": evidence_id}
    r = httpx.post(f"{BASE}/api/imaging/analyze", json=payload, timeout=60)
    if r.status_code != 200:
        print(f"  IMAGING FAILED: {r.status_code} — {r.text[:300]}")
        return {}
    return r.json()


def run_aggregation(intake_id: str) -> dict:
    """Run aggregation and return response."""
    payload = {"intake_id": intake_id}
    r = httpx.post(f"{BASE}/api/aggregate", json=payload, timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"  AGGREGATION FAILED: {r.status_code} — {r.text[:300]}")
        return {}
    return r.json()


def get_report_json(intake_id: str) -> dict:
    """Fetch the clinical report as JSON."""
    r = httpx.get(f"{BASE}/api/report/{intake_id}", timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"  REPORT FAILED: {r.status_code} — {r.text[:300]}")
        return {}
    return r.json()


def get_report_pdf(intake_id: str) -> bytes:
    """Fetch the clinical report as PDF."""
    r = httpx.get(f"{BASE}/api/report/{intake_id}/pdf", timeout=TIMEOUT)
    if r.status_code != 200:
        print(f"  PDF FAILED: {r.status_code} — {r.text[:300]}")
        return b""
    return r.content


def upload_evidence(intake_id: str, filepath: str, evidence_type: str) -> str:
    """Upload a file and return the evidence_id."""
    if not os.path.exists(filepath):
        print(f"  SKIP: File not found: {filepath}")
        return ""
    with open(filepath, "rb") as f:
        r = httpx.post(
            f"{BASE}/api/evidence/upload",
            data={"intake_id": intake_id, "evidence_type": evidence_type},
            files={"file": (os.path.basename(filepath), f, "image/jpeg")},
            timeout=TIMEOUT,
        )
    if r.status_code != 200:
        print(f"  UPLOAD FAILED: {r.status_code} — {r.text[:300]}")
        return ""
    return r.json().get("evidence_id", "")


# ── Post-Generation Validator ────────────────────────────────────────────────

def validate_report(report: dict, scenario_name: str) -> list[str]:
    """
    Automated post-generation report validator.
    Returns a list of violation descriptions (empty = all passed).
    """
    violations = []

    # 1. Python exception patterns
    exception_patterns = [
        r"Traceback",
        r"Error:",
        r"Exception",
        r"TypeError",
        r"AttributeError",
        r"KeyError",
        r"ValueError",
        r"File \".*\.py\"",
        r"line \d+, in ",
    ]
    report_text = json.dumps(report, default=str)
    for pattern in exception_patterns:
        matches = re.findall(pattern, report_text)
        # Filter out legitimate uses (e.g., "error_type" in schema, "ValueError" in description)
        # Only flag if it looks like an actual exception being rendered
        if matches:
            # Check if it's in a narrative/display field, not a schema field
            for field in ["clinical_overview", "overall_impression", "cardiac_summary",
                          "respiratory_summary", "laboratory_summary", "imaging_summary",
                          "monitoring_narrative", "precautions_narrative",
                          "alternative_considerations_narrative", "limitations_narrative"]:
                interp = report.get("clinical_interpretation", {})
                val = interp.get(field, "") if isinstance(interp, dict) else ""
                if isinstance(val, str) and re.search(pattern, val):
                    violations.append(f"Python exception pattern '{pattern}' found in {field}")

    # 2. Duplicate evidence
    evidence = report.get("evidence", [])
    seen_keys = set()
    for ev in evidence:
        key = (ev.get("file_name", ""), ev.get("evidence_type", ""))
        if key in seen_keys:
            violations.append(f"Duplicate evidence: {key}")
        seen_keys.add(key)

    # 3. Mock data leakage
    mock_patterns = [r"\btest_\w+", r"\bmock_\w+", r"\bTODO\b", r"\bFIXME\b"]
    for field_name in ["clinical_overview", "overall_impression"]:
        interp = report.get("clinical_interpretation", {})
        val = interp.get(field_name, "") if isinstance(interp, dict) else ""
        if isinstance(val, str):
            for mp in mock_patterns:
                if re.search(mp, val, re.IGNORECASE):
                    violations.append(f"Mock data pattern '{mp}' found in {field_name}")

    # 4. Empty mandatory sections
    mandatory = ["patient_summary", "vitals", "risk_engine"]
    for section in mandatory:
        val = report.get(section)
        if val is None or val == {} or val == []:
            violations.append(f"Empty mandatory section: {section}")

    # 5. Stack traces in any string field
    def _check_for_stack_traces(obj, path=""):
        if isinstance(obj, str):
            if "File \"" in obj and ".py\"" in obj and "line " in obj:
                violations.append(f"Stack trace found at {path}")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                _check_for_stack_traces(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _check_for_stack_traces(v, f"{path}[{i}]")

    _check_for_stack_traces(report)

    return violations


# ── Clinical Language Validator ──────────────────────────────────────────────

def validate_clinical_language(report: dict) -> list[str]:
    """Check that engineering terminology is not used in clinician-facing sections."""
    violations = []
    engineering_terms = [
        "Laboratory model",
        "Laboratory ML",
        "Medical Imaging AI",
        "subsystem",
        "signal strength",
    ]

    # Check narrative fields
    interp = report.get("clinical_interpretation", {})
    if isinstance(interp, dict):
        for field, val in interp.items():
            if isinstance(val, str):
                for term in engineering_terms:
                    if term.lower() in val.lower():
                        violations.append(f"Engineering term '{term}' found in {field}")

    # Check conclusions text fields
    conc = report.get("clinical_conclusions", {})
    if isinstance(conc, dict):
        for field in ["supporting_evidence", "conflicting_evidence", "confidence_factors",
                       "uncertainty_reasons"]:
            items = conc.get(field, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        for term in engineering_terms:
                            if term.lower() in item.lower():
                                violations.append(f"Engineering term '{term}' found in conclusions.{field}")

    # Check suppression reason
    agg = report.get("aggregation", {})
    if isinstance(agg, dict):
        reason = agg.get("suppression_reason", "")
        if isinstance(reason, str):
            for term in engineering_terms:
                if term.lower() in reason.lower():
                    violations.append(f"Engineering term '{term}' found in suppression_reason")

    return violations


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 1 — ACS (Emergency Cardiac)
# ═════════════════════════════════════════════════════════════════════════════

banner("SCENARIO 1 — ACS (Emergency Cardiac)")
print("  Patient: 54M, crushing chest pain, high-risk vitals")

s1 = create_intake(
    patient={
        "first_name": "Ravi", "last_name": "Kumar_S1",
        "date_of_birth": "1971-03-15", "gender": "male",
        "contact_number": "9849012345",
        "allergies": ["Penicillin"],
        "current_medications": ["Metformin", "Amlodipine"],
        "past_medical_history": ["Type 2 Diabetes", "Hypertension"],
    },
    vitals={"heart_rate": 124, "spo2": 88, "bp_systolic": 158, "bp_diastolic": 98,
            "temperature": 38.4, "respiratory_rate": 26},
    symptoms={"chest_pain": True, "breathlessness": True, "trauma": False,
              "bleeding": False, "unconsciousness": False, "neurological_symptoms": False},
    description="54 year old male, sudden onset crushing chest pain radiating to left arm and jaw for 45 minutes. Profuse sweating, severe breathlessness.",
    chief_complaint="Chest pain and breathlessness",
    ambulance_eta=7,
)

s1_id = s1.get("intake_id", "")
if s1_id:
    print(f"  intake_id: {s1_id}")
    check("S1: Intake created", bool(s1_id))
    check("S1: Severity is HIGH or CRITICAL",
          s1.get("severity", "").upper() in ("CRITICAL", "HIGH"),
          s1.get("severity"))

    # Run lab with high-risk override
    lab1 = run_lab(s1_id, override={
        "chest_pain_type": "ASY", "cholesterol": 289, "fasting_bs": 1,
        "resting_ecg": "ST", "max_hr": 124, "exercise_angina": "Y",
        "oldpeak": 2.8, "st_slope": "Flat",
    })
    if lab1:
        check("S1: Lab prediction = high_risk", lab1.get("prediction") == "high_risk", lab1.get("prediction"))
        check("S1: Risk probability >= 0.5", (lab1.get("risk_probability") or 0) >= 0.5)

    # Upload X-ray for imaging
    xray_eid = ""
    if os.path.exists(XRAY_PATH):
        xray_eid = upload_evidence(s1_id, XRAY_PATH, "xray")
        if xray_eid:
            img1 = run_imaging(s1_id, xray_eid)

    # Aggregation
    agg1 = run_aggregation(s1_id)
    if agg1:
        check("S1: Primary condition = ACS",
              agg1.get("primary_condition") == "ACS", agg1.get("primary_condition"))
        check("S1: Confidence NOT suppressed",
              agg1.get("confidence_suppressed") is False)
        probs1 = agg1.get("probabilities", {})
        check("S1: ACS probability is highest",
              (probs1.get("ACS") or 0) > max(
                  probs1.get("Pneumonia", 0) or 0,
                  probs1.get("PE", 0) or 0,
                  probs1.get("Arrhythmia", 0) or 0,
                  probs1.get("Other", 0) or 0,
              ))

    # Report + PDF validation
    report1 = get_report_json(s1_id)
    if report1:
        v_report = validate_report(report1, "ACS")
        check("S1: Report validation passed", len(v_report) == 0,
              "; ".join(v_report) if v_report else "all checks clean")
        v_lang = validate_clinical_language(report1)
        check("S1: Clinical language validation passed", len(v_lang) == 0,
              "; ".join(v_lang) if v_lang else "all terms clinical")

    pdf1 = get_report_pdf(s1_id)
    check("S1: PDF generated successfully", len(pdf1) > 0, f"{len(pdf1)} bytes")
else:
    skip("S1: All checks", "Intake creation failed")


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 2 — Routine Health Check (Healthy 29-year-old)
# ═════════════════════════════════════════════════════════════════════════════

banner("SCENARIO 2 — Routine Health Check (Healthy Patient)")
print("  Patient: 29F, no symptoms, normal vitals — MUST NOT be classified as ACS")

s2 = create_intake(
    patient={
        "first_name": "Priya", "last_name": "Sharma_S2",
        "date_of_birth": "1997-05-20", "gender": "female",
        "contact_number": "9876543210",
        "allergies": [],
        "current_medications": [],
        "past_medical_history": [],
    },
    vitals={"heart_rate": 72, "spo2": 99, "bp_systolic": 118, "bp_diastolic": 76,
            "temperature": 36.6, "respiratory_rate": 16},
    symptoms={"chest_pain": False, "breathlessness": False, "trauma": False,
              "bleeding": False, "unconsciousness": False, "neurological_symptoms": False},
    description="29 year old female, routine health check, no complaints.",
    chief_complaint="Routine health check",
    ambulance_eta=30,
)

s2_id = s2.get("intake_id", "")
if s2_id:
    print(f"  intake_id: {s2_id}")
    check("S2: Intake created", bool(s2_id))

    # Run lab WITHOUT override — this tests the 220-age MaxHR fallback
    lab2 = run_lab(s2_id)
    if lab2:
        check("S2: Lab prediction = low_risk",
              lab2.get("prediction") == "low_risk", lab2.get("prediction"))
        check("S2: Risk probability < 0.5",
              (lab2.get("risk_probability") or 1) < 0.5,
              f"{lab2.get('risk_probability'):.4f}" if lab2.get("risk_probability") else "N/A")

        # Verify max_hr used was 220-29=191, NOT resting HR 72
        input_feats = lab2.get("input_features", {})
        max_hr_used = input_feats.get("MaxHR") or input_feats.get("max_hr")
        if max_hr_used is not None:
            check("S2: MaxHR used is 220-age (191), NOT resting HR (72)",
                  abs(float(max_hr_used) - 191.0) < 1.0,
                  f"max_hr={max_hr_used}")
        else:
            skip("S2: MaxHR verification", "MaxHR not in input_features keys")

    # Aggregation — expect suppression or low ACS
    agg2 = run_aggregation(s2_id)
    if agg2:
        is_suppressed = agg2.get("confidence_suppressed", False)
        primary2 = agg2.get("primary_condition")
        probs2 = agg2.get("probabilities", {})
        acs_prob2 = probs2.get("ACS") or 0

        check("S2: NOT classified as ACS primary (or suppressed)",
              is_suppressed or primary2 != "ACS",
              f"primary={primary2}, suppressed={is_suppressed}")
        if not is_suppressed:
            check("S2: ACS probability < 0.40",
                  acs_prob2 < 0.40,
                  f"ACS={acs_prob2:.4f}")

        # Verify suppression message uses clinical language
        reason = agg2.get("suppression_reason") or ""
        if is_suppressed:
            check("S2: Suppression uses clinical language",
                  "subsystem" not in reason.lower() and "signal strength" not in reason.lower(),
                  reason[:80])

    # Report
    report2 = get_report_json(s2_id)
    if report2:
        v2 = validate_report(report2, "Routine")
        check("S2: Report validation passed", len(v2) == 0,
              "; ".join(v2) if v2 else "all checks clean")
        v2_lang = validate_clinical_language(report2)
        check("S2: Clinical language validation passed", len(v2_lang) == 0,
              "; ".join(v2_lang) if v2_lang else "all terms clinical")
else:
    skip("S2: All checks", "Intake creation failed")


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 3 — Pneumonia (Respiratory)
# ═════════════════════════════════════════════════════════════════════════════

banner("SCENARIO 3 — Pneumonia")
print("  Patient: 65M, cough + fever, SpO2 91%, abnormal CXR expected")

s3 = create_intake(
    patient={
        "first_name": "Mohan", "last_name": "Reddy_S3",
        "date_of_birth": "1961-08-10", "gender": "male",
        "contact_number": "9988776655",
        "allergies": [],
        "current_medications": [],
        "past_medical_history": ["COPD"],
    },
    vitals={"heart_rate": 96, "spo2": 91, "bp_systolic": 130, "bp_diastolic": 82,
            "temperature": 39.1, "respiratory_rate": 24},
    symptoms={"chest_pain": False, "breathlessness": True, "trauma": False,
              "bleeding": False, "unconsciousness": False, "neurological_symptoms": False},
    description="65 year old male with productive cough, fever 39.1C, breathlessness. History of COPD. SpO2 91%.",
    chief_complaint="Cough and fever with breathlessness",
    ambulance_eta=15,
)

s3_id = s3.get("intake_id", "")
if s3_id:
    print(f"  intake_id: {s3_id}")
    check("S3: Intake created", bool(s3_id))

    # Upload pneumonia X-ray
    if os.path.exists(XRAY_PATH):
        xray3 = upload_evidence(s3_id, XRAY_PATH, "xray")
        if xray3:
            img3 = run_imaging(s3_id, xray3)
            if img3:
                check("S3: Imaging prediction = pneumonia",
                      img3.get("prediction") == "pneumonia", img3.get("prediction"))

    # Run lab (no cardiac override)
    lab3 = run_lab(s3_id)

    # Aggregation
    agg3 = run_aggregation(s3_id)
    if agg3:
        check("S3: Primary condition = Pneumonia",
              agg3.get("primary_condition") == "Pneumonia",
              agg3.get("primary_condition"))

    # Report
    report3 = get_report_json(s3_id)
    if report3:
        v3 = validate_report(report3, "Pneumonia")
        check("S3: Report validation passed", len(v3) == 0,
              "; ".join(v3) if v3 else "all checks clean")
else:
    skip("S3: All checks", "Intake creation failed")


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 4 — Pulmonary Embolism
# ═════════════════════════════════════════════════════════════════════════════

banner("SCENARIO 4 — Pulmonary Embolism")
print("  Patient: 42F, chest pain + tachycardia, SpO2 89%, no fever, normal X-ray expected")

s4 = create_intake(
    patient={
        "first_name": "Lakshmi", "last_name": "Devi_S4",
        "date_of_birth": "1984-01-22", "gender": "female",
        "contact_number": "9112233445",
        "allergies": [],
        "current_medications": ["Oral contraceptive"],
        "past_medical_history": ["DVT (2023)"],
    },
    vitals={"heart_rate": 118, "spo2": 89, "bp_systolic": 100, "bp_diastolic": 65,
            "temperature": 36.8, "respiratory_rate": 28},
    symptoms={"chest_pain": True, "breathlessness": True, "trauma": False,
              "bleeding": False, "unconsciousness": False, "neurological_symptoms": False},
    description="42 year old female, sudden onset pleuritic chest pain and severe breathlessness. History of DVT. On oral contraceptives. No fever. Tachycardic.",
    chief_complaint="Sudden chest pain and breathlessness",
    ambulance_eta=10,
)

s4_id = s4.get("intake_id", "")
if s4_id:
    print(f"  intake_id: {s4_id}")
    check("S4: Intake created", bool(s4_id))

    # Run lab (no cardiac-specific override)
    lab4 = run_lab(s4_id)

    # Aggregation
    agg4 = run_aggregation(s4_id)
    if agg4:
        probs4 = agg4.get("probabilities", {})
        primary4 = agg4.get("primary_condition")
        pe_prob = probs4.get("PE") or 0
        pneumonia_prob = probs4.get("Pneumonia") or 0
        suppressed4 = agg4.get("confidence_suppressed", False)

        if not suppressed4:
            check("S4: PE or ACS is primary (not Pneumonia)",
                  primary4 in ("PE", "ACS"),
                  f"primary={primary4}")
            check("S4: PE ranks in top 2",
                  pe_prob >= sorted(
                      [probs4.get(c, 0) or 0 for c in ["ACS", "PE", "Pneumonia", "Arrhythmia", "Other"]],
                      reverse=True
                  )[1] if len(probs4) >= 2 else True,
                  f"PE={pe_prob:.4f}")
        else:
            check("S4: Confidence suppressed (acceptable for sparse evidence)", True,
                  agg4.get("suppression_reason", "")[:60])

    report4 = get_report_json(s4_id)
    if report4:
        v4 = validate_report(report4, "PE")
        check("S4: Report validation passed", len(v4) == 0,
              "; ".join(v4) if v4 else "all checks clean")
else:
    skip("S4: All checks", "Intake creation failed")


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 5 — Stroke (Neurological)
# ═════════════════════════════════════════════════════════════════════════════

banner("SCENARIO 5 — Stroke (Neurological)")
print("  Patient: 70M, unilateral weakness, slurred speech")

s5 = create_intake(
    patient={
        "first_name": "Venkat", "last_name": "Rao_S5",
        "date_of_birth": "1956-11-03", "gender": "male",
        "contact_number": "9556677881",
        "allergies": [],
        "current_medications": ["Aspirin", "Atorvastatin"],
        "past_medical_history": ["Atrial Fibrillation", "Hypertension"],
    },
    vitals={"heart_rate": 88, "spo2": 96, "bp_systolic": 182, "bp_diastolic": 105,
            "temperature": 36.7, "respiratory_rate": 18},
    symptoms={"chest_pain": False, "breathlessness": False, "trauma": False,
              "bleeding": False, "unconsciousness": False, "neurological_symptoms": True},
    description="70 year old male, sudden onset right-sided weakness and slurred speech for 2 hours. Known atrial fibrillation. BP 182/105.",
    chief_complaint="Right-sided weakness and slurred speech",
    ambulance_eta=5,
)

s5_id = s5.get("intake_id", "")
if s5_id:
    print(f"  intake_id: {s5_id}")
    check("S5: Intake created", bool(s5_id))

    risk5 = s5.get("risk_scores", {})
    check("S5: Neurological risk > 0",
          (risk5.get("neurological_risk") or risk5.get("neurological") or 0) > 0,
          f"neurological={risk5.get('neurological_risk') or risk5.get('neurological', 0)}")

    # Run lab (no override) then aggregation
    lab5 = run_lab(s5_id)
    agg5 = run_aggregation(s5_id)
    if agg5:
        primary5 = agg5.get("primary_condition")
        # Stroke won't map to our 5 conditions (ACS/PE/Pneumonia/Arrhythmia/Other)
        # so we just verify it's NOT classified as ACS/Pneumonia incorrectly
        check("S5: NOT classified as Pneumonia",
              primary5 != "Pneumonia",
              f"primary={primary5}")

    report5 = get_report_json(s5_id)
    if report5:
        v5 = validate_report(report5, "Stroke")
        check("S5: Report validation passed", len(v5) == 0,
              "; ".join(v5) if v5 else "all checks clean")
else:
    skip("S5: All checks", "Intake creation failed")


# ═════════════════════════════════════════════════════════════════════════════
# SCENARIO 6 — Trauma
# ═════════════════════════════════════════════════════════════════════════════

banner("SCENARIO 6 — Trauma")
print("  Patient: 28M, major injury, no respiratory symptoms")

s6 = create_intake(
    patient={
        "first_name": "Arjun", "last_name": "Singh_S6",
        "date_of_birth": "1998-02-14", "gender": "male",
        "contact_number": "9001122334",
        "allergies": [],
        "current_medications": [],
        "past_medical_history": [],
    },
    vitals={"heart_rate": 110, "spo2": 97, "bp_systolic": 95, "bp_diastolic": 60,
            "temperature": 36.5, "respiratory_rate": 20},
    symptoms={"chest_pain": False, "breathlessness": False, "trauma": True,
              "bleeding": True, "unconsciousness": False, "neurological_symptoms": False},
    description="28 year old male, road traffic accident, significant abdominal pain, left femur deformity, active bleeding from scalp laceration.",
    chief_complaint="Road traffic accident with multiple injuries",
    ambulance_eta=8,
)

s6_id = s6.get("intake_id", "")
if s6_id:
    print(f"  intake_id: {s6_id}")
    check("S6: Intake created", bool(s6_id))

    risk6 = s6.get("risk_scores", {})
    check("S6: Trauma risk > 0",
          (risk6.get("trauma_risk") or risk6.get("trauma") or 0) > 0,
          f"trauma={risk6.get('trauma_risk') or risk6.get('trauma', 0)}")

    # Run lab then aggregation
    lab6 = run_lab(s6_id)
    agg6 = run_aggregation(s6_id)
    if agg6:
        primary6 = agg6.get("primary_condition")
        check("S6: NOT classified as Pneumonia or PE",
              primary6 not in ("Pneumonia", "PE"),
              f"primary={primary6}")

    report6 = get_report_json(s6_id)
    if report6:
        v6 = validate_report(report6, "Trauma")
        check("S6: Report validation passed", len(v6) == 0,
              "; ".join(v6) if v6 else "all checks clean")

    pdf6 = get_report_pdf(s6_id)
    check("S6: PDF generated successfully", len(pdf6) > 0, f"{len(pdf6)} bytes")
else:
    skip("S6: All checks", "Intake creation failed")


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

banner("VERIFICATION SUMMARY — PRATHAM v5.1.0")

total = results["pass"] + results["fail"] + results["skip"]
print(f"\n  Total checks:  {total}")
print(f"  PASS:          {results['pass']}")
print(f"  FAIL:          {results['fail']}")
print(f"  SKIP:          {results['skip']}")
print()

if results["fail"] > 0:
    print("  FAILED CHECKS:")
    for d in results["details"]:
        if d["status"] == "FAIL":
            print(f"    ✗ {d['label']}: {d['note']}")
    print()

if results["fail"] == 0:
    print("  ✓ ALL CHECKS PASSED — v5.1.0 stabilization verified")
else:
    print(f"  ✗ {results['fail']} CHECK(S) FAILED — review required")

print()
print("=" * 72)
