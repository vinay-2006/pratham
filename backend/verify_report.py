"""Quick verification script for Phase A1 report data."""
import requests, json, sys

intake_id = sys.argv[1] if len(sys.argv) > 1 else "57660f5c-bc07-4efc-b88e-c7ea002d278a"
r = requests.get(f"http://localhost:8000/api/report/{intake_id}")
d = r.json()

ps = d.get("clinician_report", {}).get("patient_snapshot", {})
print("=== Patient Snapshot ===")
print(json.dumps(ps, indent=2))

print("\n=== Arrival Type ===")
print(ps.get("arrival_type"))

print("\n=== Patient Name ===")
print(d.get("patient_summary", {}).get("name"))

print("\n=== Validation ===")
print(json.dumps(d.get("validation", {}), indent=2))
