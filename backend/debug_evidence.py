import requests

BASE = "http://localhost:8000"

r = requests.get(f"{BASE}/api/investigations/queue", timeout=60)
print("Queue status:", r.status_code)

queue = r.json()

patient = next(p for p in queue if p["patient_name"] == "venkat")

print("Queue evidence:", patient["evidence_completeness"])

r = requests.get(
    f"{BASE}/api/investigations/patient/{patient['intake_id']}",
    timeout=60,
)

print("Patient status:", r.status_code)

detail = r.json()

print("Detail evidence:", detail["evidence_completeness"])

print("\nInvestigations")

for inv in detail["investigations"]:
    print(
        inv["investigation_type"],
        "| progress:",
        inv["progress"],
        "| files:",
        len(inv["evidence"])
    )
