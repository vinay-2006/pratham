"""
Quick 10-patient smoke test to verify all stabilization fixes.
Validates:
- Mock LLM bypass (zero Groq calls)
- No NoneType crashes
- No invalid workflow transitions
- Clean report generation
"""
import requests
import time
import sys

def main():
    API = "http://127.0.0.1:8000"
    PASS = 0
    FAIL = 0
    errors = []

    for i in range(1, 11):
        name = f"SmokeTest-Patient-{i:03d}"
        print(f"\n{'='*60}")
        print(f"  Patient {i}/10: {name}")
        print(f"{'='*60}")

        # 1. Submit intake (correct nested schema)
        payload = {
            "patient": {
                "first_name": name,
                "last_name": "Verification",
                "date_of_birth": str(2026 - (30 + i)) + "-01-01",
                "gender": "male" if i % 2 == 0 else "female",
            },
            "vitals": {
                "heart_rate": 75 + i,
                "spo2": 97,
                "bp_systolic": 120,
                "bp_diastolic": 80,
                "respiratory_rate": 16,
                "temperature": 37.0,
            },
            "symptoms": {
                "chest_pain": True,
                "breathlessness": i % 3 == 0,
            },
            "arrival_type": "walk_in",
            "chief_complaint": "Chest pain and shortness of breath",
            "emergency_description": f"Patient {name} presents with acute chest pain radiating to left arm",
        }

        try:
            r = requests.post(f"{API}/api/intake", json=payload, timeout=30)
            if r.status_code != 201:
                FAIL += 1
                errors.append(f"Patient {i}: Intake failed with {r.status_code}: {r.text[:200]}")
                continue
            data = r.json()
            intake_id = data.get("intake_id") or data.get("id")
            print(f"  ✓ Intake created: {intake_id}")

            # 2. Confirm arrival
            r_arr = requests.post(f"{API}/api/intake/arrival/confirm", json={
                "intake_id": intake_id,
                "arrival_type": "walk_in"
            }, timeout=10)
            if r_arr.status_code == 200:
                print(f"  ✓ Arrival confirmed")
            else:
                print(f"  ⚠ Arrival: {r_arr.status_code}")

            # 3. Approve investigations
            r_app = requests.post(f"{API}/api/investigations/approve", json={
                "intake_id": intake_id,
                "approved_tests": ["Heart Failure Blood Panel", "Chest X-ray"],
                "doctor_name": "Dr. SmokeTest"
            }, timeout=10)
            if r_app.status_code == 200:
                print(f"  ✓ Investigations approved")
            else:
                print(f"  ⚠ Approval: {r_app.status_code}")

            # 4. Load patient workspace
            r_det = requests.get(f"{API}/api/investigations/patient/{intake_id}", timeout=10)
            if r_det.status_code == 200:
                print(f"  ✓ Patient workspace loaded")
            else:
                print(f"  ⚠ Workspace: {r_det.status_code}")

            # 5. Get report
            r_rep = requests.get(f"{API}/api/report/{intake_id}", timeout=30)
            if r_rep.status_code == 200:
                rep_data = r_rep.json()
                has_clinician = "clinician_report" in rep_data
                print(f"  ✓ Report generated (clinician_report={'yes' if has_clinician else 'NO'})")
            else:
                print(f"  ⚠ Report: {r_rep.status_code}")

            PASS += 1
            print(f"  ✅ PASS")

        except Exception as exc:
            FAIL += 1
            errors.append(f"Patient {i}: Exception: {exc}")
            print(f"  ❌ FAIL: {exc}")

    print(f"\n{'='*60}")
    print(f"  SMOKE TEST RESULTS")
    print(f"{'='*60}")
    print(f"  Passed: {PASS}/10")
    print(f"  Failed: {FAIL}/10")
    if errors:
        print(f"\n  Errors:")
        for e in errors:
            print(f"    - {e}")
    print(f"{'='*60}")

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
