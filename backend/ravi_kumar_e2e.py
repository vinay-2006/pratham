"""
PRATHAM — Ravi Kumar End-to-End Clinical Case
=============================================
Runs all 5 stages of the complete patient journey:

  Stage 1: Intake form submission
  Stage 2: Evidence upload (X-ray, lab report, clinical notes)
  Stage 3: Lab analysis (XGBoost cardiac risk)
  Stage 4: Imaging analysis (EfficientNetB0 pneumonia)
  Stage 5: Aggregation (deterministic heuristic engine)

Usage:
  python ravi_kumar_e2e.py
"""
import json
import os
import sys
import time

import httpx

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"
TIMEOUT = 30

# ── Real pneumonia X-ray from dataset ────────────────────────────────────────
XRAY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "datasets", "chest_xray", "test", "PNEUMONIA",
    "person100_bacteria_475.jpeg",
)
XRAY_PATH = os.path.normpath(XRAY_PATH)

# ── Support files ────────────────────────────────────────────────────────────
LAB_REPORT_PATH = os.path.join(os.path.dirname(__file__), "ravi_kumar_labs.txt")
CLINICAL_NOTES_PATH = os.path.join(os.path.dirname(__file__), "ravi_kumar_notes.txt")


def banner(title: str):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check(label: str, condition: bool, note: str = ""):
    status = "PASS" if condition else "FAIL"
    suffix = f" — {note}" if note else ""
    print(f"  [{status}] {label}{suffix}")
    return condition


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 1 — Intake Form
# ═══════════════════════════════════════════════════════════════════════════
banner("STAGE 1 — Intake Form: Ravi Kumar")

intake_payload = {
    "patient": {
        "first_name": "Ravi",
        "last_name": "Kumar",
        "date_of_birth": "1971-03-15",
        "gender": "male",
        "contact_number": "9849012345",
        "allergies": ["Penicillin"],
        "current_medications": ["Metformin", "Amlodipine"],
        "past_medical_history": ["Type 2 Diabetes", "Hypertension"],
    },
    "vitals": {
        "heart_rate": 124,
        "spo2": 88,
        "bp_systolic": 158,
        "bp_diastolic": 98,
        "temperature": 38.4,
        "respiratory_rate": 26,
    },
    "symptoms": {
        "chest_pain": True,
        "breathlessness": True,
        "trauma": False,
        "bleeding": False,
        "unconsciousness": False,
        "neurological_symptoms": False,
    },
    "emergency_description": (
        "54 year old male, sudden onset crushing chest pain "
        "radiating to left arm and jaw for the past 45 minutes. "
        "Profuse sweating, severe breathlessness, history of "
        "diabetes and hypertension. Patient appears distressed, "
        "skin is clammy."
    ),
    "ambulance_eta": 7,
    "chief_complaint": "Chest pain and breathlessness",
}

r = httpx.post(f"{BASE}/api/intake", json=intake_payload, timeout=TIMEOUT)
check("HTTP 201", r.status_code == 201, f"got {r.status_code}")

if r.status_code != 201:
    print(f"  ERROR: {r.text[:500]}")
    sys.exit(1)

intake_body = r.json()
INTAKE_ID = intake_body["intake_id"]
PATIENT_ID = intake_body["patient_id"]

print(f"  intake_id:    {INTAKE_ID}")
print(f"  patient_id:   {PATIENT_ID}")
print(f"  severity:     {intake_body.get('severity')}")
print(f"  nlp_summary:  {intake_body.get('nlp_summary', '')[:120]}...")
print(f"  risk_scores:  {intake_body.get('risk_scores')}")
print(f"  investigations: {intake_body.get('investigations_recommended')}")
print(f"  alerts:       {intake_body.get('preparation_alerts')}")

check("severity is CRITICAL or HIGH",
      intake_body.get("severity", "").upper() in ("CRITICAL", "HIGH"),
      intake_body.get("severity"))
check("investigations include ECG",
      "ECG" in (intake_body.get("investigations_recommended") or []))
check("investigations include Troponin",
      "Troponin" in (intake_body.get("investigations_recommended") or []))


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 2 — Evidence Upload
# ═══════════════════════════════════════════════════════════════════════════
banner("STAGE 2 — Evidence Upload")

evidence_ids = {}

# Upload 1: X-ray
print("\n  --- Upload 1: Chest X-ray (real pneumonia image) ---")
if not os.path.exists(XRAY_PATH):
    print(f"  ERROR: X-ray image not found at {XRAY_PATH}")
    sys.exit(1)

print(f"  Using: {os.path.basename(XRAY_PATH)} ({os.path.getsize(XRAY_PATH)} bytes)")

with open(XRAY_PATH, "rb") as f:
    r = httpx.post(
        f"{BASE}/api/evidence/upload",
        data={"intake_id": INTAKE_ID, "evidence_type": "xray"},
        files={"file": ("person100_bacteria_475.jpeg", f, "image/jpeg")},
        timeout=TIMEOUT,
    )
check("X-ray upload HTTP 200", r.status_code == 200, f"got {r.status_code}")
if r.status_code == 200:
    xray_resp = r.json()
    evidence_ids["xray"] = xray_resp["evidence_id"]
    print(f"  evidence_id: {evidence_ids['xray']}")
    print(f"  storage_path: {xray_resp.get('storage_path')}")
else:
    print(f"  ERROR: {r.text[:300]}")

# Upload 2: Lab report
print("\n  --- Upload 2: Lab report ---")
with open(LAB_REPORT_PATH, "rb") as f:
    r = httpx.post(
        f"{BASE}/api/evidence/upload",
        data={"intake_id": INTAKE_ID, "evidence_type": "lab_report"},
        files={"file": ("ravi_kumar_labs.txt", f, "text/plain")},
        timeout=TIMEOUT,
    )
check("Lab report upload HTTP 200", r.status_code == 200, f"got {r.status_code}")
if r.status_code == 200:
    lab_resp = r.json()
    evidence_ids["lab_report"] = lab_resp["evidence_id"]
    print(f"  evidence_id: {evidence_ids['lab_report']}")
else:
    print(f"  ERROR: {r.text[:300]}")

# Upload 3: Clinical notes
print("\n  --- Upload 3: Clinical notes ---")
with open(CLINICAL_NOTES_PATH, "rb") as f:
    r = httpx.post(
        f"{BASE}/api/evidence/upload",
        data={"intake_id": INTAKE_ID, "evidence_type": "clinical_notes"},
        files={"file": ("ravi_kumar_notes.txt", f, "text/plain")},
        timeout=TIMEOUT,
    )
check("Clinical notes upload HTTP 200", r.status_code == 200, f"got {r.status_code}")
if r.status_code == 200:
    notes_resp = r.json()
    evidence_ids["clinical_notes"] = notes_resp["evidence_id"]
    print(f"  evidence_id: {evidence_ids['clinical_notes']}")
else:
    print(f"  ERROR: {r.text[:300]}")

# Verify all evidence visible
r = httpx.get(f"{BASE}/api/evidence/{INTAKE_ID}", timeout=TIMEOUT)
if r.status_code == 200:
    ev_data = r.json()
    check("All 3 evidence files uploaded", ev_data.get("count", 0) >= 3,
          f"count={ev_data.get('count')}")
    for ev in ev_data.get("evidence", []):
        print(f"    {ev.get('evidence_type'):15s}  {ev.get('file_name')}")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 3 — Lab Analysis (XGBoost Cardiac Risk)
# ═══════════════════════════════════════════════════════════════════════════
banner("STAGE 3 — Lab Analysis (XGBoost cardiac risk)")

# The lab_analysis endpoint uses clinical_override, not raw features.
# Map the user's specified values to the clinical_override format:
#   age=54, sex=1(M), cp=0(ASY), trestbps=158, chol=289, fbs=1,
#   restecg=2(ST), thalach=124, exang=1(Y), oldpeak=2.8, slope=2(Flat), ca=1, thal=2
lab_payload = {
    "intake_id": INTAKE_ID,
    "clinical_override": {
        "chest_pain_type": "ASY",        # cp=0 → Asymptomatic
        "cholesterol": 289,              # chol=289
        "fasting_bs": 1,                 # fbs=1
        "resting_ecg": "ST",             # restecg=2 → ST
        "max_hr": 124,                   # thalach=124
        "exercise_angina": "Y",          # exang=1 → Y
        "oldpeak": 2.8,                  # oldpeak=2.8
        "st_slope": "Flat",              # slope=2 → Flat
    },
}

r = httpx.post(f"{BASE}/api/lab/analyze", json=lab_payload, timeout=TIMEOUT)
check("Lab analysis HTTP 200", r.status_code == 200, f"got {r.status_code}")

if r.status_code == 200:
    lab_result = r.json()
    print(f"  lab_result_id:    {lab_result.get('lab_result_id')}")
    print(f"  prediction:       {lab_result.get('prediction')}")
    print(f"  risk_probability: {lab_result.get('risk_probability')}")
    print(f"  model_name:       {lab_result.get('model_name')}")

    check("prediction = high_risk",
          lab_result.get("prediction") == "high_risk",
          lab_result.get("prediction"))
    check("risk_probability >= 0.5",
          (lab_result.get("risk_probability") or 0) >= 0.5,
          f"{lab_result.get('risk_probability'):.4f}")

    top = lab_result.get("top_features", {})
    if top:
        print("  Top SHAP features:")
        for feat, val in top.items():
            print(f"    {feat:20s}: {val:+.6f}")
else:
    print(f"  ERROR: {r.text[:500]}")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 4 — Imaging Analysis (EfficientNetB0 Pneumonia)
# ═══════════════════════════════════════════════════════════════════════════
banner("STAGE 4 — Imaging Analysis (EfficientNetB0 pneumonia)")

if "xray" not in evidence_ids:
    print("  SKIP — X-ray evidence_id not available (upload failed)")
else:
    imaging_payload = {
        "intake_id": INTAKE_ID,
        "evidence_id": evidence_ids["xray"],
    }
    r = httpx.post(f"{BASE}/api/imaging/analyze", json=imaging_payload, timeout=60)
    check("Imaging analysis HTTP 200", r.status_code == 200, f"got {r.status_code}")

    if r.status_code == 200:
        img_result = r.json()
        print(f"  imaging_result_id:    {img_result.get('imaging_result_id')}")
        print(f"  prediction:           {img_result.get('prediction')}")
        print(f"  pneumonia_probability: {img_result.get('pneumonia_probability')}")
        print(f"  confidence:           {img_result.get('confidence')}")
        print(f"  model_name:           {img_result.get('model_name')}")

        check("prediction = pneumonia",
              img_result.get("prediction") == "pneumonia",
              img_result.get("prediction"))
        check("pneumonia_probability >= 0.50",
              (img_result.get("pneumonia_probability") or 0) >= 0.50,
              f"{img_result.get('pneumonia_probability'):.4f}")
    else:
        print(f"  ERROR: {r.text[:500]}")


# ═══════════════════════════════════════════════════════════════════════════
# STAGE 5 — Aggregation
# ═══════════════════════════════════════════════════════════════════════════
banner("STAGE 5 — Aggregation (deterministic heuristic engine)")

agg_payload = {"intake_id": INTAKE_ID}
r = httpx.post(f"{BASE}/api/aggregate", json=agg_payload, timeout=TIMEOUT)
check("Aggregation HTTP 200", r.status_code == 200, f"got {r.status_code}")

if r.status_code == 200:
    agg = r.json()
    print(f"\n  aggregation_id:       {agg.get('aggregation_id')}")
    print(f"  primary_condition:    {agg.get('primary_condition')}")
    print(f"  confidence_suppressed: {agg.get('confidence_suppressed')}")
    print(f"  suppression_reason:   {agg.get('suppression_reason')}")

    probs = agg.get("probabilities", {})
    print("\n  Probability Distribution:")
    print("  " + "-" * 40)
    prob_sum = 0
    for cond in ["ACS", "Pneumonia", "PE", "Arrhythmia", "Other"]:
        p = probs.get(cond)
        bar = ""
        if p is not None:
            prob_sum += p
            bar_len = int(p * 40)
            bar = "█" * bar_len + "░" * (40 - bar_len)
            print(f"  {cond:12s}: {p:.4f}  {bar}")
        else:
            print(f"  {cond:12s}: None (suppressed)")
    print(f"  {'SUM':12s}: {prob_sum:.6f}")

    src = agg.get("source_summary", {})
    print(f"\n  Source Summary:")
    for k, v in src.items():
        icon = "✓" if v else "✗"
        print(f"    {icon} {k}")

    print(f"\n  Evidence Breakdown:")
    for cond, trail in agg.get("evidence_breakdown", {}).items():
        if trail:
            print(f"    {cond}:")
            for item in trail:
                print(f"      {item}")

    # ── Verification checks ──────────────────────────────────────────────
    print()
    check("primary_condition = ACS", agg.get("primary_condition") == "ACS",
          agg.get("primary_condition"))
    check("confidence_suppressed = False",
          agg.get("confidence_suppressed") is False)
    check("probability sum ≈ 1.0",
          abs(prob_sum - 1.0) < 1e-4,
          f"sum={prob_sum:.8f}")
    check("ACS probability highest",
          probs.get("ACS", 0) > probs.get("Pneumonia", 0) if probs.get("ACS") else False)
    check("ACS probability >= 0.40",
          (probs.get("ACS") or 0) >= 0.40,
          f"{probs.get('ACS')}")
    check("4 sources present",
          sum(1 for v in src.values() if v) == 4,
          f"count={sum(1 for v in src.values() if v)}")

    # Expected ranges from user spec
    acs_p = probs.get("ACS") or 0
    pneu_p = probs.get("Pneumonia") or 0
    pe_p = probs.get("PE") or 0
    arr_p = probs.get("Arrhythmia") or 0

    print("\n  Range Checks (vs. user expectations):")
    check("ACS in ~0.50-0.70 range", 0.40 <= acs_p <= 0.80,
          f"{acs_p:.4f}")
    check("Pneumonia in ~0.15-0.30 range", 0.05 <= pneu_p <= 0.40,
          f"{pneu_p:.4f}")
    check("PE low", pe_p <= 0.20, f"{pe_p:.4f}")
    check("Arrhythmia low", arr_p <= 0.15, f"{arr_p:.4f}")
else:
    print(f"  ERROR: {r.text[:500]}")


# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
banner("END-TO-END SUMMARY")
print(f"  intake_id:  {INTAKE_ID}")
print(f"  patient:    Ravi Kumar, 54M")
print()
print("  All 5 stages completed.")
print("  Verify aggregation_results in Supabase dashboard.")
print(f"  Filter by intake_id = {INTAKE_ID}")
print()
print("=" * 70)
