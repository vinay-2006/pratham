"""Regression tests for GET /api/report/{id}: live status + top-level fields."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api import report as report_api

client = TestClient(app, raise_server_exceptions=False)

CACHED_REPORT = {
    "intake_id": "abc123",
    "case_id": "PRA-1",
    "arrival_type": "ambulance",
    "severity": "high",
    "created_at": "2026-01-01T10:00:00",
    "evidence": [],
}


@pytest.fixture
def stub_services(monkeypatch):
    async def fake_report(intake_id):
        if intake_id == "missing":
            raise ValueError("Intake missing not found")
        return CACHED_REPORT

    class FakeRepo:
        def get_by_id(self, intake_id, columns=None):
            return {"status": "clinical_report_ready"}

    monkeypatch.setattr(report_api, "get_complete_report", fake_report)
    monkeypatch.setattr(
        "app.domains.triage.repository.intake_repository", FakeRepo()
    )
    return monkeypatch


def test_report_includes_live_workflow_status(stub_services):
    stub_services.setattr(
        "app.services.workflow_service.get_workflow_status",
        lambda intake_id, default: "case_closed",
    )
    r = client.get("/api/report/abc123")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "case_closed"  # live status, not cached/stale
    assert body["case_id"] == "PRA-1"
    assert body["arrival_type"] == "ambulance"


def test_report_does_not_mutate_cached_dict(stub_services):
    stub_services.setattr(
        "app.services.workflow_service.get_workflow_status",
        lambda intake_id, default: "case_closed",
    )
    client.get("/api/report/abc123")
    assert "status" not in CACHED_REPORT


def test_report_unknown_intake_is_404(stub_services):
    assert client.get("/api/report/missing").status_code == 404


def test_unhandled_500_includes_cors_headers():
    """Unhandled errors must still be readable cross-origin by the frontend."""
    from app.main import _cors_origins

    @app.get("/__test_unhandled")
    async def _boom():
        raise RuntimeError("db exploded")

    origin = _cors_origins[0]
    r = client.get("/__test_unhandled", headers={"Origin": origin})
    assert r.status_code == 500
    assert r.headers["access-control-allow-origin"] == origin
    assert "db exploded" not in r.text  # no internals leaked


def test_5xx_http_exception_detail_is_sanitized(monkeypatch):
    async def boom(intake_id):
        raise RuntimeError("connection to db.internal.host:5432 refused")

    monkeypatch.setattr(report_api, "get_complete_report", boom)
    r = client.get("/api/report/x")
    assert r.status_code == 500
    assert "db.internal.host" not in r.text


def test_4xx_detail_is_preserved(stub_services):
    r = client.get("/api/report/missing")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"]
