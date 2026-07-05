"""
PRATHAM Startup Configuration Validator
Ensures all required environment variables are set and populated before backend initialization.
"""

import os
import sys

REQUIRED_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "GROQ_API_KEY",
]

def validate_startup_config():
    """Verify that all required environment variables are present and non-empty."""
    print("[PRATHAM] Auditing environment configuration...")
    missing_vars = []
    invalid_vars = []

    for var in REQUIRED_ENV_VARS:
        val = os.getenv(var)
        if val is None:
            missing_vars.append(var)
        elif not val.strip() or val.strip() == "your_value_here":
            invalid_vars.append(var)

    if missing_vars or invalid_vars:
        print("=" * 60)
        print("  FATAL CONFIGURATION ERROR: Start blocked due to missing or invalid keys")
        print("=" * 60)
        if missing_vars:
            print(f"Missing required environment variable(s): {', '.join(missing_vars)}")
        if invalid_vars:
            print(f"Placeholder or empty value for variable(s): {', '.join(invalid_vars)}")
        print("\nPlease check your .env file or environment settings before starting the server.")
        print("=" * 60)
        sys.exit(1)

    print("[PRATHAM] Environment variables checked successfully.")
