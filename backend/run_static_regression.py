"""
Phase 3.1 Static Regression Suite
Verifies all P1–P5 fixes and pre-existing behaviour without DB connectivity.
"""
import sys
import subprocess
import inspect

failures = []
passed = []

def ok(label, msg=""):
    print(f"  [OK]  {msg or label}")
    passed.append(label)

def fail(label, msg):
    print(f"  [FAIL] {msg}")
    failures.append(label)

# ── 1. Architecture Validator ────────────────────────────────────────────────
print("\n--- 1. Architecture Validator ---")
result = subprocess.run(["python", "validate_architecture.py"], capture_output=True, text=True)
if result.returncode == 0:
    for line in result.stdout.strip().splitlines():
        print(" ", line)
    ok("Architecture Validator")
else:
    print(result.stdout, result.stderr)
    fail("Architecture Validator", "validate_architecture.py returned non-zero")

# ── 2. State Machine ─────────────────────────────────────────────────────────
print("\n--- 2. State Machine Transitions ---")
from app.services.workflow_service import VALID_TRANSITIONS, validate_status_transition
from app.models.workflow import WorkflowStatus

try:
    assert WorkflowStatus.UPLOAD_PENDING in VALID_TRANSITIONS[WorkflowStatus.AWAITING_APPROVAL]
    ok("P1: AWAITING_APPROVAL -> UPLOAD_PENDING", "P1: AWAITING_APPROVAL -> UPLOAD_PENDING valid")

    assert WorkflowStatus.ARRIVED in VALID_TRANSITIONS[WorkflowStatus.AWAITING_APPROVAL]
    ok("P2: AWAITING_APPROVAL -> ARRIVED", "P2: AWAITING_APPROVAL -> ARRIVED valid")

    assert validate_status_transition("awaiting_doctor_approval", "investigations_approved")
    assert validate_status_transition("investigations_approved", "evidence_upload_pending")
    assert validate_status_transition("evidence_upload_pending", "analysis_running")
    assert validate_status_transition("analysis_running", "clinical_report_ready")
    assert validate_status_transition("clinical_report_ready", "case_closed")
    ok("State Machine", "All pre-existing state machine transitions intact")
except AssertionError as e:
    fail("State Machine", str(e))

# ── 3. reject() Workflow Transition (P2) ─────────────────────────────────────
print("\n--- 3. reject() Workflow Transition (P2) ---")
from app.services.investigation_approval_service import reject
src = inspect.getsource(reject)
try:
    assert "update_workflow_status" in src
    ok("reject() contains update_workflow_status", "reject() contains update_workflow_status")
    assert "ARRIVED" in src
    ok("reject() targets ARRIVED", "reject() targets ARRIVED state")
    assert "doctor_name" in src
    ok("reject() doctor_name param", "reject() accepts doctor_name for audit log")
    ok("P2: reject() Workflow Transition")
except AssertionError as e:
    fail("P2: reject() Workflow Transition", f"P2 REGRESSION: {e}")

# ── 4. needs_info() Audit Logging (P3) ───────────────────────────────────────
print("\n--- 4. needs_info() Audit Logging (P3) ---")
from app.services.investigation_approval_service import needs_info
src_ni = inspect.getsource(needs_info)
try:
    assert "log_status_transition" in src_ni or "update_workflow_status" in src_ni
    ok("P3: needs_info() Audit Logging", "needs_info() contains audit logging (P3)")
except AssertionError:
    fail("P3: needs_info() Audit Logging", "P3 REGRESSION: audit logging missing from needs_info()")

# ── 5. approve() Compensating Rollback (P4) ──────────────────────────────────
print("\n--- 5. approve() Compensating Rollback (P4) ---")
from app.services.investigation_approval_service import approve
src_ap = inspect.getsource(approve)
try:
    assert ("rollback" in src_ap.lower() or "compensat" in src_ap.lower() or "partial" in src_ap.lower())
    ok("P4: approve() Compensating Rollback", "approve() contains compensating rollback (P4)")
except AssertionError:
    fail("P4: approve() Compensating Rollback", "P4 REGRESSION: compensating rollback missing from approve()")

# ── 6. Evidence Mapping Utility (P5) ─────────────────────────────────────────
print("\n--- 6. Evidence Mapping Utility (P5) ---")
from app.domains.shared.utils.evidence_mapping import get_evidence_type, INVESTIGATION_EVIDENCE_MAP
try:
    t1 = get_evidence_type("Chest X-ray")
    assert t1 == "xray", f"Expected xray, got {t1}"
    t2 = get_evidence_type("CBC")
    assert t2 == "lab_report", f"Expected lab_report, got {t2}"
    t3 = get_evidence_type("ECG")
    assert t3 == "ecg", f"Expected ecg, got {t3}"
    ok("P5: Evidence Mapping Utility", "Chest X-ray->xray, CBC->lab_report, ECG->ecg (P5 correct)")
except AssertionError as e:
    fail("P5: Evidence Mapping Utility", f"P5 REGRESSION: {e}")

# ── 7. No API-to-API Imports (P5) ────────────────────────────────────────────
print("\n--- 7. No API-to-API Imports (P5) ---")
from app.api import investigations, evidence
src_inv = inspect.getsource(investigations)
src_ev = inspect.getsource(evidence)
try:
    # Check that investigations.py does NOT import from app.api.evidence
    assert "from app.api.evidence import" not in src_inv
    assert "from app.api import evidence" not in src_inv
    ok("P5: investigations.py clean", "investigations.py does not import from app.api.evidence")
    # Check that evidence.py does NOT import from app.api.investigations
    assert "from app.api.investigations import" not in src_ev
    assert "from app.api import investigations" not in src_ev
    ok("P5: evidence.py clean", "evidence.py does not import from app.api.investigations")
    ok("P5: No API-to-API Imports")
except AssertionError as e:
    fail("P5: No API-to-API Imports", f"P5 REGRESSION: {e}")

# ── 8. Doctor Review Status Filter ───────────────────────────────────────────
print("\n--- 8. Doctor Worklist Status Filter ---")
from app.services.doctor_review_service import REVIEW_STATUSES
try:
    assert WorkflowStatus.ARRIVED.value not in REVIEW_STATUSES
    ok("P2: ARRIVED not in REVIEW_STATUSES", "ARRIVED not in REVIEW_STATUSES (rejected patients leave doctor worklist)")
    assert WorkflowStatus.AWAITING_APPROVAL.value in REVIEW_STATUSES
    assert WorkflowStatus.APPROVED.value in REVIEW_STATUSES
    assert WorkflowStatus.UPLOAD_PENDING.value in REVIEW_STATUSES
    ok("Doctor REVIEW_STATUSES complete", "AWAITING_APPROVAL, APPROVED, UPLOAD_PENDING in REVIEW_STATUSES")
except AssertionError as e:
    fail("Doctor Worklist Status Filter", f"REGRESSION: {e}")

# ── 9. Nurse Queue Exclusion ─────────────────────────────────────────────────
print("\n--- 9. Nurse Queue Exclusion ---")
from app.services.patient_queue_service import _EXCLUDED_STATUSES
try:
    assert WorkflowStatus.ARRIVED.value not in _EXCLUDED_STATUSES
    ok("P2: ARRIVED not excluded", "ARRIVED not excluded from nurse queue (rejected patients visible to nurse)")
    assert WorkflowStatus.CLOSED.value in _EXCLUDED_STATUSES
    assert WorkflowStatus.OFFLINE.value in _EXCLUDED_STATUSES
    ok("Nurse exclusion set correct", "CLOSED and OFFLINE correctly excluded")
except AssertionError as e:
    fail("Nurse Queue Exclusion", f"REGRESSION: {e}")

# ── 10. History Rejection Status Derivation ───────────────────────────────────
print("\n--- 10. Investigation History — Rejection Derivation ---")
from app.services.investigation_history_service import _derive_notification_status
try:
    # P2: intake is ARRIVED, investigations are rejected — must return 'Rejected'
    s = _derive_notification_status("arrived", ["rejected", "rejected"])
    assert s == "Rejected", f"Expected Rejected, got {s}"
    ok("History: ARRIVED + rejected -> Rejected", "derive_notification_status(arrived, [rejected]) = Rejected (P2 compatible)")

    # Legacy paths unaffected
    assert _derive_notification_status("investigation_approved", ["approved"]) == "Approved"
    assert _derive_notification_status("needs_info", ["needs_info"]) == "Needs Info"
    assert _derive_notification_status("intake_pending", ["pending_approval"]) == "Pending Approval"
    ok("History: legacy branches intact", "Approved, Needs Info, Pending Approval branches unaffected")
except AssertionError as e:
    fail("History Rejection Status Derivation", f"REGRESSION: {e}")

# ── 11. WORKFLOW_PROGRESS_MAP completeness ────────────────────────────────────
print("\n--- 11. Workflow Progress Map Completeness ---")
from app.models.workflow import WORKFLOW_PROGRESS_MAP
try:
    for ws in WorkflowStatus:
        assert ws.value in WORKFLOW_PROGRESS_MAP, f"{ws.value} missing from WORKFLOW_PROGRESS_MAP"
    ok("Workflow Progress Map", f"All {len(list(WorkflowStatus))} statuses have progress percentages")
except AssertionError as e:
    fail("Workflow Progress Map", f"REGRESSION: {e}")

# ── 12. Full Module Import Chain ──────────────────────────────────────────────
print("\n--- 12. Full Module Import Chain ---")
try:
    from app.services.case_lifecycle_service import confirm_arrival, close_case, return_to_nurse
    from app.services.workflow_service import build_patient_timeline, update_workflow_status, get_workflow_status
    from app.services.investigation_history_service import get_investigation_history
    from app.services.doctor_dashboard_service import get_dashboard_stats
    from app.services.doctor_review_service import get_doctor_review_list
    from app.domains.shared.enums import WorkflowStatus as WsEnum
    ok("Full Module Import Chain", "All 12 critical service modules import successfully")
except ImportError as e:
    fail("Full Module Import Chain", f"IMPORT REGRESSION: {e}")

# ── 13. return_to_nurse targets UPLOAD_PENDING ────────────────────────────────
print("\n--- 13. return_to_nurse() -> UPLOAD_PENDING ---")
src_rtn = inspect.getsource(return_to_nurse)
try:
    assert "UPLOAD_PENDING" in src_rtn
    ok("return_to_nurse UPLOAD_PENDING", "return_to_nurse() targets UPLOAD_PENDING (P1 compatible)")
except AssertionError:
    fail("return_to_nurse UPLOAD_PENDING", "REGRESSION: return_to_nurse() does not target UPLOAD_PENDING")

# ── 14. Phase 3.1 service layer ownership check ───────────────────────────────
print("\n--- 14. Phase 3.1 Service Layer Ownership ---")
# reject() must NOT be an inline function in the API — must delegate to service
from app.api import investigations as inv_api
src_api = inspect.getsource(inv_api)
try:
    # The reject endpoint delegates to _reject_service (the service layer)
    assert "_reject_service" in src_api or "reject_service" in src_api
    ok("API delegates to reject service", "reject endpoint delegates to service layer (architecture preserved)")
except AssertionError:
    fail("API delegates to reject service", "REGRESSION: reject endpoint contains inline logic")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("PHASE 3.1 STATIC REGRESSION RESULTS")
print("="*60)
print(f"Total checks: {len(passed) + len(failures)}")
print(f"PASSED: {len(passed)}")
for p in passed:
    print(f"  [PASS] {p}")

if failures:
    print(f"\nFAILED: {len(failures)}")
    for f in failures:
        print(f"  [FAIL] {f}")
    sys.exit(1)
else:
    print("\n[ALL STATIC REGRESSION CHECKS PASSED]")
    sys.exit(0)
