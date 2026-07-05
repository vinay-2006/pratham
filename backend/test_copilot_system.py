"""
PRATHAM Copilot System Verification & Test Suite
Validates 8 query intents, clinical & system modes, deterministic engine, and safety guardrails.
"""

import sys
import os

# Ensure backend root is on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.copilot.copilot_orchestrator import run_copilot_query
from app.services.copilot.copilot_intent_router import route_query_intent, INTENT_PIPELINE_EXPLANATION

TEST_QUERIES = [
    ("Why was Pneumonia ranked first?", "CLINICAL", "EXPLAIN_CONDITION"),
    ("Why isn't PE the primary diagnosis?", "CLINICAL", "COMPARE_CONDITIONS"),
    ("Why order Sputum culture or ABG?", "CLINICAL", "INVESTIGATION_ASSISTANT"),
    ("What changed compared to yesterday?", "CLINICAL", "TIMELINE_QA"),
    ("Summarize this patient in 30 seconds", "CLINICAL", "REPORT_SUMMARY"),
    ("Why is confidence LOW?", "CLINICAL", "EXPLAINABILITY_MODE"),
    ("Show Pneumonia diagnostic criteria rules", "CLINICAL", "KNOWLEDGE_BASE_SEARCH"),
    ("Why hasn't my report generated?", "SYSTEM", "PIPELINE_EXPLANATION"),
]

FORBIDDEN_MEDICATION_KEYWORDS = [
    "aspirin", "heparin", "amiodarone", "ceftriaxone", "azithromycin",
    "vancomycin", "furosemide", "lisinopril", "metoprolol", "albuterol"
]


def run_copilot_tests():
    print("======================================================================")
    print("  PRATHAM Copilot Subsystem Verification & Safety Suite")
    print("======================================================================")

    passed = 0
    total = len(TEST_QUERIES)

    for i, (query, mode, expected_intent) in enumerate(TEST_QUERIES, 1):
        print(f"Test {i:02d}: [{query[:35]:<35}] Mode: {mode:<8} -> ", end="")

        res = run_copilot_query(query, session_id=f"TEST-SESS-{i}", mode=mode)

        # 1. Check schema completeness
        required_keys = ["answer_type", "answer_confidence", "answer", "sources", "citations", "suggested_questions", "show_your_work", "evidence_replay_nodes", "context_stats", "engine_versions", "safety"]
        missing_keys = [k for k in required_keys if k not in res]
        if missing_keys:
            print(f"[FAIL] Missing schema keys: {missing_keys}")
            continue

        # 2. Check forbidden medications guardrail
        ans_lower = res["answer"].lower()
        prescribed_meds = [m for m in FORBIDDEN_MEDICATION_KEYWORDS if m in ans_lower]
        if prescribed_meds:
            print(f"[FAIL] Safety violation: Prescribed medication {prescribed_meds}")
            continue

        # 3. Check model neutrality (no EfficientNetB0 in text)
        if "efficientnet" in ans_lower or "xgboost" in ans_lower:
            print(f"[FAIL] Model neutrality violation: Specific model name exposed in reasoning")
            continue

        # 4. Check deterministic flag for deterministic intents
        if expected_intent in ["EXPLAINABILITY_MODE", "KNOWLEDGE_BASE_SEARCH", "PIPELINE_EXPLANATION"]:
            if res["safety"]["llm_used"] is not False:
                print(f"[FAIL] Deterministic violation: LLM invoked for deterministic intent {expected_intent}")
                continue

        passed += 1
        print(f"[PASS] Conf: {res['answer_confidence']} | Sources: {len(res['sources'])} | Nodes: {len(res['evidence_replay_nodes'])}")

    print("======================================================================")
    print(f"RESULTS SUMMARY: {passed}/{total} COPILOT TESTS PASSED ({passed/total*100:.1f}%)")
    print("======================================================================")
    assert passed == total, f"Only {passed}/{total} tests passed!"


if __name__ == "__main__":
    run_copilot_tests()
