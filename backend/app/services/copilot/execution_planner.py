"""
PRATHAM Copilot — Execution Planner
Decides data retrieval needs and whether deterministic execution is sufficient or LLM synthesis is required.
"""

from typing import Dict, Any
from app.services.copilot.copilot_intent_router import (
    INTENT_EXPLAIN_CONDITION,
    INTENT_COMPARE_CONDITIONS,
    INTENT_INVESTIGATION_ASSISTANT,
    INTENT_TIMELINE_QA,
    INTENT_REPORT_SUMMARY,
    INTENT_EXPLAINABILITY_MODE,
    INTENT_KNOWLEDGE_BASE_SEARCH,
    INTENT_PIPELINE_EXPLANATION,
)


def plan_copilot_execution(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Plan required contexts and LLM invocation strategy."""
    intent = intent_data.get("intent", INTENT_EXPLAIN_CONDITION)

    # Deterministic intents do NOT require LLM call
    is_deterministic = intent in [
        INTENT_EXPLAINABILITY_MODE,
        INTENT_KNOWLEDGE_BASE_SEARCH,
        INTENT_PIPELINE_EXPLANATION,
    ]

    return {
        "intent": intent,
        "needs_llm": not is_deterministic,
        "needs_patient_context": True,
        "needs_clinical_findings": intent in [INTENT_EXPLAIN_CONDITION, INTENT_COMPARE_CONDITIONS, INTENT_INVESTIGATION_ASSISTANT, INTENT_REPORT_SUMMARY, INTENT_EXPLAINABILITY_MODE],
        "needs_reasoning_context": intent in [INTENT_EXPLAIN_CONDITION, INTENT_COMPARE_CONDITIONS, INTENT_REPORT_SUMMARY, INTENT_EXPLAINABILITY_MODE],
        "needs_knowledge_context": intent in [INTENT_EXPLAIN_CONDITION, INTENT_COMPARE_CONDITIONS, INTENT_KNOWLEDGE_BASE_SEARCH],
        "needs_timeline_context": intent in [INTENT_TIMELINE_QA, INTENT_COMPARE_CONDITIONS, INTENT_REPORT_SUMMARY],
        "needs_workflow_context": intent == INTENT_PIPELINE_EXPLANATION,
    }
