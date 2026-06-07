"""
Supabase Client — Initializes and exposes the Supabase client singleton.
Uses SUPABASE_SERVICE_ROLE_KEY for backend operations (bypasses RLS).
"""

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

_supabase_url: str = os.environ.get("SUPABASE_URL", "")
_supabase_key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

if not _supabase_url or not _supabase_key:
    raise EnvironmentError(
        "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in the environment. "
        "Copy .env.example to .env and fill in your Supabase credentials."
    )

supabase: Client = create_client(_supabase_url, _supabase_key)

# Explicitly set the Authorization header so supabase-py 2.5.x correctly
# sends the service_role JWT on every PostgREST request (bypasses RLS).
supabase.postgrest.auth(_supabase_key)
