# PRATHAM

**Predictive Risk Assessment & Triage for Healthcare AI Management**

PRATHAM is an emergency-department clinical decision-support platform that brings intake, clinical NLP, deterministic risk scoring, laboratory and imaging analysis, evidence aggregation, workflow management, and an evidence-aware copilot into one operational workspace.

> **Important:** PRATHAM is a research and engineering project, not a substitute for professional medical judgment. It has not been validated for autonomous diagnosis, treatment, or clinical deployment. Do not use it with real patient data without completing the required security, privacy, regulatory, clinical-validation, and operational reviews.

## Overview

PRATHAM is designed around a clear separation between deterministic clinical computation and generative assistance:

- **Structured intake** captures patient context and presenting information.
- **Clinical NLP** extracts useful signals from free-text notes.
- **Deterministic scoring** calculates supported triage scores such as NEWS2, qSOFA, Wells PE, and HEART.
- **Lab and imaging intelligence** processes supported evidence and returns model outputs with explainability data where available.
- **Evidence aggregation** combines pipeline results into a traceable patient-case view.
- **Clinical Copilot** provides contextual answers and workflow assistance grounded in available evidence.
- **Operational telemetry** exposes health, readiness, metrics, pipeline status, audit, and release endpoints.

## Key capabilities

- Emergency intake and patient queue management
- Clinical note NLP and structured extraction
- Demographic-aware laboratory reference ranges
- Risk scoring and triage support
- XGBoost-based cardiac laboratory analysis
- EfficientNetB0-based pneumonia imaging analysis
- Evidence upload, review, investigation, and aggregation workflows
- Clinical reports and PDF export support
- Evidence-aware clinical and system copilot
- Explainability and evidence replay surfaces
- Structured logging, request IDs, health checks, readiness checks, and metrics
- Knowledge-base content for common emergency presentations

## Architecture

```text
┌──────────────────────┐       ┌─────────────────────────┐
│ React + Vite frontend│──────▶│ FastAPI clinical API    │
│ TanStack Router      │       │                        │
└──────────────────────┘       └───────────┬─────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              ▼                            ▼                            ▼
       Supabase/Postgres          Clinical services              ML models
       patients, evidence,        NLP, scoring, workflow,        XGBoost,
       pipeline, audit            reports, copilot               EfficientNetB0
```

The backend is organized into API routers, domain schemas and repositories, clinical services, knowledge-base content, and model adapters. The frontend is a React application built with Vite, TanStack Router, Tailwind CSS, Radix UI, and React Query.

## Technology stack

| Area | Technologies |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, TanStack Router, React Query, Tailwind CSS, Radix UI |
| Backend | Python, FastAPI, Pydantic, Uvicorn |
| Data | Supabase / PostgreSQL |
| AI services | Groq, clinical NLP services, evidence-aware copilot |
| Machine learning | XGBoost, SHAP, TensorFlow, Pillow |
| Operations | Structured logging, health/readiness probes, metrics, Docker support |

## Repository structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/              # HTTP routers
│   │   ├── domains/          # Domain schemas and repositories
│   │   ├── knowledge_base/   # Clinical knowledge-base entries
│   │   ├── ml/               # Model loading and inference adapters
│   │   └── services/         # Clinical and platform services
│   ├── migrations/           # Database migrations
│   ├── ml_models/            # Model artifacts
│   ├── requirements.txt
│   └── run_migration.py
├── frontend/
│   ├── src/                  # React application source
│   ├── package.json
│   └── vite.config.*
├── atlas_data/               # Generated project metadata
├── .env.example
└── docs and reports at root  # Architecture, testing, deployment, and audit material
```

## Prerequisites

- Python 3.11 (recommended; backend dependencies are aligned with the Docker runtime)
- Node.js 20+ and npm
- A Supabase project with the required schema and migrations applied
- A Groq API key for supported AI workflows
- Git LFS or equivalent artifact handling if your workflow requires large model files

## Quick start

### 1. Configure environment variables

Copy the example configuration and fill in the values for your environment:

```bash
cp .env.example .env
```

Required variables:

```dotenv
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
GROQ_API_KEY=your-groq-api-key
FRONTEND_URL=http://localhost:5173
ENABLE_DEMO_MODE=false
```

Never commit `.env`, service-role keys, model credentials, or patient data.

### 2. Start the backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_migration.py
uvicorn app.main:app --reload --port 8000
```

Backend API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs). The OpenAPI schema is available at [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json).

### 3. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### 4. Optional production build

```bash
cd frontend
npm run build
npm run preview
```

## API surface

The FastAPI application exposes interactive documentation and includes these main route groups:

| Area | Examples |
| --- | --- |
| Health | `/health`, `/ready`, `/metrics` |
| Intake and patients | `/intake`, `/api/...` |
| NLP and risk | `/nlp/...`, `/risk/...` |
| Evidence and analysis | `/evidence/...`, `/api/evidence`, `/api/lab-analysis`, `/api/imaging-analysis` |
| Investigations | `/api/investigations`, `/investigation/...` |
| Reports and pipeline | `/api/report`, `/api/pipeline` |
| Copilot | `/api/copilot/...` |
| Explainability and search | `/api/explainability`, `/api/search` |
| Platform operations | `/api/admin`, `/api/platform-metrics`, `/api/release` |

Use the generated Swagger UI as the source of truth for request and response schemas.

## Development commands

### Frontend

```bash
npm run dev       # Start the Vite development server
npm run build     # Create a production build
npm run preview   # Serve the production build locally
npm run lint      # Run ESLint
npm run format    # Format frontend files with Prettier
```

### Backend

```bash
uvicorn app.main:app --reload --port 8000
python run_migration.py
```

## Documentation

- [Production Readiness Report](Production_Readiness_Report.md)
- [Deployment Checklist](Deployment_Checklist.md)
- [Clinical Workflow Guide](Clinical_Workflow_Guide.md)
- [Clinical Knowledge Base Guide](Clinical_Knowledge_Base_Guide.md)
- [Knowledge Base Authoring Guide](Knowledge_Base_Authoring_Guide.md)
- [Copilot Architecture](PRATHAM_Copilot_Architecture.md)
- [Engineering Case Study](PRATHAM_Engineering_Case_Study.md)
- [Security Audit Report](Security_Audit_Report.md)
- [Performance Report](Performance_Report.md)

## Production considerations

Before any real-world deployment, the following must be completed and independently verified:

- Restore or provision a reachable Supabase environment and apply all migrations.
- Add backend authentication, authorization, role enforcement, and session management.
- Complete privacy, threat-modeling, secret-management, and audit-log reviews.
- Validate all clinical models and scoring workflows with qualified clinical stakeholders.
- Test the complete intake-to-report journey against a representative non-production dataset.
- Review dependency vulnerabilities and establish an upgrade policy.
- Configure the production frontend origin instead of localhost CORS entries.
- Define monitoring, backups, incident response, data retention, and rollback procedures.

The [Production Readiness Report](Production_Readiness_Report.md) records known gaps and should be reviewed before planning a deployment.

## Safety and responsible use

PRATHAM surfaces information to support trained clinicians and operational teams. Model predictions, extracted findings, scores, and copilot responses may be incomplete or incorrect. Every output must be reviewed against the underlying evidence and local clinical protocols by an appropriately qualified professional.

## License

No license file is currently included. Until a license is added, all rights are reserved by the copyright holder.
