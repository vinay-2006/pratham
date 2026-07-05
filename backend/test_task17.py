"""
Test Task 17: PDF Export Verification
"""
import requests
import sys

API = "http://localhost:8000"
INTAKE_ID = "c6069b71-9cc5-4827-a8f9-57db60af003b"  # Priya Sharma - known good

checks = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    checks.append((name, condition))
    icon = "[PASS]" if condition else "[FAIL]"
    print(f"  {icon} {name}" + (f" -- {detail}" if detail else ""))

print("=" * 60)
print("Task 17 -- PDF Export Verification")
print("=" * 60)

# 1. JSON report still works
print("\n1. JSON Report Endpoint")
try:
    r = requests.get(f"{API}/api/report/{INTAKE_ID}", timeout=15)
    check("JSON returns 200", r.status_code == 200, f"status={r.status_code}")
    data = r.json()
    check("Patient Summary present", bool(data.get("patient_summary", {}).get("name")), data.get("patient_summary", {}).get("name", ""))
    check("Risk Scores present", data.get("risk_engine", {}).get("cardiac", -1) >= 0)
    check("Pipeline status present", bool(data.get("pipeline_status")))
    check("Investigations field present", "investigations" in data)
    check("Ambulance ETA in summary", "ambulance_eta" in data.get("patient_summary", {}))
except Exception as e:
    check("JSON endpoint reachable", False, str(e))

# 2. PDF endpoint
print("\n2. PDF Export Endpoint")
try:
    r = requests.get(f"{API}/api/report/{INTAKE_ID}/pdf", timeout=30)
    check("PDF returns 200", r.status_code == 200, f"status={r.status_code}")
    check("Content-Type is application/pdf", r.headers.get("content-type") == "application/pdf")
    cd = r.headers.get("content-disposition", "")
    check("Content-Disposition is attachment", "attachment" in cd, cd)
    check("Filename includes patient name", "Priya" in cd or "priya" in cd.lower(), cd)
    check("Filename includes date", "2026" in cd, cd)
    check("PDF magic bytes valid", r.content[:5] == b"%PDF-")
    check("PDF size reasonable (>3KB)", len(r.content) > 3000, f"{len(r.content)} bytes")
    check("PDF not corrupted (contains %%EOF)", b"%%EOF" in r.content[-50:])
except Exception as e:
    check("PDF endpoint reachable", False, str(e))

# 3. 404 for missing intake
print("\n3. Error Handling")
try:
    r = requests.get(f"{API}/api/report/00000000-0000-0000-0000-000000000000/pdf", timeout=10)
    check("Missing intake returns 404", r.status_code == 404, f"status={r.status_code}")
except Exception as e:
    check("Error handling works", False, str(e))

# Summary
print("\n" + "=" * 60)
passed = sum(1 for _, ok in checks if ok)
total = len(checks)
print(f"Results: {passed}/{total} passed")
if passed == total:
    print("[OK] Task 17 -- ALL CHECKS PASSED")
else:
    print(f"[FAIL] {total - passed} check(s) failed")
    sys.exit(1)
