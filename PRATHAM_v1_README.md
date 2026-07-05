# PRATHAM v1 System README

Welcome to **PRATHAM v1** — Clinical Decision Support & Multi-Modal Emergency Triage System.

## Project Structure

```text
pratham/
├── backend/                  # FastAPI Backend Services & Risk Engines
│   ├── app/
│   │   ├── api/              # API Endpoints (intake, lab, imaging, report, pdf)
│   │   ├── services/         # Clinical reasoning, investigation, visit classification
│   │   └── main.py           # FastAPI application entrypoint
├── frontend/                 # React + Vite + Tailwind Frontend
│   └── src/
│       ├── components/       # Clinical report, investigation row, risk card
│       └── lib/              # API integration libraries
├── PRATHAM_v1_Architecture.md
├── PRATHAM_v1_Deployment_Guide.md
└── PRATHAM_v1_Demo_Script.md
```

## Key Features

1. **Intelligent Triage & Intake**: Classifies emergency vs routine visits automatically.
2. **Pathway-Gated Investigations**: Recommends targeted diagnostic panels based on active symptoms and vitals.
3. **Multi-Modal AI Pipeline**: Combines clinical NLP, imaging intelligence, and laboratory analysis.
4. **Deterministic Reasoning Engine**: Auditable clinical conclusions with qualitative confidence mapping.
5. **Unified 17-Section Clinical Report**: Seamless sync between interactive Web UI and A4 PDF exports.

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
