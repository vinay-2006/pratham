"""
PRATHAM Backend — FastAPI Application Entry Point
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import intake, nlp, risk, investigation, imaging, labs, aggregation

load_dotenv()

# ── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    print("🏥 PRATHAM backend starting up...")
    yield
    print("🏥 PRATHAM backend shutting down...")


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

# ── CORS ────────────────────────────────────────────────────────────────────
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
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
app.include_router(aggregation.router, tags=["Aggregation"])


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "service": "PRATHAM Backend"}


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Welcome to PRATHAM Medical AI API", "docs": "/docs"}
