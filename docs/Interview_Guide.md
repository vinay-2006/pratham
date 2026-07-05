# PRATHAM Technical Interview Guide

This guide compiles common engineering interview questions, design trade-offs, and scale details regarding the PRATHAM architecture.

---

## 1. Core Architecture & Safety

### Q: Why did you decide to use a deterministic-first design instead of a pure LLM approach?
- **Answer**: In emergency medicine, clinical calculations (NEWS2, qSOFA, HEART) require 100% precision. Large Language Models (LLMs) are prone to hallucinations and format shifts.
- **PRATHAM Design**: PRATHAM separates clinical logic into Python scripts. The LLM is only called to compile narrative layouts, backed strictly by deterministic calculations.

### Q: How do you handle diagnostic reference ranges dynamically?
- **Answer**: Lab reference ranges (e.g. Troponin, WBC) are demographic-aware. We mapped reference thresholds in `reference_range_service.py` based on age, sex, and pregnancy. The system evaluates numerical entries dynamically, returning flags like `CRITICAL_HIGH` or `NORMAL`.

---

## 2. API Hardening & Security

### Q: How do you prevent SQL Injection and protect tenant separation?
- **Answer**: Database operations are conducted using parameterized filters in the Supabase PostgREST client library. String interpolation is forbidden.

### Q: Why is there an `ENABLE_DEMO_MODE` environment flag?
- **Answer**: The database reset route (`POST /api/demo/reset`) executes clean deletions. To prevent accidental data deletion in production environments, the route is locked behind `ENABLE_DEMO_MODE=true`.

---

## 3. Telemetry & Performance Optimization

### Q: Filesystem scans are heavy. How do you calculate project scale metrics efficiently?
- **Answer**: We implemented a startup caching mechanism in `platform_metrics.py`. When the FastAPI application launches, the folder scanner iterates directories to calculate lines of code, service files, and API counts once. These are cached in-memory and served instantly to dashboard queries.
