import pytest
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def force_mock_llm_provider(monkeypatch):
    """Tests must never call a real LLM, regardless of the developer's local .env.

    LLM_PROVIDER is read straight from the environment on every request (see
    agent/providers/factory.py), so overriding it here is enough to force the
    deterministic mock provider for the whole test suite.
    """
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_API_KEY", "")


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()
