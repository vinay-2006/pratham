# PRATHAM Production Security Audit Report

This report evaluates the security posture of the PRATHAM platform, detailing safeguards against common vulnerabilities, file uploads, SQL injection, secrets leakage, and LLM prompt injections.

---

## 1. Secrets Management & Configuration Safety
- **Safeguard**: All sensitive keys (`SUPABASE_SERVICE_ROLE_KEY`, `GROQ_API_KEY`) are kept strictly inside the backend `.env` environment, never exposed or bundled into the frontend client.
- **Verification**: `validate_startup_config()` checks env parameters on startup, preventing server launch with placeholder values.

---

## 2. SQL Injection Prevention
- **Safeguard**: Database operations are conducted via the Supabase PostgREST Client SDK or parameterized SQLAlchemy queries. No raw string interpolation is used for user-facing parameters.
- **Outcome**: Protects against unauthorized table drops or cross-tenant data leakage.

---

## 3. CORS Configuration
- **Safeguard**: CORS origins are strictly controlled in `main.py` using `CORSMiddleware`.
- **Allowed Origins**: Limited to configured `FRONTEND_URL` and dev ports. No wildcards (`*`) allowed in production configuration.

---

## 4. Prompt Injection Safeguards (Copilot & Summary Engines)
- **Safeguard**: The Clinical Copilot uses structured JSON schemas loaded from the `Evidence Context Builders`. User input queries are routed into categorized intent classifiers (`copilot_intent_router.py`) rather than being concatenated directly into system instructions.
- **System Instruction Enforcements**:
  - Strictly forbidden from prescribing medication dosages or names.
  - Suppresses output when evidence is missing.
  - Defers to validated diagnostic rules rather than performing LLM diagnostics.

---

## 5. File Upload Verification (Imaging & Evidence)
- **Safeguard**: The evidence upload endpoint (`api/evidence.py`) validates uploaded files against standard medical/imaging MIME types (`image/jpeg`, `image/png`, `application/pdf`).
- **File size bounds**: Enforces size limits to prevent Denial of Service (DoS) via disk resource exhaustion.
