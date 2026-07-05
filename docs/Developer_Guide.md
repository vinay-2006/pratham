# PRATHAM Developer Guide

This guide assists engineers in setting up local development workspaces, authoring custom knowledge-base rules, and extending the 7-layer pipeline.

---

## 1. Local Setup

### Backend Setup
1. Create virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run migrations:
   ```bash
   python run_migration.py
   ```
3. Start backend dev server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup
1. Install packages:
   ```bash
   cd frontend
   npm install
   ```
2. Start dev server:
   ```bash
   npm run dev
   ```

---

## 2. Authoring 13 Emergency Condition YAML Rules

To add or modify emergency disease criteria:
1. Locate YAML files under: `backend/app/knowledge_base/` (e.g. `pneumonia.yaml`, `sepsis.yaml`).
2. Add support markers, required scores, and analyte indicators:
   ```yaml
   condition: "diabetic_ketoacidosis"
   key_findings:
     - glucose_threshold: 250
     - anion_gap_threshold: 12
   confidence_weights:
     anion_gap_acidosis: 0.45
     hyperglycemia: 0.20
   ```

---

## 3. Running Regression Test Suites

PRATHAM uses deterministic validation scripts:
- **Clinical Pipeline regression**: `python test_scenarios_phase2.py` verifies all 20 emergency mock patients.
- **Copilot verification**: `python test_copilot_system.py` validates all 8 conversational intents.
