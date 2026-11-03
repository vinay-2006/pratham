"""Shared test setup. Tests run as a signed-in doctor unless they opt out with @pytest.mark.real_auth."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core import auth as auth_mod  # noqa: E402
from app.core.auth import AuthUser  # noqa: E402
from app.main import app  # noqa: E402


def make_user(role: str) -> AuthUser:
    return AuthUser(id=f"test-{role}", email=f"{role}@test.local", role=role, name=f"Test {role}", department="Test")


def pytest_configure(config):
    config.addinivalue_line("markers", "real_auth: do not stub authentication for this test")


@pytest.fixture(autouse=True)
def _stub_auth(request, monkeypatch):
    if request.node.get_closest_marker("real_auth"):
        yield
        return
    user = make_user("doctor")
    monkeypatch.setattr(auth_mod, "resolve_token", lambda token: user)
    yield


@pytest.fixture
def auth_header():
    """Header factory; with _stub_auth active any bearer value resolves to the doctor."""
    return {"Authorization": "Bearer test-token"}
