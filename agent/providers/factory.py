"""Builds an LLMProvider from configuration (env vars), decoupling the
agent from any specific provider implementation.
"""

from __future__ import annotations

import os

from agent.providers.base import LLMProvider


def get_llm_provider() -> LLMProvider:
    provider_name = os.environ.get("LLM_PROVIDER", "mock").strip().lower()

    if provider_name == "mock":
        from agent.providers.mock_provider import MockProvider

        return MockProvider()

    if provider_name == "openai":
        from agent.providers.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=os.environ.get("LLM_API_KEY", ""),
            model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
        )

    raise ValueError(f"Unknown LLM_PROVIDER '{provider_name}'. Expected 'mock' or 'openai'.")
