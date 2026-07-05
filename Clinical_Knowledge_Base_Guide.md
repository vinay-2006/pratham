# Clinical Knowledge Base Architecture Guide

## Overview

The PRATHAM v2 Knowledge Base is a declarative, versioned repository of disease rules located in `backend/app/knowledge_base/`.

```text
backend/app/knowledge_base/
├── acs.yaml
├── aki.yaml
├── arrhythmia.yaml
├── asthma.yaml
├── copd.yaml
├── dka.yaml
├── heart_failure.yaml
├── hemorrhagic_shock.yaml
├── pe.yaml
├── pneumonia.yaml
├── seizure.yaml
├── sepsis.yaml
└── stroke.yaml
```

## Disease Rule Schema

Each disease rule is written in YAML and contains:
- `condition_key`: Canonical identifier (e.g. `acs`, `pneumonia`).
- `condition_name`: Human-readable clinical title.
- `version`: Knowledge Base version (e.g. `2.0`).
- `supporting_patterns`: List of disease-agnostic clinical patterns matched by the `clinical_pattern_engine.py`.
- `supporting_findings`: Specific vitals, lab analytes, symptoms, and imaging findings that support the diagnosis.
- `conflicting_findings`: Findings that conflict with or lower the probability of the diagnosis.
- `monitoring_priorities`: Key physiological parameters to track.
- `clinical_precautions`: Immediate safety precautions.
- `suggested_investigations`: Recommended diagnostic procedures.
- `limitations`: Diagnostic caveats and limitations.
