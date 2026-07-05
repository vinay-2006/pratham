"""Quick check: what intakes exist vs what appears in queue?"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
from app.db.supabase_client import supabase

# All intakes with joined patient data (same query structure as queue endpoint)
res = supabase.table("emergency_intake").select(
    "id, status, created_at, severity_level, "
    "patients(first_name, last_name, gender, date_of_birth)"
).order("created_at", desc=True).limit(20).execute()

intakes = res.data or []
print(f"Total intakes in DB: {len(intakes)}\n")

for r in intakes:
    iid = r["id"]
    pat = r.get("patients") or {}
    fn = pat.get("first_name", "")
    ln = pat.get("last_name", "")
    pname = f"{fn} {ln}".strip() or "NO PATIENT"
    created = str(r.get("created_at", ""))[:19]
    status = r.get("status", "")
    sev = r.get("severity_level", "")
    print(f"  {iid[:12]}... | {pname:25s} | status={status:15s} | sev={sev:10s} | {created}")
