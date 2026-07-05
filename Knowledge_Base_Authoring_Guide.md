# Knowledge Base Authoring Guide

## How to Add a New Disease Definition to PRATHAM

To add a new condition to PRATHAM without writing Python code:

1. Create a new `.yaml` file in `backend/app/knowledge_base/` (e.g. `pericarditis.yaml`).
2. Follow the standardized YAML template:
   ```yaml
   condition_key: "pericarditis"
   condition_name: "Acute Pericarditis"
   version: "2.0"
   priority: 1
   description: "Inflammation of the pericardium presenting with pleuritic chest pain."
   supporting_patterns:
     - "myocardial_injury"
   supporting_findings:
     symptoms:
       - "chest_pain"
     vitals:
       - field: "heart_rate"
         operator: ">"
         threshold: 95
         label: "Mild tachycardia"
   conflicting_findings:
     labs:
       - analyte: "troponin"
         status: "HIGH"
   monitoring_priorities:
     - "Continuous ECG tracking for PR depression and diffuse ST elevation"
   clinical_precautions:
     - "Assess for cardiac tamponade signs (Beck's triad)"
   suggested_investigations:
     - "12-Lead ECG"
     - "Echocardiogram"
     - "ESR / CRP"
   limitations:
     - "Troponin elevation may occur if myopericarditis is present"
   ```
3. Restart backend service. The Evidence Ranking Engine will automatically discover, parse, rank, and integrate the new condition.
