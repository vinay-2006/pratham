"""
Run migration 006b — add missing columns to aggregation_results.

Attempts Supabase Management API first, falls back to manual instructions.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
PROJECT_REF = SUPABASE_URL.split("//")[1].split(".")[0]

migration_sql = open(
    os.path.join(os.path.dirname(__file__), "migrations", "006b_add_aggregation_columns.sql"),
    "r",
).read()

print(f"Project ref: {PROJECT_REF}")
print(f"Running migration 006b: Add missing aggregation_results columns...")

# Try available endpoints
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
        print(f"  {url}: {resp.status_code}")
        if resp.status_code < 300:
            print(f"  SUCCESS: {resp.text[:300]}")
            success = True
            break
        else:
            print(f"  Response: {resp.text[:300]}")
    except Exception as e:
        print(f"  Error: {e}")

if not success:
    # Verify current state
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SERVICE_KEY)
    try:
        res = sb.table("aggregation_results").select("evidence_breakdown_json").limit(1).execute()
        print(f"\n✅ Column already exists! Migration was previously applied.")
        success = True
    except Exception as e:
        if "42703" in str(e) or "does not exist" in str(e):
            print(f"\n❌ Columns don't exist yet. Manual migration required.")
        else:
            print(f"\n❓ Unexpected error: {str(e)[:200]}")

if not success:
    print("\n" + "=" * 60)
    print("MANUAL MIGRATION REQUIRED")
    print("=" * 60)
    print(f"\nOpen: https://supabase.com/dashboard/project/{PROJECT_REF}/sql/new")
    print("\nPaste and run this SQL:\n")
    print(migration_sql)
else:
    # Verify all 4 columns exist
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SERVICE_KEY)
    res = sb.table("aggregation_results").select("*").limit(1).execute()
    cols = list((res.data or [{}])[0].keys()) if res.data else []
    expected = {"primary_condition", "raw_scores_json", "evidence_breakdown_json", "source_summary_json"}
    found = expected.intersection(set(cols))
    missing = expected - found
    if missing:
        print(f"\n⚠ Still missing columns: {missing}")
    else:
        print(f"\n✅ All 4 new columns verified: {sorted(found)}")
