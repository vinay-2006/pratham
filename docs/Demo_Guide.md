# PRATHAM Demonstration Guide

This guide is designed for presenters, developers, and candidates showcasing the PRATHAM platform during portfolio reviews, hackathons, or interview sessions.

---

## 1. Preparing the Demo Environment

### Step 1: Launch Backend with Demo Mode Active
Make sure you set the `ENABLE_DEMO_MODE=true` environment flag:
```bash
# Windows Power Shell
$env:ENABLE_DEMO_MODE="true"
cd backend
uvicorn app.main:app --reload --port 8000
```

### Step 2: Open the SaaS Landing Page
Navigate to `http://localhost:5173`. This serves as the SaaS homepage and developer console launchpad.

---

## 2. Interactive Step-by-Step Presentation Script

### Step 1: Start with the Guided Product Tour
1. Click **Start Interactive Product Tour** on the landing page hero banner.
2. Step through the 7 overlays, explaining how PRATHAM captures patient intakes in transit, runs multi-modal diagnostic validation layers, and displays evidence reviews for doctors.

### Step 2: Showcase the Showcase Demo Cases Library
1. Scroll down to the **Interactive Product Showcase** section.
2. Click **Reset Database** to clear the dashboard queue.
3. Select **Sepsis & Septic Shock** or **Diabetic Ketoacidosis (DKA)** from the list of 10 cases, and click **Load Case**.
4. Assert to the recruiter that a complete profile including vitals, symptoms, normal ranges, and diagnostics recommendations has been populated instantly.

### Step 3: Run the Clinical API Explorer (Playground)
1. Select the **API Client** tab on the showcase panel.
2. Select **Submit Intake (POST)**.
3. Click **Send Request**. Note the latency duration (e.g. 15ms) and select **UI Preview** to demonstrate how the raw JSON response is parsed into clean visual elements.

### Step 4: Show the Telemetry & Code base Metrics
1. Select the **Telemetry** tab to display dynamic repository statistics (total LOC, react components, backend services, API endpoints).
2. Point out that these metrics are computed dynamically on backend startup and cached to save overhead.
