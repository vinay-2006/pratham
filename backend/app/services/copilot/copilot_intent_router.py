"""
PRATHAM Copilot — Intent Router
Classifies queries across 8 Intent Modes in Clinical & System Assistant modes.
"""

from typing import Dict, Any

INTENT_EXPLAIN_CONDITION = "EXPLAIN_CONDITION"
INTENT_COMPARE_CONDITIONS = "COMPARE_CONDITIONS"
INTENT_INVESTIGATION_ASSISTANT = "INVESTIGATION_ASSISTANT"
INTENT_TIMELINE_QA = "TIMELINE_QA"
INTENT_REPORT_SUMMARY = "REPORT_SUMMARY"
INTENT_EXPLAINABILITY_MODE = "EXPLAINABILITY_MODE"
INTENT_KNOWLEDGE_BASE_SEARCH = "KNOWLEDGE_BASE_SEARCH"
INTENT_PIPELINE_EXPLANATION = "PIPELINE_EXPLANATION"


def route_query_intent(query: str, mode: str = "CLINICAL") -> Dict[str, Any]:
    """Classify user query into intent and target entities."""
    q = query.strip().lower()

    # System Assistant Mode routing
    if mode == "SYSTEM" or any(kw in q for kw in ["pipeline", "subsystem", "pending", "failed", "latency", "status", "blocking"]):
        return {
            "intent": INTENT_PIPELINE_EXPLANATION,
            "mode": "SYSTEM",
            "target_entity": None,
        }

    # Clinical Assistant Mode routing
    if "vs" in q or "compare" in q or "versus" in q:
        return {
            "intent": INTENT_COMPARE_CONDITIONS,
            "mode": "CLINICAL",
            "target_entity": q,
        }
    elif any(kw in q for kw in ["why low", "why high", "confidence", "uncertainty", "evidence completeness"]):
        return {
            "intent": INTENT_EXPLAINABILITY_MODE,
            "mode": "CLINICAL",
            "target_entity": None,
        }
    elif any(kw in q for kw in ["summarize", "30 seconds", "summary", "overview"]):
        return {
            "intent": INTENT_REPORT_SUMMARY,
            "mode": "CLINICAL",
            "target_entity": None,
        }
    elif any(kw in q for kw in ["changed", "yesterday", "improved", "worsened", "timeline", "baseline"]):
        return {
            "intent": INTENT_TIMELINE_QA,
            "mode": "CLINICAL",
            "target_entity": None,
        }
    elif any(kw in q for kw in ["why cbc", "why ecg", "why ct", "investigation", "order", "lab"]):
        return {
            "intent": INTENT_INVESTIGATION_ASSISTANT,
            "mode": "CLINICAL",
            "target_entity": q,
        }
    elif any(kw in q for kw in ["rules", "criteria", "yaml", "specification"]):
        return {
            "intent": INTENT_KNOWLEDGE_BASE_SEARCH,
            "mode": "CLINICAL",
            "target_entity": q,
        }
    else:
        # Default to Explain Condition ("Why Pneumonia?", "Why ACS?")
        return {
            "intent": INTENT_EXPLAIN_CONDITION,
            "mode": "CLINICAL",
            "target_entity": q,
        }
