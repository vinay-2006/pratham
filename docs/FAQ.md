# PRATHAM Platform FAQ

Frequently asked questions regarding architecture, clinical safety guardrails, and explainable AI design.

---

## 1. How does PRATHAM prevent LLM hallucinations?
PRATHAM isolates deterministic operations from the generative LLM:
- NEWS2, qSOFA, HEART, and Wells PE scores are calculated directly using Python math libraries.
- The 13 emergency condition rules are parsed directly from structured YAML files.
- The generative LLM is only called to synthesize a clean narrative layout, backed strictly by references to these verified metrics.

---

## 2. Why does the Clinical Copilot not prescribe medications?
To prevent clinical liability and ensure patient safety, PRATHAM is design-scoped strictly for emergency diagnostics and operational triage recommendations. System prompts explicitly forbid recommending drug names, dosages, or prescribing medications.

---

## 3. How does the structured logging middleware work?
A custom FastAPI middleware intercepts every request, generates a unique `X-Request-ID` tracing header, and logs execution latencies as structured JSON objects. This maps client requests directly to database query times and API calls for easy production monitoring.

---

## 4. Why are internal tracebacks hidden in production?
Exposing raw Python errors or Supabase PostgreSQL constraint errors can leak system paths, database structures, and keys. PRATHAM registers a global server exception handler that intercepts unhandled errors, logs the traceback internally with a request ID, and returns a clean `500 Internal Server Error` message to the client.
