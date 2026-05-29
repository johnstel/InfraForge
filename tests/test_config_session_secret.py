import importlib

import src.config as config


def test_session_secret_uses_env_value(monkeypatch):
    monkeypatch.setenv("INFRAFORGE_SESSION_SECRET", "test-session-secret")
    importlib.reload(config)
    assert config.SESSION_SECRET == "test-session-secret"


def test_session_secret_fallback_is_generated(monkeypatch):
    monkeypatch.delenv("INFRAFORGE_SESSION_SECRET", raising=False)
    importlib.reload(config)
    assert config.SESSION_SECRET
    assert config.SESSION_SECRET != "infraforge-dev-secret-change-in-prod"
