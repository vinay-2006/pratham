# PRATHAM v1 Clinical Demonstration Script

## Demo Scenario 1: Acute Coronary Syndrome (Emergency Intake)
1. **Intake Creation**:
   - Patient: 58-year-old male presenting with crushing chest pain, dyspnea, HR 105 bpm, BP 150/95 mmHg.
   - Severity: High / Critical.
2. **Investigation Recommendation**:
   - System automatically triggers Cardiac Pathway: `ECG`, `Troponin`, `CBC`.
3. **Investigation Upload & Execution**:
   - Upload Troponin report -> click **Run AI Analysis**.
4. **Clinical Report Verification**:
   - Verify Primary Condition: Acute Coronary Syndrome.
   - Verify Qualitative Confidence: `HIGH` or `VERY HIGH`.
   - Verify Absence of raw ML algorithm names in clinical cards.
5. **PDF Export**:
   - Click **Download PDF Report** and confirm clean layout with Section 17 disclaimers.

---

## Demo Scenario 2: Routine Health Checkup (Asymptomatic Intake)
1. **Intake Creation**:
   - Patient: 35-year-old female presenting for routine annual checkup. Vitals normal (HR 72, BP 118/78, SpO2 99%), symptoms absent.
2. **Routine Trigger Verification**:
   - System automatically triggers Routine Checkup Baseline Panel: `CBC`, `Basic Metabolic Panel`, `Blood Glucose`, `Urinalysis`.
   - Zero imaging tests recommended.
3. **Unsupported Test Behavior**:
   - Select an unsupported test (e.g. MRI Brain). Verify UI displays `Approved` + `"Analysis not available in this version"` and disables `Run Analysis`.
