"""Copilot: role-scoped context + LLM orchestration (LLM and DB are stubbed)."""
import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.copilot import case_context, copilot_orchestrator as orch
from app.services.copilot.llm_client import LLMUnavailable
from app.services.copilot.session_memory import clear_sessions, recent_turns
from tests.conftest import make_user

client = TestClient(app, raise_server_exceptions=False, headers={"Authorization": "Bearer t"})

INTAKE = {"id": "11111111-1111-1111-1111-111111111111", "case_id": "PRA-1", "patient_id": "p1",
          "chief_complaint": "Chest pain", "severity_level": "critical", "status": "arrived"}


@pytest.fixture(autouse=True)
def _clean():
    clear_sessions()


@pytest.fixture
def stub_db(monkeypatch):
    monkeypatch.setattr(case_context, "resolve_intake", lambda ref: INTAKE if ref else None)
    monkeypatch.setattr(case_context, "_build_triage", lambda i: {"case_id": "PRA-1", "vitals": {"spo2": 88}, "workflow_history": []})
    monkeypatch.setattr(case_context, "_build_clinical", lambda i: {"case_id": "PRA-1", "vitals": {"spo2": 88},
                                                                    "differential": {"primary_condition": "ACS"}, "workflow_history": []})
    monkeypatch.setattr(case_context, "_build_admin_overview", lambda: {"total_intakes": 5, "intakes_by_status": {}})


def fake_llm(captured):
    def _chat(messages, **kw):
        captured.append(messages)
        return {"answer": "ok", "confidence": "HIGH", "supporting": ["SpO2 88"], "conflicting": [], "missing": [],
                "sources": ["vitals"], "reasoning_steps": ["a"], "suggested_questions": ["q"], "_model": "m"}
    return _chat


def test_nurse_context_excludes_diagnostic_data(stub_db):
    ctx = case_context.build_case_context("nurse", INTAKE["id"])
    assert ctx["scope"] == "nurse_triage"
    assert "differential" not in json.dumps(ctx["data"])


def test_doctor_context_includes_differential(stub_db):
    ctx = case_context.build_case_context("doctor", INTAKE["id"])
    assert ctx["scope"] == "doctor_full" and ctx["data"]["differential"]["primary_condition"] == "ACS"


def test_admin_never_gets_patient_data_even_with_intake_id(stub_db):
    ctx = case_context.build_case_context("admin", INTAKE["id"])
    assert ctx["scope"] == "admin_aggregate"
    assert "PRA-1" not in json.dumps(ctx["data"])


def test_prompt_contains_only_scoped_data(stub_db, monkeypatch):
    seen = []
    monkeypatch.setattr(orch, "chat_json", fake_llm(seen))
    orch.run_copilot_query("diagnosis?", make_user("nurse"), "s", INTAKE["id"])
    system = seen[0][0]["content"]
    assert "TRIAGE NURSE" in system and "primary_condition" not in system
    seen.clear()
    orch.run_copilot_query("diagnosis?", make_user("doctor"), "s2", INTAKE["id"])
    assert "primary_condition" in seen[0][0]["content"]


def test_response_shape_for_ui(stub_db, monkeypatch):
    monkeypatch.setattr(orch, "chat_json", fake_llm([]))
    r = orch.run_copilot_query("hi", make_user("doctor"), "s", INTAKE["id"])
    for key in ("answer", "answer_confidence", "sources", "citations", "suggested_questions",
                "show_your_work", "evidence_card", "safety", "context_stats"):
        assert key in r
    assert r["safety"]["llm_used"] is True


def test_llm_outage_degrades_to_data_only(stub_db, monkeypatch):
    def down(*a, **k):
        raise LLMUnavailable("down")
    monkeypatch.setattr(orch, "chat_json", down)
    r = orch.run_copilot_query("hi", make_user("nurse"), "s", INTAKE["id"])
    assert r["safety"]["llm_used"] is False and r["answer_confidence"] == "LOW"


def test_sessions_are_isolated_per_user(stub_db, monkeypatch):
    monkeypatch.setattr(orch, "chat_json", fake_llm([]))
    orch.run_copilot_query("secret question", make_user("doctor"), "shared", INTAKE["id"])
    assert recent_turns("test-doctor", "shared")
    assert recent_turns("test-nurse", "shared") == []


def test_followup_history_is_sent_to_llm(stub_db, monkeypatch):
    seen = []
    monkeypatch.setattr(orch, "chat_json", fake_llm(seen))
    u = make_user("doctor")
    orch.run_copilot_query("first", u, "s", INTAKE["id"])
    orch.run_copilot_query("and why?", u, "s", INTAKE["id"])
    roles = [m["role"] for m in seen[1]]
    assert roles == ["system", "user", "assistant", "user"]


def test_endpoint_rejects_empty_query():
    assert client.post("/api/copilot/query", json={"query": "   "}).status_code == 400


def test_endpoint_returns_answer(stub_db, monkeypatch):
    monkeypatch.setattr(orch, "chat_json", fake_llm([]))
    r = client.post("/api/copilot/query", json={"query": "hi", "intake_id": INTAKE["id"]})
    assert r.status_code == 200 and r.json()["answer"] == "ok"
