"""
Run migration 007 using Supabase Management API (v1/sql endpoint).
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ["SUPABASE_URL"]
SERVICE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
PROJECT_REF = SUPABASE_URL.split("//")[1].split(".")[0]  # rctuolwfeuwscenexncu

migration_sql = open(
    os.path.join(os.path.dirname(__file__), "migrations", "007_pipeline_status.sql"),
    "r",
).read()

# Try using the PostgREST SQL execution via the /rest/v1/ endpoint
# Supabase provides a way to call PostgreSQL functions
# We'll create a temporary function first, then call it

# Step 1: First try the database webhook approach
print(f"Project ref: {PROJECT_REF}")
print(f"Trying to create table via Supabase...")

# Actually, let's just try to use the supabase-py client to do individual
# table operations that effectively create what we need.
# Since the REST API can't run raw DDL, let's use the database URL directly.

# Try using the Supabase SQL API endpoint (available in newer Supabase versions)
endpoints_to_try = [
    # Supabase v2 SQL endpoint
    (f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query", {
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }),
    # Alternative management endpoint
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
            print(f"  SUCCESS: {resp.text[:200]}")
            success = True
            break
        else:
            print(f"  Response: {resp.text[:200]}")
    except Exception as e:
        print(f"  Error: {e}")

if not success:
    # Last resort: use the Supabase client to verify table doesn't exist,
    # then guide user
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SERVICE_KEY)
    
    # Check if table exists by trying to query it
    try:
        result = sb.table("pipeline_status").select("id").limit(1).execute()
        print(f"\nTable already exists! Found {len(result.data)} rows.")
        print("Migration was already applied. Proceeding with verification.")
        success = True
    except Exception as e:
        if "pipeline_status" in str(e).lower() or "42P01" in str(e):
            print(f"\nTable does not exist. Need manual migration.")
        else:
            # Might be a different error - table might exist
            print(f"\nUnexpected error: {str(e)[:200]}")

if not success:
    print("\n" + "="*60)
    print("MANUAL MIGRATION REQUIRED")
    print("="*60)
    print(f"\nOpen: https://supabase.com/dashboard/project/{PROJECT_REF}/sql/new")
    print("\nPaste and run this SQL:\n")
    print(migration_sql)
