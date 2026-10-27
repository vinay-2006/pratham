"""
PRATHAM Database Integrity Verification Tool
============================================================
Checks all tables for duplicates, orphaned records, missing references,
invalid workflow states, and other relational integrity issues.
"""
import sys
from dotenv import load_dotenv

# Load env variables
load_dotenv()

try:
    from app.db.supabase_client import supabase
    from app.models.workflow import WorkflowStatus
except Exception as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def run_checks():
    print("=" * 60)
    print("  PRATHAM Database Integrity Verification")
    print("=" * 60)
    
    errors = 0
    warnings = 0
    
    # ── 1. Duplicate Case IDs in emergency_intake ──────────────────────────────
    print("\n[Check 1] Duplicate Case IDs...")
    res = supabase.table("emergency_intake").select("id, case_id").execute()
    cases = res.data or []
    case_map = {}
    duplicates = []
    for c in cases:
        cid = c.get("case_id")
        if cid:
            if cid in case_map:
                duplicates.append(cid)
            else:
                case_map[cid] = c["id"]
    if duplicates:
        print(f"  [FAIL] Duplicate case_ids found: {list(set(duplicates))}")
        errors += len(duplicates)
    else:
        print("  [PASS] All case_ids are unique.")

    # ── 2. Orphaned Recommendations ──────────────────────────────────────────
    print("\n[Check 2] Orphaned Investigation Recommendations...")
    res = supabase.table("investigation_recommendations").select("id, intake_id").execute()
    recs = res.data or []
    intake_ids = {c["id"] for c in cases}
    orphans = []
    for r in recs:
        iid = r.get("intake_id")
        if iid not in intake_ids:
            orphans.append(r["id"])
    if orphans:
        print(f"  [FAIL] {len(orphans)} orphaned investigation recommendations found (no matching intake).")
        errors += len(orphans)
    else:
        print("  [PASS] No orphaned investigation recommendations.")

    # ── 3. Orphaned Evidence ──────────────────────────────────────────────────
    print("\n[Check 3] Orphaned Evidence records...")
    res = supabase.table("evidence").select("id, intake_id").execute()
    ev_list = res.data or []
    orphans_ev = []
    for ev in ev_list:
        iid = ev.get("intake_id")
        if iid not in intake_ids:
            orphans_ev.append(ev["id"])
    if orphans_ev:
        print(f"  [FAIL] {len(orphans_ev)} orphaned evidence records found.")
        errors += len(orphans_ev)
    else:
        print("  [PASS] No orphaned evidence records.")

    # ── 4. Orphaned Workflow Logs ─────────────────────────────────────────────
    print("\n[Check 4] Orphaned Workflow Logs...")
    res = supabase.table("workflow_logs").select("id, intake_id").execute()
    logs = res.data or []
    orphans_logs = []
    for l in logs:
        iid = l.get("intake_id")
        if iid not in intake_ids:
            orphans_logs.append(l["id"])
    if orphans_logs:
        print(f"  [FAIL] {len(orphans_logs)} orphaned workflow logs found.")
        errors += len(orphans_logs)
    else:
        print("  [PASS] No orphaned workflow logs.")

    # ── 5. Invalid Workflow States ────────────────────────────────────────────
    print("\n[Check 5] Invalid Workflow States...")
    valid_states = {
        "intake_pending",
        "investigation_approved",
        "evidence_upload_pending",
        "clinical_report_ready",
        "case_closed",
        "offline_care",
        None
    }
    invalid_cases = []
    for c in cases:
        status = c.get("status")
        if status not in valid_states:
            invalid_cases.append((c["id"], status))
    if invalid_cases:
        print(f"  [FAIL] {len(invalid_cases)} cases have invalid workflow status: {invalid_cases}")
        errors += len(invalid_cases)
    else:
        print("  [PASS] All cases have valid workflow status.")

    # ── 6. Missing Workflow Logs ─────────────────────────────────────────────
    print("\n[Check 6] Missing Workflow Logs...")
    cases_with_logs = {l.get("intake_id") for l in logs}
    missing_logs = []
    for c in cases:
        if c["id"] not in cases_with_logs:
            missing_logs.append(c["id"])
    if missing_logs:
        print(f"  [WARN] {len(missing_logs)} cases have zero workflow log history records.")
        warnings += len(missing_logs)
    else:
        print("  [PASS] All cases have at least one workflow log record.")

    print("\n" + "=" * 60)
    print(f"  Integrity Check Complete: {errors} Errors, {warnings} Warnings")
    print("=" * 60)
    
    if errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_checks()
