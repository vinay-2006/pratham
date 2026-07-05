# PRATHAM Platform Architecture

PRATHAM (Predictive Risk & Automated Triage Hospital Assistance Matrix) is an emergency clinical decision support system built using a modular micro-services design.

---

## 7-Layer Processing Pipeline

To eliminate LLM hallucination and ensure absolute clinical calculation safety, PRATHAM segregates deterministic logic from generative synthesis:

```text
               Patient Data (Vitals, Symptoms, Free-text Intake)
                                     │
                                     ▼
                Layer 1: Clinical Context Demographic Adjuster
              (Pregnancy, Age, Chronic baseline creatinine status)
                                     │
                                     ▼
                  Layer 2: Reference Range Status Evaluator
                  (Analyte → Range → qualitative status: HIGH)
                                     │
                                     ▼
                    Layer 3: Lab & Chest Radiograph Engine
                  (Pneumonia probability, Lab analyte parsed)
                                     │
                                     ▼
                        Layer 4: Pattern Engine
                  (Respiratory distress, Shock, Inflammation)
                                     │
                                     ▼
                      Layer 5: Clinical Scoring Engine
                 (NEWS2 · qSOFA · CURB-65 · HEART · Wells PE)
                                     │
                                     ▼
                  Layer 6: 13 Emergency Condition Engine
               (YAML specification support/conflict ranking)
                                     │
                                     ▼
                  Layer 7: Grounded LLM Report Generator
                   (Structured 4-tier recommendation PDF)
```

---

## Evidence-Aware Clinical & System Copilot

The Clinical Copilot features an interactive evidence-grounded Q&A engine:
- **Clinical Mode**: Doctors/nurses query patient telemetry, differentials, missing data, and score rationales.
- **System Mode**: Admins query pipeline status, execution blockages, and latency details.

### Orchestration Flow:
1. **Intent Router**: Classifies queries into 8 intents.
2. **Execution Planner**: Bypasses LLM execution for deterministic questions.
3. **Tool Registry**: Calls modular skill handlers.
4. **Structured Response**: Returns answer confidence, citations, interactive evidence replay nodes, and a "Show Your Work" reasoning panel.
