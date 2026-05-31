# PRATHAM — Predictive Risk Assessment & Triage for Healthcare AI Management

> A full-stack medical AI platform for emergency patient intake, real-time risk stratification, intelligent investigation recommendations, and evidence aggregation.

---

## 🏥 Overview

PRATHAM is an AI-assisted clinical decision support system designed for emergency departments. It combines natural language processing, multi-modal evidence analysis (imaging + labs), and risk scoring to help clinicians triage patients faster and more accurately.

### Core Capabilities

| Module | Description |
|---|---|
| **Emergency Intake** | Structured patient data capture with NLP-assisted symptom extraction |
| **Risk Assessment** | Severity scoring based on vitals, history, and clinical flags |
| **Investigation Panel** | AI-recommended diagnostic workups |
| **Evidence Aggregation** | Unified view of X-ray, lab, and vitals findings |
| **Feedback Log** | Clinician feedback loop for continuous model improvement |

---

## 🗂️ Project Structure

```
pratham/
├── frontend/          # React + TypeScript + Tailwind CSS
├── backend/           # FastAPI + Python 3.11
├── notebooks/         # Colab training notebooks
├── data/              # Test datasets
├── ml_models/         # Trained model weights (.pt, .json)
└── docker-compose.yml # Full-stack orchestration
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js >= 18
- Python 3.11
- Docker & Docker Compose (optional)
- A Supabase project (URL + anon key)

### Environment Setup

```bash
cp .env.example .env
# Fill in your SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY, FRONTEND_URL
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

### Docker (Full Stack)

```bash
docker-compose up --build
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/intake` | Submit patient intake form |
| POST | `/nlp/extract` | Extract structured data from clinical notes |
| POST | `/risk/assess` | Calculate patient risk score |
| POST | `/investigation/recommend` | Get recommended investigations |
| POST | `/evidence/xray` | Analyze X-ray findings |
| POST | `/evidence/labs` | Process lab results |
| POST | `/aggregate` | Aggregate all evidence into unified report |

---

## 🧠 Technology Stack

**Frontend**
- React 18 + TypeScript
- Tailwind CSS
- React Router v6
- Axios

**Backend**
- FastAPI
- Pydantic v2 (strict typing)
- Supabase PostgreSQL
- Python 3.11

**AI/ML** *(planned)*
- Groq LLM API (NLP extraction)
- Custom PyTorch models (imaging)
- BERT-based clinical NER

---

## 🗺️ Roadmap

- [ ] NLP symptom extraction via Groq
- [ ] Risk scoring ML model
- [ ] CXR (Chest X-Ray) AI analysis
- [ ] Lab value anomaly detection
- [ ] Real-time websocket dashboard
- [ ] FHIR R4 integration
- [ ] Audit logging & compliance

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
