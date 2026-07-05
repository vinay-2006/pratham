# PRATHAM API Reference — v5.0.0

This document catalogs the REST API endpoints exposed by the PRATHAM FastAPI backend (running on port `8000`).

Full interactive documentation: `http://localhost:8000/docs`

---

## 1. Intake & NLP Services

### `POST /api/intake`
Creates a new emergency patient record, persisting patient demographics, vitals, symptoms, and triggering the async AI pipeline (NLP + Risk scoring).

**Payload:**
```json
{
  "patient": { "first_name": "Ravi", "last_name": "Kumar", "date_of_birth": "1975-01-01", "gender": "male", "contact_number": "9999999999", "allergies": [], "current_medications": [], "past_medical_history": [] },
  "intake": { "ambulance_eta": 10, "emergency_description": "Acute chest pain radiating to left arm", "chief_complaint": "Chest pain" },
  "vitals": { "heart_rate": 118, "spo2": 90, "bp_systolic": 95, "bp_diastolic": 60, "temperature": 37.2, "respiratory_rate": 28 },
  "symptoms": { "chest_pain": true, "breathlessness": true, "trauma": false, "bleeding": false, "unconsciousness": false, "neurological_symptoms": false }
}
```

### `POST /nlp/extract`
Triggers Groq LLM NLP entity extraction to flag symptoms and history from intake free-text notes.

---

## 2. Diagnostics & Scoring

### `POST /api/lab/analyze`
Evaluates uploaded lab values against demographic-aware normal ranges using the XGBoost Lab Intelligence Engine.

### `POST /api/imaging/analyze`
Triggers EfficientNetB0 classification on Chest X-Rays uploaded to Supabase Storage.

### `GET /api/pipeline/status/{intake_id}`
Returns live progress stats for all 5 AI pipeline stages (nlp, risk, lab, imaging, aggregation).

---

## 3. Evidence & Clinical Reports

### `POST /api/evidence/upload`
Uploads a file (X-ray, lab report, ECG, clinical notes) to Supabase Storage and creates an evidence record.

### `GET /api/evidence/{intake_id}`
Lists all evidence rows for a given intake.

### `GET /api/report/{intake_id}`
Returns the full consolidated Clinical Intelligence Report in JSON format.

### `GET /api/report/{intake_id}/pdf`
Streams a PDF export of the Clinical Intelligence Report.

---

## 4. Investigations

### `GET /api/investigations/queue`
Returns all pending investigation requests across all patients.

### `GET /api/investigations/patient/{intake_id}`
Returns investigation recommendations for a specific intake.

### `POST /api/investigations/approve`
Approves a pending investigation recommendation.

### `POST /api/investigations/reject`
Rejects a pending investigation recommendation.

### `POST /api/investigations/needs-info`
Flags an investigation as requiring additional clinical information.

---

## 5. Evidence-Aware Copilot

### `POST /api/copilot/query`
Submits a natural-language query to the deterministic Clinical Copilot orchestrator.

**Payload:**
```json
{
  "query": "Why was Pneumonia ranked first?",
  "session_id": "SESSION-123",
  "intake_id": "INT-901",
  "mode": "CLINICAL"
}
```

**Supported intents:** `EXPLAIN_CONDITION`, `COMPARE_CONDITIONS`, `TIMELINE_QA`, `REPORT_SUMMARY`, `INVESTIGATION_ASSISTANT`, `EXPLAINABILITY_MODE`, `KNOWLEDGE_BASE_SEARCH`, `PIPELINE_EXPLANATION`

### `GET /api/copilot/history/{session_id}`
Returns conversation history for a session.

---

## 6. Telemetry & Platform Health

### `GET /health`
Liveness check probe. Returns `{"status": "ok"}`.

### `GET /ready`
Readiness check verifying active Supabase DB connection and valid Groq API key.

### `GET /metrics`
Observability telemetry: average stage latencies and execution counts from live pipeline_status data.

### `GET /api/version`
Returns current release version metadata (`v5.0.0`).

### `GET /api/release`
Returns full release information including version, branch, commit hash, and status.

---

## 7. Admin & Command Center

### `GET /api/admin/metrics`
System operational metrics: stage latencies (live from pipeline_status), subsystem health.

### `GET /api/command-center/telemetry`
Live Emergency Department queue: patient list with triage priority, severity, and color code.

### `GET /api/platform-metrics/telemetry`
Platform codebase statistics (cached at startup): LOC, component counts, engine versions.

---

## 8. Demo Mode (requires `ENABLE_DEMO_MODE=true`)

### `GET /api/demo/cases`
Returns the library of 10 pre-built clinical demonstration cases.

### `POST /api/demo/load/{case_id}`
Loads a demo case into the database (creates patient + intake + vitals + symptoms).

### `POST /api/demo/reset`
Resets all demo patient data without touching schema. Safe to run repeatedly.

---

## ⚠️ Deprecated Endpoints (still registered for compatibility)

| Endpoint | Replacement |
|----------|-------------|
| `POST /evidence/xray` | `POST /api/imaging/analyze` |
| `POST /evidence/labs` | `POST /api/lab/analyze` |
| `POST /investigation/recommend` | Full investigations workflow |
