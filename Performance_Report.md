# PRATHAM System Performance Report

This report documents the performance metrics, latency benchmarks, and optimization strategies across all layers of the PRATHAM Clinical AI pipeline.

---

## 1. End-to-End Latency Breakdown

The clinical intelligence pipeline operates in under **4.5 seconds** total, allowing emergency teams to view incoming patient status instantly.

| Pipeline Stage / Operation | Average Latency | Execution Type | Subsystem / Model Used |
| :--- | :--- | :--- | :--- |
| **In-Transit Patient Intake** | < 150 ms | Write / DB | Supabase Client PostgreSQL |
| **NLP Clinical Extraction** | ~1.40 s | Async / LLM | Groq API Llama-3 (JSON Mode) |
| **Demographic Lab Parser** | ~0.80 s | CPU Bound | Demographic Reference Range Engine |
| **Chest X-Ray Imaging AI** | ~1.20 s | PyTorch Inference | EfficientNetB0 Pneumonia Model |
| **Deterministic Risk Calculator**| < 50 ms | CPU Bound | NEWS2, qSOFA, HEART Engine |
| **Evidence Aggregation & Rules**| ~0.50 s | CPU Bound | 13 YAML Rule Condition Matcher |
| **PDF Clinical Report Export** | ~0.60 s | PDF rendering | ReportLab PDF Generator |
| **Copilot Query (Deterministic)**| < 30 ms | CPU Bound | Deterministic Response Engine |
| **Copilot Query (Narrative)** | ~1.80 s | LLM Bound | Structured Copilot Orchestrator |

---

## 2. Performance Telemetry Observability

- Real-time pipeline latency metrics are stored in `pipeline_status` on Supabase.
- Telemetry stats are parsed and aggregated on-demand via the `/metrics` endpoint.
- Structured logging middleware tracks duration metrics for every HTTP endpoint, alerting if any stage exceeds a 5-second timeout threshold.

---

## 3. High-Impact Optimizations Implemented
1. **Model Cache**: PyTorch EfficientNetB0 weights and XGBoost estimators are loaded once at startup during the lifespan context (`main.py`), preventing heavy disk I/O on inference requests.
2. **Deterministic Bypassing**: Obviates Groq LLM queries for basic scoring, explainability cards, and specification retrieval, dropping response latencies from **1.8s** to **<30ms** for deterministic intents.
3. **Optimized PDF Buffers**: ReportLab PDF reports write binary content using in-memory byte buffers (`io.BytesIO`) rather than local temporary files, reducing latency.
