# PRATHAM — Predictive Risk Assessment & Triage for Healthcare AI Management

> **PRATHAM v4.0.0** is an enterprise-grade emergency department clinical AI platform providing real-time in-transit intake, NLP extraction, demographic-aware lab analytics, deterministic clinical scoring (NEWS2, qSOFA, Wells PE, HEART), and an interactive **Evidence-Aware Clinical & System Copilot**.

---

## 🏥 Architecture Overview

PRATHAM uses a modular 7-layer design to prevent LLM hallucinations by isolating clinical calculations from generative synthesis.

For in-depth guides, check the dedicated folders:
- [Platform Architecture Specification](file:///d:/pratham/docs/Architecture.md)
- [API Route Reference Sheet](file:///d:/pratham/docs/API_Reference.md)
- [Staging & Production Deployment Guide](file:///d:/pratham/docs/Deployment_Guide.md)
- [Local Developer Setup Guide](file:///d:/pratham/docs/Developer_Guide.md)
- [Frequently Asked Questions (FAQ)](file:///d:/pratham/docs/FAQ.md)

---

## 🚀 Quick Start

### 1. Environment Setup
Create a `.env` file in the root directory:
```bash
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
GROQ_API_KEY="your-groq-key"
FRONTEND_URL="http://localhost:5173"
```

### 2. Startup & Development

#### Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run_migration.py
uvicorn app.main:app --reload --port 8000
```
- Swagger Docs available at: `http://localhost:8000/docs`

#### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
- Workspace runs at: `http://localhost:5173`

#### Docker Compose (Full Stack Staging)
```bash
docker-compose up -d --build
```

---

## 🧠 Platform Capabilities

- **Clinical Copilot Assistant**: Dual-mode (Clinical & System) structured chat with interactive evidence replay and reasoning audits.
- **Demographic Reference Ranges**: Dynamic age/sex thresholds for critical analytes.
- **Multimodal Telemetry**: PyTorch imaging analysis & deterministic scoring calculators.
- **Observability Probes**: Standardized `/health`, `/ready`, and `/metrics` JSON performance tracking.
- **Audit Logs**: Traceable record schema logging pipeline stage latencies and subsystem states.
