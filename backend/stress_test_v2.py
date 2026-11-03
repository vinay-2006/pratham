"""
PRATHAM v6.2.0 — Full 100-Patient Stress Test
Validates complete patient lifecycle with all stabilization fixes.
Uses correct nested API payload schema.
"""
import requests
import time
import sys
import random

API = "http://127.0.0.1:8000"
PASS_COUNT = 0
FAIL_COUNT = 0
errors = []
timings = {"intake": [], "approve": [], "workspace": [], "report": []}

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Raj",
    "Priya", "Amir", "Fatima", "Chen", "Yuki", "Pedro", "Maria", "Ahmed",
    "Olga", "Hans", "Ingrid", "Kwame", "Nia", "Sven", "Sofia", "Ivan",
    "Akiko", "Diego", "Lena"
]

COMPLAINTS = [
    "Chest pain radiating to left arm",
    "Severe shortness of breath",
    "Persistent cough with fever",
    "Acute abdominal pain",
    "Dizziness and palpitations",
    "Head injury after fall",
    "Chest tightness with nausea",
    "Difficulty breathing at rest",
    "Sharp chest pain on inspiration",
    "Intermittent chest discomfort",
]


def avg(lst):
    return sum(lst) / len(lst) if lst else 0


def p95(lst):
    if not lst:
        return 0
    s = sorted(lst)
    idx = int(len(s) * 0.95)
    return s[min(idx, len(s) - 1)]


def main():
    global PASS_COUNT, FAIL_COUNT
    for i in range(1, 101):
        first = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
        last = f"StressTest-{i:03d}"
        age = 25 + (i % 55)
        gender = "male" if i % 2 == 0 else "female"
        complaint = COMPLAINTS[(i - 1) % len(COMPLAINTS)]

        print(f"[{i:3d}/100] {first} {last} ...", end=" ", flush=True)

        payload = {
            "patient": {
                "first_name": first,
                "last_name": last,
                "date_of_birth": f"{2026 - age}-06-15",
                "gender": gender,
            },
            "vitals": {
                "heart_rate": 60 + (i % 40),
                "spo2": 95 + (i % 5),
                "bp_systolic": 110 + (i % 30),
                "bp_diastolic": 70 + (i % 15),
                "respiratory_rate": 14 + (i % 8),
                "temperature": 36.5 + (i % 10) * 0.1,
            },
            "symptoms": {
                "chest_pain": i % 3 != 0,
                "breathlessness": i % 4 == 0,
            },
            "arrival_type": "walk_in",
            "chief_complaint": complaint,
            "emergency_description": f"Patient {first} {last}, {age}yo {gender}, presenting with {complaint}.",
        }

        try:
            # 1. Intake
            t0 = time.time()
            r = requests.post(f"{API}/api/intake", json=payload, timeout=30)
            t_intake = (time.time() - t0) * 1000
            timings["intake"].append(t_intake)

            if r.status_code != 201:
                FAIL_COUNT += 1
                errors.append(f"P{i}: Intake {r.status_code}")
                print(f"FAIL (intake {r.status_code})")
                continue

            data = r.json()
            intake_id = data.get("intake_id") or data.get("id")

            # 2. Approve investigations
            t0 = time.time()
            r_app = requests.post(f"{API}/api/investigations/approve", json={
                "intake_id": intake_id,
                "approved_tests": ["Heart Failure Blood Panel", "Chest X-ray"],
                "doctor_name": "Dr. StressTest"
            }, timeout=10)
            t_approve = (time.time() - t0) * 1000
            timings["approve"].append(t_approve)

            # 3. Workspace
            t0 = time.time()
            r_det = requests.get(f"{API}/api/investigations/patient/{intake_id}", timeout=10)
            t_workspace = (time.time() - t0) * 1000
            timings["workspace"].append(t_workspace)

            # 4. Report
            t0 = time.time()
            r_rep = requests.get(f"{API}/api/report/{intake_id}", timeout=30)
            t_report = (time.time() - t0) * 1000
            timings["report"].append(t_report)

            has_clinician = "clinician_report" in (r_rep.json() if r_rep.status_code == 200 else {})

            if r.status_code == 201 and r_app.status_code == 200 and r_det.status_code == 200 and r_rep.status_code == 200 and has_clinician:
                PASS_COUNT += 1
                print(f"PASS  intake={t_intake:.0f}ms approve={t_approve:.0f}ms ws={t_workspace:.0f}ms report={t_report:.0f}ms")
            else:
                FAIL_COUNT += 1
                issues = []
                if r_app.status_code != 200: issues.append(f"approve={r_app.status_code}")
                if r_det.status_code != 200: issues.append(f"workspace={r_det.status_code}")
                if r_rep.status_code != 200: issues.append(f"report={r_rep.status_code}")
                if not has_clinician: issues.append("no_clinician_report")
                errors.append(f"P{i}: {', '.join(issues)}")
                print(f"FAIL ({', '.join(issues)})")

        except Exception as exc:
            FAIL_COUNT += 1
            errors.append(f"P{i}: {exc}")
            print(f"FAIL ({exc})")

    print(f"\n{'='*70}")
    print(f"  PRATHAM v6.2.0 STRESS TEST RESULTS")
    print(f"{'='*70}")
    print(f"  Passed:  {PASS_COUNT}/100")
    print(f"  Failed:  {FAIL_COUNT}/100")
    print(f"\n  Performance (avg / p95):")
    print(f"    Intake:    {avg(timings['intake']):7.0f}ms / {p95(timings['intake']):7.0f}ms")
    print(f"    Approve:   {avg(timings['approve']):7.0f}ms / {p95(timings['approve']):7.0f}ms")
    print(f"    Workspace: {avg(timings['workspace']):7.0f}ms / {p95(timings['workspace']):7.0f}ms")
    print(f"    Report:    {avg(timings['report']):7.0f}ms / {p95(timings['report']):7.0f}ms")
    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for e in errors[:20]:
            print(f"    - {e}")
        if len(errors) > 20:
            print(f"    ... and {len(errors) - 20} more")
    print(f"{'='*70}")

    sys.exit(0 if FAIL_COUNT == 0 else 1)


if __name__ == "__main__":
    main()
