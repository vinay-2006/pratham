"""
PRATHAM Backend — FastAPI Application Entry Point
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api import intake, nlp, risk, investigation, imaging, labs, aggregation, investigations, evidence, lab_analysis, imaging_analysis, report, pipeline, admin, command_center, explainability, search, copilot
from app.ml.lab_model import load_lab_model
from app.ml.imaging_model import load_imaging_model

from app.core.config_validator import validate_startup_config
from app.core.logging_service import log_event
import logging
import uuid
import time
from typing import Any

load_dotenv()
validate_startup_config()

# ── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    log_event("PRATHAM Backend starting up...", level=logging.INFO)
    # Load XGBoost cardiac model + SHAP explainer once at startup
    try:
        load_lab_model()
        log_event("XGBoost cardiac model loaded.", level=logging.INFO)
    except Exception as exc:
        log_event(f"WARNING: Lab model failed to load: {exc}", level=logging.WARNING)
    # Load EfficientNetB0 pneumonia model — fail fast if missing
    try:
        load_imaging_model()
        log_event("EfficientNetB0 imaging model loaded.", level=logging.INFO)
    except FileNotFoundError as exc:
        log_event(f"FATAL: Imaging model file not found: {exc}", level=logging.CRITICAL)
        raise SystemExit(1)
    except Exception as exc:
        log_event(f"WARNING: Imaging model failed to load: {exc}", level=logging.WARNING)
    yield
    log_event("PRATHAM Backend shutting down...", level=logging.INFO)


# ── App Factory ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="PRATHAM Medical AI API",
    description=(
        "Predictive Risk Assessment & Triage for Healthcare AI Management. "
        "Provides emergency intake, NLP extraction, risk scoring, investigation "
        "recommendations, imaging analysis, lab processing, and evidence aggregation."
    ),
    version="4.0.0",
    lifespan=lifespan,
)


# ── Structured Logging Middleware ───────────────────────────────────────────
@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start_time = time.time()
    
    path = request.url.path
    patient_id = None
    if "patient/" in path:
        parts = path.split("patient/")
        if len(parts) > 1:
            patient_id = parts[1].split("/")[0]
    elif "status/" in path:
        parts = path.split("status/")
        if len(parts) > 1:
            patient_id = parts[1].split("/")[0]

    response = await call_next(request)
    
    duration_ms = (time.time() - start_time) * 1000.0
    response.headers["X-Request-ID"] = request_id
    
    log_event(
        message=f"{request.method} {path} completed with status {response.status_code}",
        level=logging.INFO,
        request_id=request_id,
        patient_id=patient_id,
        pipeline_stage=path.split("/")[1] if len(path.split("/")) > 1 else "ROOT",
        duration_ms=duration_ms
    )
    
    return response


# ── Global Server Error Exception Handler ───────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    log_event(
        message=f"Unhandled Server Error on {request.method} {request.url.path}: {exc}",
        level=logging.ERROR,
        request_id=request_id,
        pipeline_stage="UNHANDLED_EXCEPTION"
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "request_id": request_id,
            "status": "error"
        }
    )


# ── Convert Pydantic validation errors to 400 Bad Request ───────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return 400 with clear field-level error messages instead of Pydantic's default 422."""
    errors = []
    for err in exc.errors():
        field = " → ".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        errors.append(f"{field}: {err['msg']}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Validation failed",
            "errors": errors,
        },
    )


# ── CORS ────────────────────────────────────────────────────────────────────
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Allow both the configured frontend URL and common local dev ports
_cors_origins = list({frontend_url, "http://localhost:8080", "http://localhost:8081", "http://localhost:5173"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(intake.router, tags=["Intake"])
app.include_router(nlp.router, prefix="/nlp", tags=["NLP"])
app.include_router(risk.router, prefix="/risk", tags=["Risk"])
app.include_router(investigation.router, prefix="/investigation", tags=["Investigation"])
app.include_router(imaging.router, prefix="/evidence", tags=["Evidence"])
app.include_router(labs.router, prefix="/evidence", tags=["Evidence"])
app.include_router(aggregation.router, prefix="/api", tags=["Aggregation"])
app.include_router(investigations.router, prefix="/api", tags=["Investigations"])
app.include_router(evidence.router, prefix="/api", tags=["Evidence Upload"])
app.include_router(lab_analysis.router, prefix="/api", tags=["Lab Analysis"])
app.include_router(imaging_analysis.router, prefix="/api", tags=["Imaging Analysis"])
app.include_router(report.router, prefix="/api", tags=["Clinical Report"])
app.include_router(pipeline.router, prefix="/api", tags=["Pipeline"])
app.include_router(admin.router, prefix="/api", tags=["Admin Telemetry"])
app.include_router(command_center.router, prefix="/api", tags=["Command Center"])
app.include_router(explainability.router, prefix="/api", tags=["Explainability Explorer"])
app.include_router(search.router, prefix="/api", tags=["Clinical Search"])
app.include_router(copilot.router, prefix="/api/copilot", tags=["Clinical Copilot"])


# ── Health, Readiness, Metrics & Version ─────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "service": "PRATHAM Backend"}


@app.get("/ready", tags=["Health"])
async def readiness_probe() -> dict[str, str]:
    """Verify Supabase database connection and Groq environment status."""
    try:
        from app.db.supabase_client import supabase
        # Test database connection
        supabase.table("patients").select("id").limit(1).execute()
        # Test Groq key
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key or len(groq_key) < 10:
             raise Exception("Invalid GROQ_API_KEY configuration")
        return {"status": "ready", "database": "connected", "groq_api": "active"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Service Unavailable: {exc}")


@app.get("/metrics", tags=["Health"])
async def metrics_endpoint() -> dict[str, Any]:
    """Observability telemetry exposing average pipeline stage latencies."""
    try:
        from app.db.supabase_client import supabase
        res = supabase.table("pipeline_status").select("stage, duration_ms, status").execute()
        
        stages_data = res.data or []
        stage_metrics = {}
        stage_counts = {}
        
        for item in stages_data:
            stage = item.get("stage")
            duration = item.get("duration_ms")
            status = item.get("status")
            if stage and duration is not None and status == "completed":
                stage_metrics[stage] = stage_metrics.get(stage, 0.0) + duration
                stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        averages = {}
        for stage in ["nlp", "risk", "lab", "imaging", "aggregation"]:
            total_duration = stage_metrics.get(stage, 0.0)
            count = stage_counts.get(stage, 0)
            averages[f"average_{stage}_latency_seconds"] = round((total_duration / count) / 1000.0, 2) if count > 0 else 0.0
            averages[f"{stage}_execution_count"] = count

        return {
            "total_pipelines_tracked": len(stages_data) // 5,
            "averages": averages,
            "system_status": "OPERATIONAL"
        }
    except Exception as exc:
        return {
            "total_pipelines_tracked": 0,
            "averages": {
                "average_nlp_latency_seconds": 0.0,
                "average_risk_latency_seconds": 0.0,
                "average_lab_latency_seconds": 0.0,
                "average_imaging_latency_seconds": 0.0,
                "average_aggregation_latency_seconds": 0.0,
            },
            "system_status": "LIMITED_OFFLINE",
            "info": f"Could not retrieve live metrics: {exc}"
        }


@app.get("/api/version", tags=["Version"])
async def get_version_endpoint() -> dict[str, str]:
    """Return platform metadata versioning information."""
    return {
        "version": "v4.0.0",
        "api_spec_version": "v1.0",
        "build_date": "2026-07-05",
        "commit_hash": "5f0017d",
    }


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Welcome to PRATHAM Medical AI API", "docs": "/docs"}
