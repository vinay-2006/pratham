"""Role-based access control: who may call what."""
import pytest
from fastapi.testclient import TestClient

from app.core import auth as auth_mod
from app.core.auth import allowed_roles_for
from app.main import app
from tests.conftest import make_user

client = TestClient(app, raise_server_exceptions=False)


def as_role(monkeypatch, role):
    user = make_user(role)
    monkeypatch.setattr(auth_mod, "resolve_token", lambda token: user)
    return {"Authorization": "Bearer x"}


@pytest.mark.real_auth
def test_missing_token_is_401():
    assert client.get("/api/investigations/pending").status_code == 401
    assert client.post("/api/copilot/query", json={"query": "hi"}).status_code == 401


@pytest.mark.real_auth
def test_garbage_token_is_401(monkeypatch):
    from fastapi import HTTPException

    def boom(token):
        raise HTTPException(status_code=401, detail="bad")

    monkeypatch.setattr(auth_mod, "resolve_token", boom)
    assert client.get("/api/investigations/pending", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_health_and_login_are_public():
    assert client.get("/health").status_code == 200


@pytest.mark.parametrize(
    "method,path,allowed,denied",
    [
        ("POST", "/api/investigations/approve", ["doctor"], ["nurse", "admin"]),
        ("POST", "/api/investigations/reject", ["doctor"], ["nurse", "admin"]),
        ("GET", "/api/admin/metrics", ["admin"], ["nurse", "doctor"]),
        ("GET", "/api/doctor/dashboard/stats", ["doctor"], ["nurse", "admin"]),
        ("GET", "/api/report/abc", ["doctor"], ["nurse", "admin"]),
        ("GET", "/api/explainability/tree/abc", ["doctor"], ["nurse", "admin"]),
        ("GET", "/api/aggregate/abc", ["doctor"], ["nurse", "admin"]),
        ("GET", "/api/investigations/patient/abc", ["nurse", "doctor"], ["admin"]),
        ("GET", "/api/intake/registry", ["nurse", "doctor"], ["admin"]),
        ("GET", "/api/search", ["nurse", "doctor"], ["admin"]),
        ("GET", "/api/platform-metrics/telemetry", ["admin", "doctor"], ["nurse"]),
        ("POST", "/api/intake/arrival/confirm", ["nurse"], ["doctor", "admin"]),
        ("POST", "/api/copilot/query", ["nurse", "doctor", "admin"], []),
    ],
)
def test_access_matrix(method, path, allowed, denied):
    roles = allowed_roles_for(method, path)
    assert roles is not None
    for r in allowed:
        assert r in roles, f"{r} should reach {method} {path}"
    for r in denied:
        assert r not in roles, f"{r} must NOT reach {method} {path}"


@pytest.mark.real_auth
@pytest.mark.parametrize("role,status", [("nurse", 403), ("admin", 403)])
def test_non_doctor_cannot_approve(monkeypatch, role, status):
    h = as_role(monkeypatch, role)
    r = client.post("/api/investigations/approve", headers=h, json={})
    assert r.status_code == status


@pytest.mark.real_auth
def test_nurse_and_doctor_cannot_read_admin_metrics(monkeypatch):
    for role in ("nurse", "doctor"):
        h = as_role(monkeypatch, role)
        assert client.get("/api/admin/metrics", headers=h).status_code == 403


@pytest.mark.real_auth
def test_user_without_role_is_rejected(monkeypatch):
    from types import SimpleNamespace

    from app.db import supabase_client

    fake = SimpleNamespace(user=SimpleNamespace(id="u", email="x@y", app_metadata={}, user_metadata={}))
    monkeypatch.setattr(supabase_client.supabase.auth, "get_user", lambda t: fake)
    auth_mod.clear_token_cache()
    assert client.get("/api/investigations/pending", headers={"Authorization": "Bearer r"}).status_code == 403
    auth_mod.clear_token_cache()
