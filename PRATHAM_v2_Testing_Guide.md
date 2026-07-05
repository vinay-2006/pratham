# PRATHAM v2 Testing & Validation Guide

## Running the Automated Test Suites

### 1. Execute 20 Clinical Scenarios Validation
```bash
python backend/test_scenarios_phase2.py
```

### 2. Verify Micro-Services & Reasoning Engine
```bash
python -c "from app.services.clinical_reasoning_service import derive_clinical_conclusions; print('OK')"
```

### 3. Verify Knowledge Base Parsing
```bash
python -c "from app.services.evidence_ranking_engine import rank_evidence_for_conditions; print(len(rank_evidence_for_conditions({}, [], [])))"
```
