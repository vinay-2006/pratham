"""
PRATHAM Copilot Orchestrator Engine
Orchestrates intent classification, context retrieval, execution planning, tool invocation, and session recording.
"""

from typing import Dict, Any
from app.services.copilot.copilot_intent_router import route_query_intent
from app.services.copilot.execution_planner import plan_copilot_execution
from app.services.copilot.session_memory import get_or_create_session, update_session_history
from app.services.copilot.tool_registry import TOOL_REGISTRY
from app.services.copilot.patient_context import build_patient_context
from app.services.copilot.clinical_findings import build_clinical_findings
from app.services.copilot.reasoning_context import build_reasoning_context
from app.services.copilot.knowledge_context import build_knowledge_context
from app.services.copilot.timeline_context import build_timeline_context
from app.services.copilot.workflow_context import build_workflow_context


def run_copilot_query(
    query: str,
    session_id: str = "SESSION-DEMO",
    intake_id: str = "INT-100",
    mode: str = "CLINICAL",
    patient_data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Execute end-to-end Copilot query through 4-tier pipeline."""
    if patient_data is None:
        patient_data = {
            "patient_id": "P-100",
            "intake_id": intake_id,
            "chief_complaint": "Severe dyspnea and fever",
            "vitals": {"hr": 114, "bp": "102/65", "spo2": 91, "rr": 24, "temp": 38.4},
            "labs": {"wbc": 14.2, "troponin": 0.01, "creatinine": 0.9, "d_dimer": 0.22},
            "imaging": {"finding": "Right Lower Lobe Infiltrate", "confidence": 0.88},
            "top_condition": "Community-Acquired Pneumonia",
            "confidence": "HIGH",
        }

    # 1. Router & Session
    session = get_or_create_session(session_id, intake_id)
    intent_data = route_query_intent(query, mode=mode)

    # 2. Execution Planner
    plan = plan_copilot_execution(intent_data)

    # 3. Context Retrieval
    contexts = {}
    if plan["needs_patient_context"]:
        contexts["patient"] = build_patient_context(patient_data)
    if plan["needs_clinical_findings"]:
        contexts["findings"] = build_clinical_findings(patient_data)
    if plan["needs_reasoning_context"]:
        contexts["reasoning"] = build_reasoning_context(patient_data)
    if plan["needs_knowledge_context"]:
        contexts["knowledge"] = build_knowledge_context(intent_data.get("target_entity") or "pneumonia")
    if plan["needs_timeline_context"]:
        contexts["timeline"] = build_timeline_context(patient_data.get("patient_id", "P-100"))
    if plan["needs_workflow_context"]:
        contexts["workflow"] = build_workflow_context(intake_id)

    # 4. Tool Registry Invocation
    intent_key = intent_data["intent"]
    handler = TOOL_REGISTRY.get(intent_key, TOOL_REGISTRY["EXPLAIN_CONDITION"])
    response_obj = handler(contexts, query)

    # 5. Record Session Memory & return
    update_session_history(session_id, query, response_obj)

    return response_obj
