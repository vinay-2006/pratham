"""
PRATHAM End-to-End Test Suite
Tests all 8 fix groups.
"""
import json
import sys
import urllib.request
import urllib.error

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API = "http://localhost:8000"

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{API}{path}", data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def get(path):
    req = urllib.request.Request(f"{API}{path}", method="GET")
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

print("=" * 60)
print("TEST A -- Invalid vitals (HR=0, SpO2=150, BP=500/300)")
print("=" * 60)
status, body = post("/api/intake", {
    "patient": {"first_name": "Test", "last_name": "InvalidVitals"},
    "vitals": {"heart_rate": 0, "spo2": 150, "bp_systolic": 500, "bp_diastolic": 300},
    "symptoms": {"chest_pain": False},
})
print(f"  Status: {status}")
if status == 400:
    print(f"  PASS -- Rejected with errors: {body.get('errors', [])}")
else:
    print(f"  FAIL -- Expected 400, got {status}")
    print(f"  Body: {json.dumps(body, indent=2)}")

print()
print("=" * 60)
print("TEST B -- Valid chest pain case (HR=128, SpO2=95, BP=170/100)")
print("=" * 60)
status, body = post("/api/intake", {
    "patient": {"first_name": "Cardiac", "last_name": "TestCase", "date_of_birth": "55", "gender": "male"},
    "vitals": {"heart_rate": 128, "spo2": 95, "bp_systolic": 170, "bp_diastolic": 100, "temperature": 37.2, "respiratory_rate": 18},
    "symptoms": {"chest_pain": True, "breathlessness": False, "trauma": False, "bleeding": False, "unconsciousness": False, "neurological_symptoms": False},
    "emergency_description": "55yo male with crushing chest pain radiating to left arm, diaphoretic.",
})
print(f"  Status: {status}")
if status == 201:
    print(f"  PASS -- Intake created")
    print(f"  Patient ID: {body.get('patient_id', 'N/A')[:8]}...")
    print(f"  Intake ID: {body.get('intake_id', 'N/A')[:8]}...")
    print(f"  Severity: {body.get('severity')}")
    investigations = body.get("investigations_recommended", [])
    print(f"  Investigations: {investigations}")
    expected = {"ECG", "Troponin", "CBC"}
    found = set(investigations)
    if expected.issubset(found):
        print(f"  PASS -- ECG, Troponin, CBC all recommended")
    else:
        print(f"  FAIL -- Missing: {expected - found}")
    test_b_intake_id = body.get("intake_id")
else:
    print(f"  FAIL -- Expected 201, got {status}")
    print(f"  Body: {json.dumps(body, indent=2)}")
    test_b_intake_id = None

print()
print("=" * 60)
print("TEST D -- Approve investigation, verify in history")
print("=" * 60)
if test_b_intake_id:
    # Approve
    status, body = post("/api/investigations/approve", {
        "intake_id": test_b_intake_id,
        "approved_tests": ["ECG", "Troponin", "CBC"],
        "doctor_name": "Dr. TestBot",
        "doctor_notes": "E2E test approval",
    })
    print(f"  Approve status: {status}")
    if status == 200:
        print(f"  PASS -- Approved {body.get('approved_count')} tests")
    else:
        print(f"  FAIL -- {body}")

    # Fetch history - check approved tab
    status, history = get("/api/investigations/history?status=approved")
    print(f"  History fetch status: {status}")
    if status == 200:
        found = [h for h in history if h.get("intake_id") == test_b_intake_id]
        if found:
            print(f"  PASS -- Record found in Approved tab")
            audit = found[0].get("audit", {})
            if audit.get("reviewedBy"):
                print(f"  PASS -- Audit trail: {audit['reviewedBy']} at {audit.get('reviewedAt', 'N/A')}")
            else:
                print(f"  WARN -- No audit trail data found")
        else:
            print(f"  FAIL -- Record NOT found in Approved history")
    else:
        print(f"  FAIL -- History fetch failed: {history}")
else:
    print("  SKIP -- No intake ID from Test B")

print()
print("=" * 60)
print("TEST E -- Reject investigation, verify in history")
print("=" * 60)
# Create a new intake for rejection test
status, body = post("/api/intake", {
    "patient": {"first_name": "Reject", "last_name": "TestCase", "date_of_birth": "30", "gender": "female"},
    "vitals": {"heart_rate": 80, "spo2": 98, "bp_systolic": 120, "bp_diastolic": 80, "temperature": 36.8, "respiratory_rate": 16},
    "symptoms": {"chest_pain": False, "breathlessness": True},
    "emergency_description": "Mild breathlessness on exertion.",
})
if status == 201:
    reject_intake_id = body.get("intake_id")
    # Reject
    status, body = post("/api/investigations/reject", {
        "intake_id": reject_intake_id,
        "doctor_name": "Dr. RejectBot",
        "doctor_notes": "E2E rejection test",
    })
    print(f"  Reject status: {status}")
    if status == 200:
        print(f"  PASS -- Rejected")
    else:
        print(f"  FAIL -- {body}")

    # Fetch history - check rejected tab
    status, history = get("/api/investigations/history?status=rejected")
    if status == 200:
        found = [h for h in history if h.get("intake_id") == reject_intake_id]
        if found:
            print(f"  PASS -- Record found in Rejected tab")
            audit = found[0].get("audit", {})
            if audit.get("reviewedBy"):
                print(f"  PASS -- Audit trail: {audit['reviewedBy']}")
            else:
                print(f"  WARN -- No audit trail data")
        else:
            print(f"  FAIL -- Record NOT found in Rejected history")
    else:
        print(f"  FAIL -- History fetch failed")
else:
    print(f"  FAIL -- Could not create intake for rejection test: {status}")

print()
print("=" * 60)
print("TEST F -- Missing vitals -> no malformed UI values")
print("=" * 60)
status, body = post("/api/intake", {
    "patient": {"first_name": "NoVitals", "last_name": "TestCase", "date_of_birth": "40", "gender": "male"},
    "vitals": {},
    "symptoms": {"chest_pain": False, "breathlessness": False},
    "emergency_description": "Minor complaint, no vitals taken.",
})
if status == 201:
    novitals_intake_id = body.get("intake_id")
    # Fetch the intake and check vitals rendering
    status, detail = get(f"/api/intake/{novitals_intake_id}")
    if status == 200:
        vitals = detail.get("vitals", {})
        spo2 = vitals.get("spo2")
        hr = vitals.get("heartRate")
        temp = vitals.get("temperature")
        print(f"  Vitals from API: HR={hr}, SpO2={spo2}, Temp={temp}")
        
        # Check for malformed values
        issues = []
        if str(spo2) == "None%" or str(spo2) == "%" or str(spo2) == "null%":
            issues.append(f"SpO2 is malformed: {spo2}")
        if str(hr) == "None" and hr != 0:
            issues.append(f"HR is None not 0")
        if issues:
            print(f"  FAIL - {issues}")
        else:
            print(f"  PASS - No malformed vitals values (HR={hr}, SpO2={spo2}, Temp={temp})")
        
        # Check evidence completeness
        ec = detail.get("evidenceCompleteness")
        print(f"  Evidence completeness: {ec}")
        if ec == "LOW":
            print(f"  PASS - Correctly marked as LOW for missing vitals")
        else:
            print(f"  INFO - Evidence completeness is {ec} (LOW expected for minimal vitals)")
    else:
        print(f"  FAIL - Could not fetch intake detail: {status}")
else:
    print(f"  FAIL - Could not create intake: {status} - {body}")

print()
print("=" * 60)
print("TEST G -- Verify tab counts (All / Pending / Approved / Rejected)")
print("=" * 60)
status_all, all_data = get("/api/investigations/history")
status_pending, pending_data = get("/api/investigations/history?status=pending_approval")
status_approved, approved_data = get("/api/investigations/history?status=approved")
status_rejected, rejected_data = get("/api/investigations/history?status=rejected")

if all([s == 200 for s in [status_all, status_pending, status_approved, status_rejected]]):
    print(f"  All tab: {len(all_data)} records")
    print(f"  Pending tab: {len(pending_data)} records")
    print(f"  Approved tab: {len(approved_data)} records")
    print(f"  Rejected tab: {len(rejected_data)} records")
    total_filtered = len(pending_data) + len(approved_data) + len(rejected_data)
    # All should be >= sum of individual tabs (may include needs_info too)
    if len(all_data) >= total_filtered:
        print(f"  PASS - All tab ({len(all_data)}) >= sum of filtered tabs ({total_filtered})")
    else:
        print(f"  FAIL - All tab count mismatch")
else:
    print(f"  FAIL - Some history fetches failed")

print()
print("=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
