"""
pytest configuration for InfraForge.

Centrally validates the Azure deploy context required by
``azure_infrastructure_test.py`` before any integration tests run.
"""

import os
import pytest


# ---------------------------------------------------------------------------
# Marker registration
# ---------------------------------------------------------------------------

def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "azure_integration: marks tests that require a live Azure deploy context "
        "(AZURE_SUBSCRIPTION_ID env var + valid credential via DefaultAzureCredential).",
    )


# ---------------------------------------------------------------------------
# Azure context preflight
# ---------------------------------------------------------------------------

_AZURE_ENV_VARS = ("AZURE_SUBSCRIPTION_ID",)


def _missing_azure_vars():
    """Return a list of required Azure env vars that are not set."""
    return [v for v in _AZURE_ENV_VARS if not os.environ.get(v)]


def _azure_context_available():
    """Return True when the minimum Azure env/auth context is present."""
    return not _missing_azure_vars()


@pytest.fixture(scope="session", autouse=False, name="azure_context")
def azure_context_fixture():
    """Session-scoped fixture that validates Azure deploy context.

    Request this fixture in any test that needs live Azure access.
    It skips the test (instead of failing cryptically) when the
    required environment is not present.
    """
    missing = _missing_azure_vars()
    if missing:
        pytest.skip(
            "Azure integration tests require the following env vars: "
            + ", ".join(missing)
            + ". Set them and run `az login` (or configure a service principal) "
            "before running these tests. "
            "See docs/SETUP.md § 'Running Integration Tests' for the full setup guide."
        )


def pytest_collection_modifyitems(config, items):
    """Skip azure_integration tests when Azure context is missing."""
    if _azure_context_available():
        return

    missing = _missing_azure_vars()
    reason = (
        "Azure deploy context not available — missing env vars: "
        + ", ".join(missing)
        + ". Set them and run `az login` before running Azure integration tests. "
        "See docs/SETUP.md § 'Running Integration Tests'."
    )
    skip_marker = pytest.mark.skip(reason=reason)
    for item in items:
        if item.get_closest_marker("azure_integration"):
            item.add_marker(skip_marker)
