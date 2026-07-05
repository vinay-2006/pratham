"""
Verify evidence_breakdown_json: bypass pipeline guards, call scoring directly,
persist with new columns, then verify report service picks it up.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from app.db.supabase_client import supabase

intake_id = "b81583ae-4b1c-49b6-aae1-66262bb5fd1a"
print(f"Intake: {intake_id}")

# Step 1: Check what upstream data exists
print("\n" + "=" * 60)
print("STEP 1: Checking upstream data...")
print("=" * 60)

from app.api.aggregation import _fetch_nlp, _fetch_risk, _fetch_lab, _fetch_imaging

nlp = _fetch_nlp(intake_id)
risk = _fetch_risk(intake_id)
lab = _fetch_lab(intake_id)
imaging = _fetch_imaging(intake_id)

print(f"  NLP: {'present' if nlp else 'missing'}")
print(f"  Risk: {'present' if risk else 'missing'}")
print(f"  Lab: {'present' if lab else 'missing'}")
print(f"  Imaging: {'present' if imaging else 'missing'}")

# Step 2: Score evidence directly (bypass pipeline guards)
print("\n" + "=" * 60)
print("STEP 2: Running evidence scoring...")
print("=" * 60)

from app.api.aggregation import _score_evidence, _check_suppression, _normalize, CONDITIONS

raw_scores, evidence_breakdown = _score_evidence(nlp, risk, lab, imaging)
print(f"  Raw scores: {raw_scores}")
print(f"  Evidence breakdown:")
for cond, trails in evidence_breakdown.items():
    print(f"    {cond}: {trails}")

source_summary = {
    "nlp": nlp is not None,
    "risk": risk is not None,
    "lab": lab is not None,
    "imaging": imaging is not None,
}
sources_present = sum(source_summary.values())
suppressed, suppression_reason = _check_suppression(raw_scores, sources_present)

if suppressed:
    print(f"\n  Suppressed: {suppression_reason}")
    probabilities = {c: None for c in CONDITIONS}
    primary_condition = None
else:
    prob_map = _normalize(raw_scores)
    probabilities = {c: prob_map[c] for c in CONDITIONS}
    primary_condition = max(prob_map, key=lambda c: prob_map[c])
    print(f"\n  Primary: {primary_condition}")
    print(f"  Probabilities: {probabilities}")

# Step 3: Persist with new columns
print("\n" + "=" * 60)
print("STEP 3: Persisting with new columns...")
print("=" * 60)

from datetime import datetime, timezone
now = datetime.now(timezone.utc).isoformat()

db_row = {
    "intake_id": intake_id,
    "primary_condition": primary_condition,
    "confidence_suppressed": suppressed,
    "suppression_reason": suppression_reason,
    "raw_scores_json": raw_scores,
    "evidence_breakdown_json": evidence_breakdown,
    "source_summary_json": source_summary,
    "acs_probability": probabilities.get("ACS"),
    "pe_probability": probabilities.get("PE"),
    "pneumonia_probability": probabilities.get("Pneumonia"),
    "arrhythmia_probability": probabilities.get("Arrhythmia"),
    "other_probability": probabilities.get("Other"),
    "created_at": now,
}

insert_res = supabase.table("aggregation_results").insert(db_row).execute()
agg_id = insert_res.data[0].get("id", "") if insert_res.data else ""
print(f"  Inserted aggregation_id: {agg_id}")

# Step 4: Verify DB
print("\n" + "=" * 60)
print("STEP 4: Reading back from DB...")
print("=" * 60)

latest = supabase.table("aggregation_results") \
    .select("primary_condition, evidence_breakdown_json, raw_scores_json, source_summary_json") \
    .eq("intake_id", intake_id) \
    .order("created_at", desc=True) \
    .limit(1) \
    .execute()

row = latest.data[0] if latest.data else {}
eb_db = row.get("evidence_breakdown_json")
print(f"  primary_condition: {row.get('primary_condition')}")
print(f"  evidence_breakdown_json type: {type(eb_db).__name__}")
if eb_db:
    if isinstance(eb_db, str):
        eb_db = json.loads(eb_db)
    for cond, trails in eb_db.items():
        print(f"    {cond}: {trails}")
    print("  DB PERSISTENCE: PASS")
else:
    print("  DB PERSISTENCE: FAIL")

# Step 5: Verify report service
print("\n" + "=" * 60)
print("STEP 5: Verifying report service...")
print("=" * 60)

from app.services.report_service import generate_report
report = generate_report(intake_id)
agg_section = report.get("aggregation", {})
eb_report = agg_section.get("evidence_breakdown", {})

print(f"  aggregation.available: {agg_section.get('available')}")
print(f"  aggregation.primary_condition: {agg_section.get('primary_condition')}")
print(f"  aggregation.evidence_breakdown populated: {bool(eb_report)}")
if eb_report:
    for cond, trails in eb_report.items():
        print(f"    {cond}: {trails}")
    print("\n  REPORT SERVICE: PASS")
    print("\n  >>> evidence_breakdown_json: DB -> Report API -> Frontend <<<")
else:
    print("\n  REPORT SERVICE: FAIL")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
