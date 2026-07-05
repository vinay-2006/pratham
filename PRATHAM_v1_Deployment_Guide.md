# PRATHAM v1 Production Deployment Guide

## Overview
This guide describes the production deployment procedures for PRATHAM v1, including environment requirements, Supabase migrations, FastAPI backend setup, and React frontend build.

## Prerequisites
- **Python**: 3.10+
- **Node.js**: 18+
- **Supabase Account & Database**: Postgres database with pgvector support
- **Environment Variables**: See `.env.example` in `backend/` and `frontend/`

## Environment Setup

### Backend (.env)
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
GROQ_API_KEY=your-groq-api-key
PORT=8000
```

### Database Setup
Run database migrations using the provided scripts:
```bash
python backend/run_migration.py
```

## Docker Deployment
```bash
# Build & start containers
docker-compose up --build -d
```

## Health Check
- Backend status: `GET http://localhost:8000/health`
- API documentation: `GET http://localhost:8000/docs`
