# PRATHAM Deployment Guide

This guide details steps to deploy and manage the PRATHAM platform in dockerized or cloud-native staging/production environments.

---

## 1. Environment Variable Configuration

Create a secure `.env` file in the root directory:
```bash
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
GROQ_API_KEY="gsk_your_key"
FRONTEND_URL="http://localhost:5173"
```

---

## 2. Docker Compose Deployment

Launch multi-container backend and frontend service compositions:

```bash
# Build and start services
docker-compose up -d --build

# View container logs
docker-compose logs -f
```

- **Backend Port**: `8000` (FastAPI Swagger UI available at `http://localhost:8000/docs`).
- **Frontend Port**: `5173` (React workspace web application).

---

## 3. Production Health Probes

Integrate system healthchecks into load balancers (e.g. AWS ALB, Nginx, or Kubernetes probes):

1. **Liveness Check**:
   - Path: `GET /health`
   - Action: Asserts backend process is active.
2. **Readiness Check**:
   - Path: `GET /ready`
   - Action: Asserts active connections to Supabase PostgreSQL and Groq LLM API.
3. **Observability Telemetry**:
   - Path: `GET /metrics`
   - Action: Returns database latency statistics.
