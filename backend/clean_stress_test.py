"""
PRATHAM v6.2.0 — Clean 20-Patient Stress Test
Runs 20 patients sequentially through the full pipeline:
  Intake → Approve → Workspace → Report
With small delays to avoid Supabase rate limiting.
"""
import requests
import time
import sys

API = "http://127.0.0.1:8000"

def flush_print(msg):
    print(msg, flush=True)

def main():
    flush_print("=" * 60)
    flush_print("PRATHAM v6.2.0 — 20-Patient Clean Stress Test")
    flush_print("=" * 60)
    flush_print("")

    PASS = 0
    FAIL = 0
    errors = []
    timings = []

    for i in range(1, 21):
        t0 = time.time()
        try:
            payload = {
                "patient": {
                    "first_name": f"Final{i}",
                    "last_name": f"Test{i}",
                    "date_of_birth": f"{1985 + i}-03-15",
                    "gender": "male" if i % 2 == 0 else "female",
                },
                "vitals": {
                    "heart_rate": 70 + i,
                    "spo2": 97,
                    "bp_systolic": 120,
                    "bp_diastolic": 80,
                    "respiratory_rate": 16,
                    "temperature": 36.8,
                },
                "symptoms": {
                    "chest_pain": i % 3 == 0,
                    "breathlessness": i % 3 == 1,
                },
                "arrival_type": "walk_in",
                "chief_complaint": "Routine check" if i % 2 == 0 else "Chest pain",
                "emergency_description": f"Patient Final{i} evaluation",
            }

            # Step 1: Intake
            r1 = requests.post(f"{API}/api/intake", json=payload, timeout=60)
            if r1.status_code != 201:
                FAIL += 1
                errors.append(f"P{i}: intake={r1.status_code}")
                flush_print(f"[{i:2d}] FAIL intake={r1.status_code}")
                continue
            iid = r1.json().get("intake_id")

            time.sleep(0.5)  # Small gap

            # Step 2: Approve
            r2 = requests.post(
                f"{API}/api/investigations/approve",
                json={"intake_id": iid, "approved_tests": ["CBC"], "doctor_name": "Dr.Final"},
                timeout=30,
            )

            time.sleep(0.3)

            # Step 3: Workspace
            r3 = requests.get(f"{API}/api/investigations/patient/{iid}", timeout=30)

            # Step 4: Report
            r4 = requests.get(f"{API}/api/report/{iid}", timeout=60)

            fails = []
            if r2.status_code != 200:
                fails.append(f"approve={r2.status_code}")
            if r3.status_code != 200:
                fails.append(f"ws={r3.status_code}")
            if r4.status_code != 200:
                fails.append(f"report={r4.status_code}")

            elapsed = time.time() - t0
            timings.append(elapsed)

            if fails:
                FAIL += 1
                errors.append(f"P{i}: {fails}")
                flush_print(f"[{i:2d}] FAIL {fails} ({elapsed:.1f}s)")
            else:
                PASS += 1
                flush_print(f"[{i:2d}] PASS ({elapsed:.1f}s)")

        except Exception as e:
            FAIL += 1
            errors.append(f"P{i}: {e}")
            flush_print(f"[{i:2d}] FAIL {e}")

    flush_print("")
    flush_print("=" * 60)
    flush_print(f"RESULT: {PASS}/{PASS + FAIL} passed")
    flush_print("=" * 60)

    if timings:
        avg = sum(timings) / len(timings)
        flush_print(f"Avg time per patient: {avg:.1f}s")

    if errors:
        flush_print("\nErrors:")
        for e in errors:
            flush_print(f"  {e}")

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
