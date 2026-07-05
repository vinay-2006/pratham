# PRATHAM Evidence-Aware Clinical & System Copilot Architecture Specification

## Overview
The **PRATHAM Evidence-Aware Clinical & System Copilot** transforms static emergency dashboards into an interactive, evidence-grounded conversational reasoning engine. It operates across 8 specialized query intents in dual operational modes (**Clinical Assistant** & **System Assistant**).

---

## 4-Tier Pipeline Architecture

```text
Doctor / Clinician / Admin Query
              │
              ▼
    Copilot Assistant Drawer UI (Clinical / System Mode)
              │
              ▼
    Tier 1: Intent Router (8 Intent Modes)
              │
              ▼
    Tier 2: Execution Planner (Context & LLM Strategy)
              │
              ▼
    Tier 3: Tool Registry (Decoupled Skill Handlers)
              │
              ▼
    Tier 4: Copilot Orchestrator & Deterministic Engine
              │
              ▼
    Structured Response Object (Citations, Evidence Replay, "Show Your Work")
```

---

## Key Subsystems & Micro-Modules

### 1. Modular Evidence Context Builders (`app/services/copilot/`)
- `patient_context.py`: Demographics and baseline risk factors.
- `clinical_findings.py`: Vitals, qualitative lab findings, and Medical Imaging Engine results.
- `reasoning_context.py`: Deterministic score calculations (NEWS2, qSOFA, CURB-65, HEART, Wells) & pattern syndromes.
- `knowledge_context.py`: 13 Emergency condition YAML rule criteria.
- `timeline_context.py`: Multi-visit analyte deltas and longitudinal trend analysis.
- `workflow_context.py`: Pipeline status, subsystem latencies, and operational telemetry.

### 2. Intent Routing & Execution Planning
- `copilot_intent_router.py`: Classifies queries into 8 intents (`EXPLAIN_CONDITION`, `COMPARE_CONDITIONS`, `INVESTIGATION_ASSISTANT`, `TIMELINE_QA`, `REPORT_SUMMARY`, `EXPLAINABILITY_MODE`, `KNOWLEDGE_BASE_SEARCH`, `PIPELINE_EXPLANATION`).
- `execution_planner.py`: Determines required data contexts and bypasses LLM synthesis for deterministic queries.

### 3. Tool Registry & Deterministic Engine
- `deterministic_engine.py`: Instant deterministic responses for scores, rules, confidence, and pipeline status.
- `tool_registry.py`: Skill handler map decoupled from core orchestrator loop.

### 4. Interactive Copilot UI
- `copilot-assistant-drawer.tsx`: Slide-over drawer with Clinical/System mode switcher, Explainability Cards, Interactive Evidence Replay flow, Sources & Citations badges, Suggested Questions chips, and expandable "Show Your Work" audit panel.

---

## Clinical Safety & Model Neutrality Safeguards
1. **Zero Medication Prescriptions**: System never prescribes drug names or dosages.
2. **Model Neutral Terminology**: Uses neutral engine names (`Medical Imaging Engine`, `Laboratory Intelligence Engine`) rather than specific model names.
3. **Explicit Missing Evidence Callouts**: Highlights missing investigations (e.g. Sputum culture, CTPA) explicitly in Explainability Cards.
4. **Deterministic Preference**: Bypasses LLM execution for deterministic questions, ensuring zero hallucination.
