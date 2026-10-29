"""
PRATHAM Clinical Preservation & Safety Verification Suite
Tests all clinical logic layers to ensure zero behavioral regression from performance optimizations.
"""
import sys
import os
import json
import asyncio
from typing import Dict, Any

sys.path.insert(0, r"d:\pratham\backend")

from app.models.workflow import WorkflowStatus, WORKFLOW_PROGRESS_MAP
from app.services.workflow_service import validate_status_transition
from app.services.clinical_reasoning_service import build_clinical_evidence
from app.services.report_service import get_complete_report, _get_cached_report, invalidate_report_cache
from app.domains.workflow.repository import workflow_repository
from app.db.supabase_client import supabase

print("=" * 80)
print("PRATHAM CLINICAL BEHAVIOR PRESERVATION SUITE")
print("=" * 80)

passed = 0
failed = 0

def test(name: str, condition: bool, details: str = ""):
    global passed, failed
    if condition:
        print(f"  [PASS] {name} {details}")
        passed += 1
    else:
        print(f"  [FAIL] {name} - {details}")
        failed += 1

# ── 1. Workflow State Machine Integrity ──────────────────────────────────────
print("\n--- 1. Workflow State Machine Transitions ---")
test("Initial intake submitted -> arrived", validate_status_transition(WorkflowStatus.INTAKE_SUBMITTED.value, WorkflowStatus.ARRIVED.value))
test("Arrived -> awaiting approval", validate_status_transition(WorkflowStatus.ARRIVED.value, WorkflowStatus.AWAITING_APPROVAL.value))
test("Awaiting approval -> approved", validate_status_transition(WorkflowStatus.AWAITING_APPROVAL.value, WorkflowStatus.APPROVED.value))
test("Awaiting approval -> upload pending", validate_status_transition(WorkflowStatus.AWAITING_APPROVAL.value, WorkflowStatus.UPLOAD_PENDING.value))
test("Approved -> upload pending", validate_status_transition(WorkflowStatus.APPROVED.value, WorkflowStatus.UPLOAD_PENDING.value))
test("Upload pending -> analysis running", validate_status_transition(WorkflowStatus.UPLOAD_PENDING.value, WorkflowStatus.ANALYSIS_RUNNING.value))
test("Analysis running -> report ready", validate_status_transition(WorkflowStatus.ANALYSIS_RUNNING.value, WorkflowStatus.REPORT_READY.value))
test("Report ready -> under review", validate_status_transition(WorkflowStatus.REPORT_READY.value, WorkflowStatus.UNDER_REVIEW.value))
test("Under review -> case closed", validate_status_transition(WorkflowStatus.UNDER_REVIEW.value, WorkflowStatus.CLOSED.value))
test("Invalid jump rejected (submitted -> closed)", not validate_status_transition(WorkflowStatus.INTAKE_SUBMITTED.value, WorkflowStatus.CLOSED.value))

# ── 2. Workflow Progress Mapping ─────────────────────────────────────────────
print("\n--- 2. Workflow Progress Percentage Mapping ---")
for st in WorkflowStatus:
    test(f"Progress mapped: {st.value}", st.value in WORKFLOW_PROGRESS_MAP, f"({WORKFLOW_PROGRESS_MAP.get(st.value)}%)")

# ── 3. Workflow Batch Status Derivation Correctness ──────────────────────────
print("\n--- 3. Workflow Batch Resolution Protocol ---")
test("Empty intake list returns empty dict", workflow_repository.get_batch_latest_status([]) == {})
test("Missing/invalid ID list handled safely", isinstance(workflow_repository.get_batch_latest_status(["00000000-0000-0000-0000-000000000000"]), dict))

# ── 4. Clinical Report DTO 17-Section Contract ──────────────────────────────
print("\n--- 4. Report DTO 17-Section Structural Integrity ---")
async def verify_report():
    intakes = supabase.table("emergency_intake").select("id").limit(1).execute()
    if not intakes.data:
        print("  [WARN] No intakes to test report DTO.")
        return
    iid = intakes.data[0]["id"]
    rep = await get_complete_report(iid)
    
    expected_base_sections = [
        "patient_summary", "vitals", "symptoms", "nlp_findings",
        "risk_engine", "investigations", "evidence", "lab_intelligence",
        "imaging_intelligence", "aggregation", "pipeline_status",
        "clinical_interpretation", "clinical_conclusions",
        "clinician_report", "clinical_audit_log", "validation"
    ]
    for sec in expected_base_sections:
        test(f"Base Report section present: {sec}", sec in rep)

    clinician_rep = rep.get("clinician_report", {})
    expected_clinician_sections = [
        "patient_snapshot", "timeline", "presenting_complaint",
        "hpi", "vitals_list", "investigations_matrix",
        "clinical_findings", "differential_diagnosis",
        "recommendations", "evidence_quality"
    ]
    for sec in expected_clinician_sections:
        test(f"Clinician Report sub-section present: {sec}", sec in clinician_rep)

asyncio.run(verify_report())

print("\n" + "=" * 80)
print(f"VERIFICATION SUMMARY: {passed} PASSED, {failed} FAILED")
print("=" * 80)
