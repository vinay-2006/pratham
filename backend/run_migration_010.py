"""
PRATHAM Migration 010 Execution & Verification Script
Attempts execution via Supabase API and provides verification probes.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
PROJECT_REF = SUPABASE_URL.split("//")[1].split(".")[0]

migration_file = os.path.join(os.path.dirname(__file__), "migrations", "010_performance_indexes.sql")
with open(migration_file, "r") as f:
    migration_sql = f.read()

print(f"Project Reference: {PROJECT_REF}")
print(f"Attempting to apply migration 010...")

# Try Supabase SQL query endpoints
endpoints = [
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

applied = False
for url, headers in endpoints:
    try:
        resp = requests.post(url, headers=headers, json={"query": migration_sql}, timeout=10)
        if resp.status_code < 300:
            print(f"  [SUCCESS] Endpoint {url} executed migration.")
            applied = True
            break
        else:
            print(f"  [INFO] Endpoint {url} returned {resp.status_code}")
    except Exception as e:
        print(f"  [INFO] {url} skipped: {e}")

# Verification: Test RPC function presence
print("\n--- Verifying RPC `get_latest_workflow_statuses` ---")
try:
    from app.db.supabase_client import supabase
    rpc_test = supabase.rpc("get_latest_workflow_statuses", {"p_intake_ids": []}).execute()
    print(f"  [VERIFIED] RPC `get_latest_workflow_statuses` is LIVE on Supabase database!")
    print(f"  RPC probe returned: {rpc_test.data}")
    applied = True
except Exception as exc:
    print(f"  [PENDING] RPC not yet available in PostgREST schema cache: {exc}")

if not applied:
    print("\n" + "="*70)
    print("ACTION REQUIRED: MANUAL MIGRATION IN SUPABASE DASHBOARD")
    print("="*70)
    print(f"1. Open Supabase SQL Editor:")
    print(f"   https://supabase.com/dashboard/project/{PROJECT_REF}/sql/new")
    print(f"2. Copy and paste the contents of:")
    print(f"   d:\\pratham\\backend\\migrations\\010_performance_indexes.sql")
    print(f"3. Click 'Run'.")
    print("="*70)
