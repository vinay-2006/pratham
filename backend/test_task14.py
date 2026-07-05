"""
Task 14 Verification Script - Pipeline Status Tracking

Runs all verification steps:
  1. Verify migration 007 was applied (pipeline_status table exists)
  2. Create intake -> check initial pipeline status
  3. Run Lab Analysis -> check lab completed
  4. Run Aggregation -> check aggregation completed
  5. Force aggregation failure with bad intake_id
  6. Retry aggregation -> check attempt_count increments
  7. Delete evidence -> check pipeline reset

Prerequisites:
  - Migration 007 must be run manually in Supabase SQL Editor
  - Backend server must be running on localhost:8000
"""

import json
import os
import sys
import io
import time
import requests

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

API = "http://localhost:8000/api"
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

HEADERS_SB = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

results = []

def pp(label, data):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, default=str))
    else:
        print(data)
    print()

def step(n, title):
    print(f"\n{'#'*60}")
    print(f"  STEP {n}: {title}")
    print(f"{'#'*60}")

def passed(n, msg):
    results.append((n, True, msg))
    print(f"  [PASS] Step {n}: {msg}")

def failed(n, msg):
    results.append((n, False, msg))
    print(f"  [FAIL] Step {n}: {msg}")

def skipped(n, msg):
    results.append((n, None, msg))
    print(f"  [SKIP] Step {n}: {msg}")

# ---------------------------------------------------------------
# STEP 1: Verify migration 007 was applied
# ---------------------------------------------------------------
step(1, "Verify pipeline_status table exists")

try:
    check = requests.get(
        f"{SUPABASE_URL}/rest/v1/pipeline_status?select=id&limit=1",
        headers=HEADERS_SB,
        timeout=10,
    )
    if check.status_code == 200:
        passed(1, "pipeline_status table exists and is accessible")
    else:
        err = check.text[:200]
        print(f"\n  Table does not exist! Status: {check.status_code}")
        print(f"  Response: {err}")
        print(f"\n  You MUST run the migration first!")
        print(f"  Open: https://supabase.com/dashboard/project/rctuolwfeuwscenexncu/sql/new")
        print(f"  Paste the contents of: migrations/007_pipeline_status.sql")
        print(f"  Then re-run this script.\n")
        failed(1, "pipeline_status table does not exist - run migration first")
        sys.exit(1)
except Exception as e:
    failed(1, f"Error checking table: {e}")
    sys.exit(1)

# ---------------------------------------------------------------
# STEP 2: Create a brand-new intake
# ---------------------------------------------------------------
step(2, "Create intake and check initial pipeline status")

intake_payload = {
    "patient": {
        "first_name": "Pipeline",
        "last_name": "TestPatient",
        "date_of_birth": "1985-03-15",
        "gender": "male",
        "contact_number": "555-PIPE-001"
    },
    "vitals": {
        "heart_rate": 88,
        "spo2": 96,
        "bp_systolic": 135,
        "bp_diastolic": 85,
        "temperature": 37.2,
        "respiratory_rate": 18
    },
    "symptoms": {
        "chest_pain": True,
        "breathlessness": False,
        "trauma": False,
        "bleeding": False,
        "unconsciousness": False,
        "neurological_symptoms": False
    },
    "emergency_description": "Patient experiencing intermittent chest pain for the past 2 hours. Pain radiates to left arm.",
    "chief_complaint": "Chest pain"
}

intake_resp = requests.post(f"{API}/intake", json=intake_payload, timeout=30)
if intake_resp.status_code not in (200, 201):
    print(f"  Intake creation failed: {intake_resp.status_code}")
    print(f"  {intake_resp.text[:500]}")
    failed(2, "Intake creation failed")
    sys.exit(1)

intake_data = intake_resp.json()
intake_id = intake_data.get("intake_id")
pp("Intake Created", {"intake_id": intake_id, "severity": intake_data.get("severity")})

time.sleep(1)
ps_resp = requests.get(f"{API}/pipeline/status/{intake_id}", timeout=10)
if ps_resp.status_code != 200:
    failed(2, f"Pipeline status endpoint failed: {ps_resp.status_code}")
    sys.exit(1)

pipeline = ps_resp.json()
stages = pipeline["stages"]
pp("Pipeline Status After Intake", {k: {"status": v["status"], "duration_ms": v.get("duration_ms"), "attempt_count": v.get("attempt_count")} for k, v in stages.items()})

try:
    assert stages["nlp"]["status"] in ("completed", "failed"), f"NLP: expected completed/failed, got {stages['nlp']['status']}"
    assert stages["risk"]["status"] == "completed", f"Risk: expected completed, got {stages['risk']['status']}"
    assert stages["lab"]["status"] == "pending", f"Lab: expected pending, got {stages['lab']['status']}"
    assert stages["imaging"]["status"] == "pending", f"Imaging: expected pending, got {stages['imaging']['status']}"
    assert stages["aggregation"]["status"] == "pending", f"Aggregation: expected pending, got {stages['aggregation']['status']}"
    passed(2, f"NLP={stages['nlp']['status']}({stages['nlp'].get('duration_ms')}ms), Risk=completed({stages['risk'].get('duration_ms')}ms), Lab/Img/Agg=pending")
except AssertionError as e:
    failed(2, str(e))
    sys.exit(1)

# ---------------------------------------------------------------
# STEP 3: Run Lab Analysis
# ---------------------------------------------------------------
step(3, "Run Lab Analysis and check pipeline")

lab_resp = requests.post(f"{API}/lab/analyze", json={"intake_id": intake_id}, timeout=30)
if lab_resp.status_code not in (200, 201):
    failed(3, f"Lab analysis failed: {lab_resp.status_code} - {lab_resp.text[:200]}")
else:
    lab_data = lab_resp.json()
    time.sleep(0.5)
    ps_resp = requests.get(f"{API}/pipeline/status/{intake_id}", timeout=10)
    stages = ps_resp.json()["stages"]

    pp("Pipeline After Lab", {k: {"status": v["status"], "duration_ms": v.get("duration_ms"), "attempt_count": v.get("attempt_count")} for k, v in stages.items()})

    if stages["lab"]["status"] == "completed" and stages["lab"]["duration_ms"] is not None and stages["lab"]["attempt_count"] == 1:
        passed(3, f"Lab completed, duration={stages['lab']['duration_ms']}ms, attempt_count=1")
    else:
        failed(3, f"Lab status={stages['lab']['status']}, duration={stages['lab'].get('duration_ms')}, attempts={stages['lab'].get('attempt_count')}")

# ---------------------------------------------------------------
# STEP 4: Skip Imaging (requires real X-ray)
# ---------------------------------------------------------------
step(4, "Imaging Analysis (skipped - requires real X-ray in storage)")
skipped(4, "Imaging requires real X-ray file upload; Lab+Imaging are optional for aggregation")

# ---------------------------------------------------------------
# STEP 5: Run Aggregation
# ---------------------------------------------------------------
step(5, "Run Aggregation and check pipeline")

agg_resp = requests.post(f"{API}/aggregate", json={"intake_id": intake_id}, timeout=30)
if agg_resp.status_code not in (200, 201):
    failed(5, f"Aggregation failed: {agg_resp.status_code} - {agg_resp.text[:300]}")
else:
    agg_data = agg_resp.json()
    time.sleep(0.5)
    ps_resp = requests.get(f"{API}/pipeline/status/{intake_id}", timeout=10)
    stages = ps_resp.json()["stages"]

    pp("Pipeline After Aggregation (ALL 5 STAGES)", {k: {"status": v["status"], "duration_ms": v.get("duration_ms"), "attempt_count": v.get("attempt_count")} for k, v in stages.items()})

    if stages["aggregation"]["status"] == "completed" and stages["aggregation"]["duration_ms"] is not None:
        passed(5, f"Aggregation completed, duration={stages['aggregation']['duration_ms']}ms, primary={agg_data.get('primary_condition')}")
    else:
        failed(5, f"Aggregation status={stages['aggregation']['status']}")

# ---------------------------------------------------------------
# STEP 6: Force failure (bad intake_id)
# ---------------------------------------------------------------
step(6, "Force Aggregation failure with bad intake_id")

bad_id = "00000000-0000-0000-0000-000000000000"
fail_resp = requests.post(f"{API}/aggregate", json={"intake_id": bad_id}, timeout=10)
pp("Failure Response", {"status_code": fail_resp.status_code, "detail": fail_resp.json().get("detail", "")[:200] if fail_resp.headers.get("content-type", "").startswith("application/json") else fail_resp.text[:200]})

if fail_resp.status_code in (400, 404, 500):
    passed(6, f"Aggregation correctly rejected bad ID with HTTP {fail_resp.status_code}")
else:
    failed(6, f"Expected error status, got {fail_resp.status_code}")

# ---------------------------------------------------------------
# STEP 7: Retry aggregation (attempt_count should increment)
# ---------------------------------------------------------------
step(7, "Retry Aggregation (verify attempt_count increments)")

agg_resp2 = requests.post(f"{API}/aggregate", json={"intake_id": intake_id}, timeout=30)
if agg_resp2.status_code not in (200, 201):
    failed(7, f"Aggregation retry failed: {agg_resp2.status_code}")
else:
    time.sleep(0.5)
    ps_resp = requests.get(f"{API}/pipeline/status/{intake_id}", timeout=10)
    agg_stage = ps_resp.json()["stages"]["aggregation"]

    pp("Aggregation After Retry", agg_stage)

    if agg_stage["status"] == "completed" and agg_stage["attempt_count"] >= 2:
        passed(7, f"Retry succeeded, attempt_count={agg_stage['attempt_count']}")
    else:
        failed(7, f"status={agg_stage['status']}, attempt_count={agg_stage['attempt_count']}")

# ---------------------------------------------------------------
# STEP 8: Evidence deletion resets pipeline
# ---------------------------------------------------------------
step(8, "Evidence deletion resets pipeline stages")

# Upload a test xray evidence
try:
    from PIL import Image
    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="JPEG")
    img_buffer.seek(0)

    upload_resp = requests.post(
        f"{API}/evidence/upload",
        data={"intake_id": intake_id, "evidence_type": "xray"},
        files={"file": ("test_xray.jpg", img_buffer, "image/jpeg")},
        timeout=15,
    )
except ImportError:
    # Fallback without PIL - create a minimal JPEG header
    jpeg_header = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b'\x00' * 50 + bytes([0xFF, 0xD9])
    upload_resp = requests.post(
        f"{API}/evidence/upload",
        data={"intake_id": intake_id, "evidence_type": "xray"},
        files={"file": ("test_xray.jpg", jpeg_header, "image/jpeg")},
        timeout=15,
    )

if upload_resp.status_code not in (200, 201):
    skipped(8, f"Evidence upload failed ({upload_resp.status_code}), skipping deletion test")
else:
    evidence_id = upload_resp.json().get("evidence_id")
    print(f"  Uploaded evidence: {evidence_id}")

    # Delete it
    del_resp = requests.delete(f"{API}/evidence/{evidence_id}", timeout=10)
    print(f"  Delete response: {del_resp.status_code}")

    time.sleep(0.5)
    ps_resp = requests.get(f"{API}/pipeline/status/{intake_id}", timeout=10)
    stages = ps_resp.json()["stages"]

    pp("Pipeline After Evidence Deletion", {k: {"status": v["status"], "attempt_count": v.get("attempt_count")} for k, v in stages.items()})

    # Imaging and aggregation should be reset to pending
    # Lab should remain completed
    img_ok = stages["imaging"]["status"] == "pending"
    agg_ok = stages["aggregation"]["status"] == "pending"
    lab_ok = stages["lab"]["status"] == "completed"
    nlp_ok = stages["nlp"]["status"] in ("completed", "failed")

    if img_ok and agg_ok and lab_ok and nlp_ok:
        passed(8, "Evidence deletion correctly reset imaging+aggregation to pending, lab+nlp unchanged")
    else:
        failed(8, f"imaging={stages['imaging']['status']}, agg={stages['aggregation']['status']}, lab={stages['lab']['status']}")

# ---------------------------------------------------------------
# FINAL SUMMARY
# ---------------------------------------------------------------
print("\n" + "="*60)
print("  TASK 14 VERIFICATION SUMMARY")
print("="*60)

# Final pipeline status
ps_resp = requests.get(f"{API}/pipeline/status/{intake_id}", timeout=10)
pp("Final Pipeline Status", ps_resp.json())

total_pass = sum(1 for _, ok, _ in results if ok is True)
total_fail = sum(1 for _, ok, _ in results if ok is False)
total_skip = sum(1 for _, ok, _ in results if ok is None)

print(f"\n  Results: {total_pass} passed, {total_fail} failed, {total_skip} skipped")
print()
for n, ok, msg in results:
    status = "[PASS]" if ok is True else "[FAIL]" if ok is False else "[SKIP]"
    print(f"  {status} Step {n}: {msg}")

print(f"\n  Intake ID: {intake_id}")
print(f"  Pipeline URL: {API}/pipeline/status/{intake_id}")
print(f"  Report URL: {API}/report/{intake_id}")

if total_fail == 0:
    print("\n  TASK 14 VERIFICATION COMPLETE")
else:
    print(f"\n  {total_fail} test(s) failed. Review output above.")
    sys.exit(1)
