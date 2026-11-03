# PRATHAM — Production Readiness Report

Date: 2026-10-27 · Branch: `phase-a-stabilization` · Scope: frontend (TanStack Start/Vite), backend (FastAPI), browser behaviour.

## A. Summary

**Verdict: NOT production-ready — one hard blocker, plus unverified end-to-end behaviour.**

**Blocker:** the Supabase host in `backend/.env` no longer resolves (`[Errno 8] nodename nor servname`), so the project is probably deleted or paused. Every DB-backed workflow (intake, queue, approvals, evidence upload, pipeline, report generation, copilot data) could **not** be tested against a real database. Nothing below claims otherwise.

### Defects found and fixed

| Sev | Defect | Fix | Verified by |
|---|---|---|---|
| P0 | `/dashboard`, `/imaging`, `/investigations` call `useState` after an early return. When a patient case loads after first render React throws "order of Hooks changed" and the page dies. | Hooks moved above the early return. | Browser test reproduces the crash on the old code (3/3 fail) and passes on the fix (3/3). |
| P1 | Doctor report page reads fields the API never returns (`status`, `evidence_list`, `case_id`, `arrival_type`, `severity`, `created_at`). Result: Close Case never switches to the closed state, the new-evidence warning never fires, polling never stops, and the cover sheet shows blanks. | Backend DTO now returns the fields; `status` is resolved live because the report cache holds for 120s. Frontend uses `evidence` and the top-level fields. | 3 pytest tests plus a mocked-network browser test (ready vs closed). |
| P1 | Unhandled 500s carried no CORS headers, so the browser reported a generic "network error" instead of a server error. | Handler adds CORS headers for allowed origins. | pytest (fails without the fix, passes with it) and curl. |
| P1 | 21 endpoints return `detail=str(e)` on 500, exposing internals (DB hostnames, driver errors) to clients. | Central handler replaces any 5xx detail with a generic message and logs the original. 4xx details are kept. | pytest; curl shows a generic body. |
| P2 | Raw backend/exception text shown in UI error banners. | New `lib/api-error.ts` (`apiErrorMessage`); 13 call sites use it. 4xx validation text is kept, 5xx and network failures get plain wording. | Browser screenshot of the queue error state. |
| P2 | Horizontal overflow at tablet width (820px) on every app route; the header was clipped. | Top-bar patient block and Pending chip appear at wider breakpoints; `min-w-0` on the inset; Knowledge Base grid uses `minmax(0,1fr)` and `lg:` columns. | 84 route×viewport loads: overflow 28 → 0. |
| P2 | Nested `<main>` landmarks (a11y). | Inner `<main>` changed to `<div>`. | Playwright strict-mode locator caught it. |
| P3 | Duplicate "Admin Telemetry" entry in the sidebar. | Showcase copy removed. | Visual. |
| P3 | 31 TypeScript errors: undefined `"xs"` button size (unstyled), `StatusPipeline` and mock-data types, and report types. | Added `xs` size; types corrected. | `tsc --noEmit`: 31 → 0. |

### Environment problems found (not code defects)
- `frontend/node_modules` held Windows-only native binaries (rollup win32) and `.bin` shims without exec bit. The build failed until `npm install` was re-run (macOS binary installed). `npm run` still fails on `.bin` permissions; running tools through `node node_modules/<pkg>/…` works.
- `backend/requirements.txt` pins `pydantic==2.7.1`, which does not build on Python 3.13 (Dockerfile uses 3.11, so Docker is likely fine). Checks here ran on 3.13 using the anaconda packages.

## B. Component Status Matrix

Backend data flows are BLOCKED by the dead database. "Rendered" means the page loaded with no JS errors and no overflow, **not** that its data flow works.

| Component / Feature | Test performed | Status | Evidence / remaining issue |
|---|---|---|---|
| All 27 routes + 404 | Playwright load at desktop/tablet/mobile (84 loads) | PASS (render only) | 0 page errors, 0 overflow; data panels show error states because the DB is down |
| Patient context pages (`/dashboard`, `/imaging`, `/investigations`) | Delayed mocked `/api/intake/:id`, null → case transition | PASS | Fails on old code, passes on new |
| Doctor report page | Mocked `/api/report/:id`, status `clinical_report_ready` vs `case_closed` | PASS (mocked data) | Real report generation BLOCKED |
| `GET /api/report/{id}` (status overlay, cache not mutated, 404) | pytest with mocked services | PASS | 6/6 tests |
| 5xx sanitisation, CORS-on-500 | pytest + curl | PASS | |
| Queue / list error state | Browser, backend 500 | PASS | Banner now readable; retry button present |
| Nurse intake submit, patient queue, registry | — | BLOCKED | DB unreachable |
| Evidence upload / delete, investigation approval | — | BLOCKED | DB unreachable |
| NLP / risk / lab / imaging pipeline | — | BLOCKED | Needs DB; ML models load at startup (XGBoost OK, SHAP not installed → empty explanations) |
| Copilot, Command Center data | — | BLOCKED | Needs DB. Command Center now shows a server error instead of a CORS failure |
| `/api/version`, `/api/release`, `/api/evidence-map`, `/api/admin/metrics`, `/api/search` | curl GET | PASS (200) | Return empty or default data without the DB |
| `/ready` | curl | FAIL (expected) | 503 "Database health check failed" — correct behaviour, the DB is down |
| Auth / authorization / session expiry | Code and route inspection | NOT TESTED | No login. Role is a client-side toggle in localStorage; backend endpoints have no auth (see D) |
| Keyboard navigation, focus, contrast, forms with invalid input | — | NOT TESTED | Only the landmark check was done |
| PDF export, file upload/download | — | BLOCKED | Needs DB |

## C. Test Results

| Check | Command | Result |
|---|---|---|
| Type check | `node node_modules/typescript/bin/tsc --noEmit` | Baseline 31 errors → **0** |
| Lint (non-format rules) | `node node_modules/eslint/bin/eslint.js .` | rules-of-hooks 3 → **0**; `no-explicit-any` 16 and `only-export-components` 7 remain (pre-existing, not fixed) |
| Lint (prettier) | same | **18,329 errors**, nearly all CRLF line endings; deliberately not mass-reformatted (huge diff). Needs a `.gitattributes`/`eol=lf` decision |
| Production build | `node node_modules/vite/bin/vite.js build` | Baseline FAIL (Windows binaries) → **PASS** |
| Backend tests | `pytest backend/tests` | **6 passed** (new). Existing `backend/test_*.py` are live-server scripts; pytest collects 0 from them, and they need a working DB, so they were **not run** |
| Browser: route sweep | `routes.mjs` (scratch) | 84/84 loads without page errors; 0 overflow |
| Browser: regression | `frontend/e2e/hooks.e2e.mjs`, `report.e2e.mjs` | 3/3 and 2/2 pass |
| Dependency audit | `npm audit --omit=dev` | **25 vulns (7 critical, 16 high, 1 mod, 1 low)** — includes `@tanstack/react-start`, `axios`, `vite`, `zod`, `dompurify`, `seroval`. `npm audit fix` fails on a peer-dependency conflict with `@lovable.dev/vite-tanstack-config`; not forced. Python deps not audited |
| Secret scan | grep for JWT/`gsk_`/`sb_secret_` patterns | `.env` is gitignored and not tracked; the only hit is base64 image data in a local notebook |

## D. Outstanding Issues

1. **Blocker:** restore or recreate the Supabase project and rerun the existing e2e scripts and a full browser journey (intake → approval → evidence → report → close).
2. **No authentication or authorization** on backend routes; role switching is client-only. This must be addressed before any real patient data.
3. **27 untracked backend `.py` files** (e.g. `models/workflow.py`, `services/case_lifecycle_service.py`) are imported by the app. A deploy from git would crash; also `migrations/008`, `010`, `schema_v7.sql`. Commit them.
4. The npm vulnerabilities above; upgrading the TanStack/Lovable toolchain is a breaking change that needs its own pass.
5. `no-explicit-any` ×16 and fast-refresh warnings (low risk); CRLF/prettier policy.
6. Report page silently ignores a failed `mark-reviewed` call (logs a console warning only) and passes a hard-coded reviewer name `"Dr. Clinician"`.
7. Many `/doctor/*` routes render inside the Nurse sidebar until the role toggle is used; not changed (product decision).
8. SHAP isn't installed here, so explainability returns empty values; `numpy 2.5` / SciPy version warning at startup.
9. Python 3.13 vs pinned dependencies (`pydantic==2.7.1`); verify with the 3.11 Docker image.
10. Docs (`README`) reference `d:\pratham\...` Windows paths.

## E. Deployment Checklist

| Item | Status |
|---|---|
| Env vars (`SUPABASE_*`, `GROQ_API_KEY`, `FRONTEND_URL`) | Present locally; `.env` ignored by git. Supabase URL **does not resolve** |
| Secrets in repo | None found by pattern scan |
| DB migrations | NOT VERIFIED (DB unreachable); some migration files untracked |
| Authentication | **Missing** |
| Production build | PASS |
| Logging | Structured JSON logs; 5xx details now logged server-side only. Full PII audit not done |
| Error handling | Improved (generic 5xx, CORS, friendly UI errors); real-failure recovery paths not exercised against a DB |
| CORS | Origins from `FRONTEND_URL` + localhost ports; confirm production origin is set |
| Deployment config (`docker-compose.yml`, `wrangler.jsonc`) | NOT TESTED |

## Files changed (this pass)
Backend: `app/main.py`, `app/api/report.py`, `app/services/report_service.py`, `tests/test_report_endpoint.py` (new).
Frontend: `lib/api-error.ts` (new), `lib/report-api.ts`, `lib/mock-data.ts`, `components/{top-bar,app-shell,app-sidebar,knowledge-base-browser,status-pipeline,clinical-report}.tsx`, `components/ui/button.tsx`, six files switched to `apiErrorMessage`, routes `_app.{dashboard,imaging,investigations}.tsx`, `_app.doctor.report.$intakeId.tsx`, `_app.doctor.reports.tsx`, `e2e/*` (new).
Note: the working tree already held ~240 uncommitted changes before this pass, mostly CRLF/line-ending churn, so `git diff --stat` overstates what changed here.
