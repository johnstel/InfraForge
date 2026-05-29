import importlib
import os

import pytest
import src.config as config


@pytest.fixture(autouse=True)
def restore_config_after_test():
    original = os.environ.get("INFRAFORGE_SESSION_SECRET")
    yield
    if original is None:
        os.environ.pop("INFRAFORGE_SESSION_SECRET", None)
    else:
        os.environ["INFRAFORGE_SESSION_SECRET"] = original
    importlib.reload(config)


def test_session_secret_uses_env_value(monkeypatch):
    monkeypatch.setenv("INFRAFORGE_SESSION_SECRET", "test-session-secret")
    importlib.reload(config)
    assert config.SESSION_SECRET == "test-session-secret"


def test_session_secret_fallback_is_generated(monkeypatch):
    monkeypatch.delenv("INFRAFORGE_SESSION_SECRET", raising=False)
    importlib.reload(config)
    assert config.SESSION_SECRET
    assert len(config.SESSION_SECRET) >= 64
    assert config.SESSION_SECRET != "infraforge-dev-secret-change-in-prod"
