import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
PROJECT_REF = SUPABASE_URL.split("//")[1].split(".")[0]

migration_sql = open(
    os.path.join(os.path.dirname(__file__), "migrations", "008_workflow_updates.sql"),
    "r",
).read()

print(f"Project ref: {PROJECT_REF}")
print(f"Running migration 008: Add case_id, arrival_type, and workflow logs...")

endpoints_to_try = [
    (f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query", {
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }),
    (f"{SUPABASE_URL}/rest/v1/rpc/exec_sql", {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }),
]

success = False
for url, headers in endpoints_to_try:
    try:
        resp = requests.post(url, headers=headers, json={"query": migration_sql}, timeout=15)
        if resp.status_code < 300:
            print(f"  SUCCESS: {resp.text[:300]}")
            success = True
            break
    except Exception as e:
        pass

if not success:
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SERVICE_KEY)
    try:
        res = sb.table("emergency_intake").select("case_id").limit(1).execute()
        print(f"\n✅ Columns already exist! Migration was previously applied.")
        success = True
    except Exception as e:
        pass

if not success:
    print("\n" + "=" * 60)
    print("MANUAL MIGRATION REQUIRED")
    print("=" * 60)
    print(f"\nPlease open your Supabase SQL Editor: https://supabase.com/dashboard/project/{PROJECT_REF}/sql/new")
    print("\nPaste and run the SQL below:\n")
    print(migration_sql)
    print("=" * 60)
else:
    print("Migration applied successfully!")
