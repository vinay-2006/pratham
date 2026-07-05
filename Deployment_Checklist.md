# PRATHAM Production Deployment Checklist

This document tracks readiness requirements for deploying the PRATHAM platform to production or staging environments.

---

## 1. Pre-Deployment Configuration Audit

- [ ] **Environment Validation**:
  - Verify `.env` is populated with active keys:
    - `SUPABASE_URL`
    - `SUPABASE_ANON_KEY`
    - `SUPABASE_SERVICE_ROLE_KEY`
    - `GROQ_API_KEY`
    - `FRONTEND_URL`
  - Run startup dry run: `python -c "import app.main"` to check for config errors.
- [ ] **Secret Safety Verification**:
  - Verify `.env` is listed in `.gitignore`.
  - Ensure no API keys or local database passwords are hardcoded in services.

---

## 2. Containerized Environment (Docker)

- [ ] **Multi-Container Composition (`docker-compose.yml`)**:
  - Backend is bound to host port `8000`.
  - Frontend is bound to host port `5173`.
  - Volumes map `/app/ml_models` locally to cache weight files.
- [ ] **Container Healthchecks**:
  - Verify backend health check: `curl -f http://localhost:8000/health`.
  - Verify ready check: `curl -f http://localhost:8000/ready`.

---

## 3. Database Schema & Storage Setup

- [ ] **Database Schema Execution**:
  - Execute `schema.sql` inside Supabase SQL editor to create base tables.
  - Run migrations in `backend/migrations/` sequentially using `run_migration.py`.
- [ ] **Supabase Storage Bucket Configuration**:
  - Create storage bucket named `evidence`.
  - Ensure storage policy allows authenticated/service role access for file read/write.

---

## 4. Production Operations & Backups

- [ ] **Log Ingestion**:
  - Structured JSON logs from backend `stdout` are routed to centralized logging tools (e.g. CloudWatch, Datadog).
- [ ] **Backup Schedule**:
  - Database: Configure daily automatic backups in Supabase dashboard.
  - Storage: Set up bucket replication rules for uploaded media.
