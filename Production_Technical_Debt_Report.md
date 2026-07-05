# PRATHAM Production Technical Debt Report

This report presents a thorough review of technical debt, code duplication, database schema health, dependency specifications, and dead/obsolete paths across the PRATHAM platform.

---

## 1. Codebase & Imports Audit

### Obsolete / Deprecated Endpoints
- **Files**:
  - `backend/app/api/imaging.py`
  - `backend/app/api/labs.py`
  - `backend/app/api/investigation.py`
- **Assessment**: These were the initial prototype stubs. Since the core clinical pipeline in `intake.py` and dedicated routers (`lab_analysis.py`, `imaging_analysis.py`, `investigations.py`) have fully replaced them, these stub routes have been marked as `@deprecated` with warnings logged to prevent any active production calls.
- **Action**: Retained with active deprecation flags to ensure backwards compatibility with early-stage E2E test scripts.

### Dead / Stale Code
- Checked all helper services under `backend/app/services`.
- Removed raw `print()` statements and replaced them with standard structured events in the core lifespans and routers.

---

## 2. Database Schema & Constraint Audit

The PRATHAM PostgreSQL schema (`schema.sql`) was reviewed for constraint safety, index optimization, and relational cascading:

### Referential Integrity & Cascades
- **Emergency Intake Table**: `patient_id` references `patients(id) ON DELETE CASCADE`.
- **Vitals, Symptoms, NLP Extractions, Risk Scores, Alerts, Recommendations, Pipeline Status Tables**: All reference `intake_id` with `ON DELETE CASCADE`.
- **Outcome**: Deleting a patient or intake sweeps all associated downstream telemetry cleanly, preventing orphaned data records.

### Database Index Mapping
- Unique composite index `idx_pipeline_stage` on `pipeline_status(intake_id, stage)` guarantees that duplicate pipeline stages are never inserted.
- Index `idx_pipeline_intake` on `pipeline_status(intake_id)` optimizes live status polling lookup times.
- Recommendation: Add index on `investigation_recommendations(intake_id)` to speed up patient workstation loading.

---

## 3. Dependency Audit & Package Health

### Backend Dependencies (`requirements.txt`)
- Standardized FastAPI, Uvicorn, Supabase, PyTorch, and Groq dependencies.
- No duplicate or unversioned packages.

### Frontend Dependencies (`package.json`)
- React 19 and TanStack Router / Start configurations checked.
- Obsolete package configurations cleaned up.
