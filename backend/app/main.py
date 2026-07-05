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

load_dotenv()

# ── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    print("[PRATHAM] Backend starting up...")
    # Load XGBoost cardiac model + SHAP explainer once at startup
    try:
        load_lab_model()
        print("[PRATHAM] XGBoost cardiac model loaded.")
    except Exception as exc:
        print(f"[PRATHAM] WARNING: Lab model failed to load: {exc}")
    # Load EfficientNetB0 pneumonia model — fail fast if missing
    try:
        load_imaging_model()
        print("[PRATHAM] EfficientNetB0 imaging model loaded.")
    except FileNotFoundError as exc:
        print(f"[PRATHAM] FATAL: Imaging model file not found: {exc}")
        raise SystemExit(1)
    except Exception as exc:
        print(f"[PRATHAM] WARNING: Imaging model failed to load: {exc}")
    yield
    print("[PRATHAM] Backend shutting down...")


# ── App Factory ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="PRATHAM Medical AI API",
    description=(
        "Predictive Risk Assessment & Triage for Healthcare AI Management. "
        "Provides emergency intake, NLP extraction, risk scoring, investigation "
        "recommendations, imaging analysis, lab processing, and evidence aggregation."
    ),
    version="0.1.0",
    lifespan=lifespan,
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


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "service": "PRATHAM Backend"}


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Welcome to PRATHAM Medical AI API", "docs": "/docs"}
