"""
PRATHAM Startup Configuration Validator
Ensures all required environment variables are set and populated before backend initialization.
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "GROQ_API_KEY",
]

def validate_startup_config():
    """Verify that all required environment variables are present and non-empty."""
    logger.info("[PRATHAM] Auditing environment configuration...")
    missing_vars = []
    invalid_vars = []

    for var in REQUIRED_ENV_VARS:
        val = os.getenv(var)
        if val is None:
            missing_vars.append(var)
        elif not val.strip() or val.strip() == "your_value_here":
            invalid_vars.append(var)

    if missing_vars or invalid_vars:
        sep = "=" * 60
        logger.critical(sep)
        logger.critical("  FATAL CONFIGURATION ERROR: Start blocked due to missing or invalid keys")
        logger.critical(sep)
        if missing_vars:
            logger.critical("Missing required environment variable(s): %s", ", ".join(missing_vars))
        if invalid_vars:
            logger.critical("Placeholder or empty value for variable(s): %s", ", ".join(invalid_vars))
        logger.critical("Please check your .env file or environment settings before starting the server.")
        logger.critical(sep)
        sys.exit(1)

    logger.info("[PRATHAM] Environment variables validated successfully.")
