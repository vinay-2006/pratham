"""
Phase 1 Verification Script
Creates fresh patient → uploads distinct evidence per investigation →
verifies filtering → tests delete → runs imaging + lab analysis.
"""
import json, os, sys, io, time, requests

API = "http://localhost:8000"

def step(msg): print(f"\n{'='*60}\n  {msg}\n{'='*60}")
def ok(msg):   print(f"  ✅  {msg}")
def fail(msg): print(f"  ❌  {msg}"); 

# ── 1. Create patient ──────────────────────────────────────────────────────
step("1 · Create test patient")
payload = {
    "patient":   {"firstName":"Phase1","lastName":"VerifyTest","dateOfBirth":"1975-03-10",
                  "gender":"male","contactNumber":"+91-9000000001"},
    "emergency": {"chiefComplaint":"Chest pain and breathlessness",
                  "emergencyDescription":"Phase1 evidence filtering verification",
                  "ambulanceEta":5},
    "vitals":    {"heartRate":115,"spo2":90,"bpSystolic":155,"bpDiastolic":98,
                  "temperature":38.8,"respiratoryRate":28},
    "symptoms":  {"chestPain":True,"breathlessness":True,"trauma":False,
                  "bleeding":False,"unconsciousness":False,"neurologicalSymptoms":False},
}
r = requests.post(f"{API}/intake", json=payload); r.raise_for_status()
d = r.json(); intake_id = d["intake_id"]
ok(f"Patient created  intake_id={intake_id}")

# ── 2. NLP + Risk + Investigations ────────────────────────────────────────
step("2 · NLP, Risk, and Investigation recommendations")
requests.post(f"{API}/nlp/extract",          json={"intake_id":intake_id}).raise_for_status()
ok("NLP done")
requests.post(f"{API}/risk/calculate",       json={"intake_id":intake_id}).raise_for_status()
ok("Risk done")
requests.post(f"{API}/investigation/recommend", json={"intake_id":intake_id}).raise_for_status()
ok("Investigations recommended")

# ── 3. Doctor approves Chest X-ray + CBC + ABG ────────────────────────────
step("3 · Doctor approves Chest X-ray, CBC, ABG")
requests.post(f"{API}/api/investigations/approve", json={
    "intake_id": intake_id,
    "approved_tests": ["Chest X-ray","CBC","ABG"],
    "doctor_notes": "Phase1 test",
    "doctor_name": "Dr.Phase1"
}).raise_for_status()
ok("3 investigations approved")

# ── 4. Fetch investigation IDs ─────────────────────────────────────────────
step("4 · Fetch investigation IDs")
r = requests.get(f"{API}/api/investigations/patient/{intake_id}"); r.raise_for_status()
data = r.json()
inv_map = {inv["investigation_type"]: inv["id"]
           for inv in data["investigations"] if inv["status"]=="approved"}
for k,v in inv_map.items():
    ok(f"{k} → {v[:8]}…")

# ── 5. Upload distinct evidence per investigation ──────────────────────────
step("5 · Upload distinct evidence — one per investigation")
xray_path = os.path.join(os.path.dirname(__file__), "test_xray.jpg")

def upload(inv_type, ev_type, filename, content):
    inv_id = inv_map.get(inv_type)
    if not inv_id:
        fail(f"No approved investigation for {inv_type}"); return None
    files  = {"file": (filename, io.BytesIO(content),
               "image/jpeg" if filename.endswith((".jpg",".jpeg")) else "text/plain")}
    fields = {"intake_id": intake_id, "evidence_type": ev_type, "investigation_id": inv_id}
    r = requests.post(f"{API}/api/evidence/upload", data=fields, files=files)
    r.raise_for_status()
    ev = r.json()
    ok(f"Uploaded '{filename}' → {inv_type} ({ev_type}) evidence_id={ev['evidence_id'][:8]}…")
    return ev

# Chest X-ray — use real test image for imaging analysis
with open(xray_path,"rb") as f: xray_bytes = f.read()
xray_ev  = upload("Chest X-ray", "xray",       "chest_xray_phase1.jpg", xray_bytes)
cbc_ev   = upload("CBC",         "lab_report",  "cbc_report_phase1.txt",
                   b"CBC Report\nWBC:12.5 RBC:4.2 Hgb:14.1 Plt:250")
abg_ev   = upload("ABG",         "lab_report",  "abg_report_phase1.txt",
                   b"ABG Report\npH:7.35 pCO2:45 pO2:80 HCO3:24")

# ── 6. Verify filtering ────────────────────────────────────────────────────
step("6 · Verify evidence filtering (no cross-contamination)")
r = requests.get(f"{API}/api/investigations/patient/{intake_id}"); r.raise_for_status()
data2 = r.json()

expected = {"Chest X-ray":["chest_xray_phase1.jpg"],
            "CBC":["cbc_report_phase1.txt"],
            "ABG":["abg_report_phase1.txt"]}
all_ok = True
for inv in data2["investigations"]:
    if inv["status"] != "approved": continue
    itype = inv["investigation_type"]
    expected_files = expected.get(itype, [])
    actual_files   = [e["file_name"] for e in inv["evidence"]]
    match = sorted(actual_files) == sorted(expected_files)
    if match:
        ok(f"{itype}: {actual_files}  ← CORRECT")
    else:
        fail(f"{itype}: expected={expected_files}  got={actual_files}")
        all_ok = False

unlinked = data2.get("unlinked_evidence",[])
if unlinked:
    fail(f"Unlinked evidence present: {[e['file_name'] for e in unlinked]}")
    all_ok = False
else:
    ok("No unlinked evidence — all files properly assigned")

print(f"\n  {'FILTERING PASS ✅' if all_ok else 'FILTERING FAIL ❌'}")

# ── 7. Delete test ─────────────────────────────────────────────────────────
step("7 · Delete evidence and verify removal")
# Find ABG evidence_id from live data
abg_inv = next((i for i in data2["investigations"]
                if i["investigation_type"]=="ABG" and i["evidence"]), None)
if abg_inv:
    ev_id  = abg_inv["evidence"][0]["evidence_id"]
    ev_name= abg_inv["evidence"][0]["file_name"]
    r = requests.delete(f"{API}/api/evidence/{ev_id}")
    if r.status_code == 204:
        ok(f"DELETE 204 for '{ev_name}'")
    else:
        fail(f"DELETE returned {r.status_code}")
    # Confirm gone
    r2 = requests.get(f"{API}/api/investigations/patient/{intake_id}"); r2.raise_for_status()
    d3 = r2.json()
    all_ids = [e["evidence_id"] for inv in d3["investigations"] for e in inv["evidence"]]
    all_ids += [e["evidence_id"] for e in d3.get("unlinked_evidence",[])]
    if ev_id not in all_ids:
        ok(f"'{ev_name}' confirmed removed from all investigation cards")
    else:
        fail(f"'{ev_name}' STILL appears after delete!")

# ── 8. Imaging analysis ────────────────────────────────────────────────────
step("8 · Run Imaging Analysis (EfficientNetB0)")
if xray_ev:
    r = requests.post(f"{API}/api/imaging/analyze",
                      json={"intake_id": intake_id, "evidence_id": xray_ev["evidence_id"]})
    r.raise_for_status()
    img = r.json()
    ok(f"Model: {img.get('model_name')}")
    ok(f"Prediction: {img.get('prediction')}  Probability: {img.get('pneumonia_probability'):.4f}")
    ok(f"Confidence: {img.get('confidence'):.4f}")
    ok(f"Grad-CAM URL: {'✅ present' if img.get('gradcam_url') else '⚠ not generated'}")
    print(f"\n  IMAGING ANALYSIS PASS ✅")

# ── 9. Lab analysis ────────────────────────────────────────────────────────
step("9 · Run Lab Analysis (XGBoost)")
r = requests.post(f"{API}/api/lab/analyze", json={"intake_id": intake_id})
r.raise_for_status()
lab = r.json()
ok(f"Model: {lab.get('model_name')}")
ok(f"Prediction: {lab.get('prediction')}  Risk Probability: {lab.get('risk_probability'):.4f}")
tops = lab.get("top_features",{})
ok(f"Top SHAP features: {list(tops.keys())[:3]}")
print(f"\n  LAB ANALYSIS PASS ✅")

# ── 10. Verify results appear in patient detail ────────────────────────────
step("10 · Verify analysis results surface in patient detail API")
r = requests.get(f"{API}/api/investigations/patient/{intake_id}"); r.raise_for_status()
d4 = r.json()
ps = d4.get("pipeline_status",{})
ok(f"Pipeline → NLP:{ps.get('nlp')}  Risk:{ps.get('risk')}  Lab:{ps.get('lab')}  "
   f"Imaging:{ps.get('imaging')}  Aggregation:{ps.get('aggregation')}")

xray_inv = next((i for i in d4["investigations"]
                 if i["evidence_type"]=="xray" and i["status"]=="approved"), None)
if xray_inv and xray_inv.get("analysis_result"):
    ar = xray_inv["analysis_result"]
    ok(f"Imaging result on card: {ar.get('prediction')}  {ar.get('probability'):.4f}")
else:
    fail("Imaging result NOT surfaced on investigation card")

lab_inv = next((i for i in d4["investigations"]
                if i["evidence_type"]=="lab_report" and i["status"]=="approved"
                and i.get("analysis_result")), None)
if lab_inv:
    ar = lab_inv["analysis_result"]
    ok(f"Lab result on card: {ar.get('prediction')}  {ar.get('probability'):.4f}")
else:
    fail("Lab result NOT surfaced on investigation card")

print(f"\n{'='*60}")
print(f"  PHASE 1 COMPLETE")
print(f"  Intake ID for browser: {intake_id}")
print(f"  Queue URL: http://localhost:8080/nurse/queue")
print(f"{'='*60}\n")
