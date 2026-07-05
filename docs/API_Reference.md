# PRATHAM API Reference

This document catalogs the REST API endpoints exposed by the PRATHAM FastAPI backend (running on port `8000`).

---

## 1. Intake & NLP Services

### `POST /intake`
- **Description**: Creates a new emergency patient record, saving vital signs and symptoms.
- **Payload**:
  ```json
  {
    "demographics": { "first_name": "John", "last_name": "Doe", "age": 45, "sex": "male" },
    "vitals": { "hr": 110, "bp": "100/60", "spo2": 91 },
    "chief_complaint": "Acute chest pain and severe SOB"
  }
  ```

### `POST /nlp/extract`
- **Description**: Triggers LLM NLP entity extraction to flags symptoms and history from intake free-text notes.

---

## 2. Diagnostics & Scoring

### `POST /api/lab-analysis`
- **Description**: Evaluates uploaded numerical lab values against demographic-aware normal ranges.

### `POST /api/imaging/analyze`
- **Description**: Triggers PyTorch EfficientNetB0 classification on Chest X-Rays.

### `GET /api/pipeline/status/{intake_id}`
- **Description**: Returns live progress stats for all 5 AI pipeline stages.

---

## 3. Evidence & Clinical Reports

### `POST /api/report/generate`
- **Description**: Creates a grounded clinical report summarizing risk scores, rule matching, and PDF generation.

---

## 4. Evidence-Aware Copilot

### `POST /api/copilot/query`
- **Description**: Submits Q&A prompt to the structured clinical copilot orchestrator.
- **Payload**:
  ```json
  {
    "query": "Why was Pneumonia ranked first?",
    "session_id": "SESSION-123",
    "intake_id": "INT-901",
    "mode": "CLINICAL"
  }
  ```

---

## 5. Telemetry & Platform Health

### `GET /health`
- **Description**: Liveness check probe.

### `GET /ready`
- **Description**: Readiness check verifying active Supabase DB and Groq connectivity.

### `GET /metrics`
- **Description**: Observability telemetry returns average stage latencies and run counts.

### `GET /api/version`
- **Description**: Returns current release version metadata.
