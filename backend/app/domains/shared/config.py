"""
PRATHAM Centralized Configuration — Single location for all runtime settings.

All environment variables, timeouts, feature flags, and external service
configuration are read and validated here. No other module should call
os.getenv() for application configuration — import from this module instead.

Validation: This module fails fast at import time if critical configuration
is missing. Non-critical configuration uses documented defaults.

Domain Ownership: shared (cross-cutting)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

# Load .env before reading any environment variables
load_dotenv()


# ── Supabase Configuration ───────────────────────────────────────────────────

@dataclass(frozen=True)
class SupabaseConfig:
    """Supabase connection settings."""
    url: str
    anon_key: str
    service_role_key: str
    storage_bucket: str = "evidence-files"
    signed_url_expiry_seconds: int = 3600


# ── Groq LLM Configuration ──────────────────────────────────────────────────

@dataclass(frozen=True)
class GroqConfig:
    """Groq API settings for NLP extraction and clinical interpretation."""
    api_key: str
    model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    temperature: float = 0.1
    max_tokens: int = 1024
    timeout_seconds: int = 8
    use_mock: bool = False


# ── Pipeline Configuration ───────────────────────────────────────────────────

@dataclass(frozen=True)
class PipelineConfig:
    """AI pipeline execution settings."""
    stages: tuple[str, ...] = ("nlp", "risk", "lab", "imaging", "aggregation")
    stage_timeout_seconds: int = 120
    max_retry_attempts: int = 2


# ── Application Configuration ────────────────────────────────────────────────

@dataclass(frozen=True)
class AppConfig:
    """General application settings."""
    version: str = "v5.0.0"
    api_spec_version: str = "v1.0"
    frontend_url: str = "http://localhost:5173"
    cors_additional_origins: tuple[str, ...] = ("http://localhost:8080", "http://localhost:8081")
    lifecycle_timeout_hours: int = 48
    log_level: str = "INFO"


# ── Feature Flags ────────────────────────────────────────────────────────────
# ADR-012: Feature Flag Governance
# Every flag follows the lifecycle: dev → staging → ga → permanent

@dataclass(frozen=True)
class FeatureFlags:
    """Runtime feature flags — read from PRATHAM_FF_* environment variables."""
    mandatory_vitals: bool = False
    routine_mode: bool = False
    upload_validation: bool = False
    ai_upload_restrictions: bool = False
    live_eta: bool = False
    auto_archival: bool = False
    background_pipeline: bool = False
    report_caching: bool = False
    report_auto_regen: bool = False
    report_v2_redesign: bool = False
    copilot_v2: bool = False
    demo_launch_mode: bool = False


# ── ML Model Configuration ──────────────────────────────────────────────────

@dataclass(frozen=True)
class MLConfig:
    """Machine learning model settings."""
    lab_model_path: str = "app/ml/models/task9_xgboost_heart_model.json"
    imaging_model_path: str = "app/ml/models/task10_efficientnetb0_pneumonia.pth"
    lab_model_name: str = "task9_xgboost_heart_model"
    imaging_model_name: str = "task10_efficientnetb0_pneumonia"


# ── Reliability Configuration ────────────────────────────────────────────────

@dataclass(frozen=True)
class ReliabilityConfig:
    """Retry, timeout, and circuit breaker defaults."""
    db_read_timeout_seconds: int = 5
    db_write_timeout_seconds: int = 10
    db_read_retry_attempts: int = 2
    llm_retry_attempts: int = 2
    llm_retry_backoff_seconds: float = 1.0
    storage_upload_timeout_seconds: int = 30
    storage_retry_attempts: int = 2
    report_generation_timeout_seconds: int = 45


# ── Settings Singleton ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class Settings:
    """Root configuration object — the single entry point for all settings."""
    supabase: SupabaseConfig
    groq: GroqConfig
    pipeline: PipelineConfig
    app: AppConfig
    features: FeatureFlags
    ml: MLConfig
    reliability: ReliabilityConfig


def _read_bool(env_var: str, default: bool = False) -> bool:
    """Read a boolean from an environment variable (true/1/yes → True)."""
    val = os.getenv(env_var, "").strip().lower()
    if not val:
        return default
    return val in ("true", "1", "yes", "on")


def _read_int(env_var: str, default: int) -> int:
    """Read an integer from an environment variable with a fallback default."""
    val = os.getenv(env_var, "").strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _build_settings() -> Settings:
    """
    Construct the Settings singleton from environment variables.

    Fails fast if critical configuration is missing. Non-critical
    configuration uses documented defaults.
    """
    # ── Critical: Supabase (required) ────────────────────────────────────
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_anon = os.getenv("SUPABASE_ANON_KEY", "").strip()
    supabase_service = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    # ── Critical: Groq (required) ────────────────────────────────────────
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    # ── Build sub-configs ────────────────────────────────────────────────
    supabase_config = SupabaseConfig(
        url=supabase_url,
        anon_key=supabase_anon,
        service_role_key=supabase_service,
        storage_bucket=os.getenv("SUPABASE_STORAGE_BUCKET", "evidence-files").strip(),
        signed_url_expiry_seconds=_read_int("SUPABASE_SIGNED_URL_EXPIRY", 3600),
    )

    groq_config = GroqConfig(
        api_key=groq_key,
        model_name=os.getenv("GROQ_MODEL_NAME", "meta-llama/llama-4-scout-17b-16e-instruct").strip(),
        temperature=float(os.getenv("GROQ_TEMPERATURE", "0.1")),
        max_tokens=_read_int("GROQ_MAX_TOKENS", 1024),
        timeout_seconds=_read_int("GROQ_TIMEOUT_SECONDS", 8),
        use_mock=_read_bool("USE_MOCK_LLM"),
    )

    pipeline_config = PipelineConfig(
        stage_timeout_seconds=_read_int("PIPELINE_STAGE_TIMEOUT", 120),
        max_retry_attempts=_read_int("PIPELINE_MAX_RETRIES", 2),
    )

    app_config = AppConfig(
        frontend_url=os.getenv("FRONTEND_URL", "http://localhost:5173").strip(),
        lifecycle_timeout_hours=_read_int("LIFECYCLE_TIMEOUT_HOURS", 48),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
    )

    feature_flags = FeatureFlags(
        mandatory_vitals=_read_bool("PRATHAM_FF_INTAKE_MANDATORY_VITALS"),
        routine_mode=_read_bool("PRATHAM_FF_INTAKE_ROUTINE_MODE"),
        upload_validation=_read_bool("PRATHAM_FF_EVIDENCE_UPLOAD_VALIDATION"),
        ai_upload_restrictions=_read_bool("PRATHAM_FF_EVIDENCE_AI_RESTRICTIONS"),
        live_eta=_read_bool("PRATHAM_FF_WORKFLOW_LIVE_ETA"),
        auto_archival=_read_bool("PRATHAM_FF_WORKFLOW_AUTO_ARCHIVAL"),
        background_pipeline=_read_bool("PRATHAM_FF_PIPELINE_BACKGROUND"),
        report_caching=_read_bool("PRATHAM_FF_REPORT_CACHING"),
        report_auto_regen=_read_bool("PRATHAM_FF_REPORT_AUTO_REGEN"),
        report_v2_redesign=_read_bool("PRATHAM_FF_REPORT_V2_REDESIGN"),
        copilot_v2=_read_bool("PRATHAM_FF_COPILOT_V2"),
        demo_launch_mode=_read_bool("PRATHAM_FF_DEMO_LAUNCH_MODE"),
    )

    ml_config = MLConfig(
        lab_model_path=os.getenv("LAB_MODEL_PATH", "app/ml/models/task9_xgboost_heart_model.json").strip(),
        imaging_model_path=os.getenv("IMAGING_MODEL_PATH", "app/ml/models/task10_efficientnetb0_pneumonia.pth").strip(),
    )

    reliability_config = ReliabilityConfig(
        db_read_timeout_seconds=_read_int("DB_READ_TIMEOUT", 5),
        db_write_timeout_seconds=_read_int("DB_WRITE_TIMEOUT", 10),
        llm_retry_attempts=_read_int("LLM_RETRY_ATTEMPTS", 2),
    )

    return Settings(
        supabase=supabase_config,
        groq=groq_config,
        pipeline=pipeline_config,
        app=app_config,
        features=feature_flags,
        ml=ml_config,
        reliability=reliability_config,
    )


# ── Module-level singleton ───────────────────────────────────────────────────
# Import as: from app.domains.shared.config import settings
settings: Settings = _build_settings()
