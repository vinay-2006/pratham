"""
Quick verification: Does the report endpoint return non-empty evidence_breakdown
for patients that have aggregation results?
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.supabase_client import supabase

print("=" * 70)
print("VERIFICATION: evidence_breakdown_json in report pipeline")
print("=" * 70)

# 1. Find all intakes with aggregation results
agg_res = supabase.table("aggregation_results").select(
    "intake_id, primary_condition, evidence_breakdown_json, source_summary_json"
).execute()

if not agg_res.data:
    print("\n❌ No aggregation_results rows found. Run aggregation first.")
    sys.exit(1)

print(f"\nFound {len(agg_res.data)} aggregation result(s)\n")

for row in agg_res.data:
    iid = row["intake_id"]
    eb = row.get("evidence_breakdown_json")
    primary = row.get("primary_condition")
    
    print(f"  Intake: {iid}")
    print(f"  Primary Condition: {primary}")
    print(f"  evidence_breakdown_json type: {type(eb).__name__}")
    
    if eb:
        if isinstance(eb, str):
            import json
            eb = json.loads(eb)
        
        print(f"  Conditions in breakdown: {list(eb.keys())}")
        for condition, trails in eb.items():
            trail_list = trails if isinstance(trails, list) else []
            print(f"    {condition}: {trail_list}")
    else:
        print(f"  ⚠ evidence_breakdown_json is empty or NULL")
    print()

# 2. Now test through the report service
print("-" * 70)
print("Testing report_service.generate_report()...")
print("-" * 70)

from app.services.report_service import generate_report

for row in agg_res.data[:2]:  # test up to 2
    iid = row["intake_id"]
    print(f"\n  Generating report for intake: {iid}")
    try:
        report = generate_report(iid)
        agg_section = report.get("aggregation", {})
        eb_in_report = agg_section.get("evidence_breakdown", {})
        
        print(f"  aggregation.available: {agg_section.get('available')}")
        print(f"  aggregation.primary_condition: {agg_section.get('primary_condition')}")
        print(f"  aggregation.evidence_breakdown keys: {list(eb_in_report.keys())}")
        
        if eb_in_report:
            for cond, items in eb_in_report.items():
                print(f"    {cond}: {items}")
            print(f"\n  ✅ evidence_breakdown is present in report API response")
        else:
            print(f"\n  ⚠ evidence_breakdown is EMPTY in report API response")
    except Exception as e:
        print(f"  ❌ Error generating report: {e}")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
