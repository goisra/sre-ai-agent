"""Deterministic LLM provider.

Used as the default runtime provider (so the app works with zero API keys)
and as the test double for the agent's tool-calling loop. It follows a
fixed investigation plan instead of calling a real model, so its behavior
is 100% reproducible.
"""

from __future__ import annotations

import re

from agent.providers.base import LLMDecision, LLMProvider, ToolResult, ToolSpec
from agent.tools.fixtures import known_services

_KNOWN_SERVICES = known_services()

# Order in which the mock investigates a service before answering.
_INVESTIGATION_PLAN = [
    "get_service_status",
    "get_recent_deployments",
    "get_error_rate",
]


def _extract_service(message: str) -> str | None:
    lowered = message.lower()
    for service in _KNOWN_SERVICES:
        if service in lowered:
            return service
    return None


def _find_result(tool_results: list[ToolResult], tool_name: str) -> dict | None:
    for tool_result in tool_results:
        if tool_result.tool == tool_name:
            return tool_result.result
    return None


class MockProvider(LLMProvider):
    def decide(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]],
        tool_results: list[ToolResult],
        tools: list[ToolSpec],
    ) -> LLMDecision:
        service = _extract_service(user_message)

        if service is None:
            return LLMDecision(
                kind="final_answer",
                content=(
                    "I can help you investigate a service's health. Ask me about a "
                    f"specific service, for example: {', '.join(_KNOWN_SERVICES)}."
                ),
            )

        mentions_incidents = bool(re.search(r"incident", user_message, re.IGNORECASE))
        called_names = {tool_result.tool for tool_result in tool_results}

        plan = list(_INVESTIGATION_PLAN)
        if mentions_incidents:
            plan.append("get_recent_incidents")

        for step in plan:
            if step not in called_names:
                return LLMDecision(kind="tool_call", tool_name=step, arguments={"service": service})

        return LLMDecision(kind="final_answer", content=self._summarize(service, tool_results))

    @staticmethod
    def _summarize(service: str, tool_results: list[ToolResult]) -> str:
        status = _find_result(tool_results, "get_service_status") or {}
        deployment = _find_result(tool_results, "get_recent_deployments") or {}
        error_rate = _find_result(tool_results, "get_error_rate") or {}
        incidents = _find_result(tool_results, "get_recent_incidents")

        state = status.get("status", "unknown")
        rate = status.get("error_rate")
        latency = status.get("latency_ms")

        if state == "operational":
            return (
                f"The {service} service is currently operational with a {rate}% error rate "
                f"and {latency}ms latency. No action appears to be needed."
            )

        sentences = [
            f"The {service} service is currently {state} with a {rate}% error rate "
            f"and elevated latency ({latency}ms)."
        ]

        version = deployment.get("deployment")
        minutes_ago = deployment.get("minutes_ago")
        if version:
            sentences.append(
                f"The latest deployment was {version}, which went out approximately "
                f"{minutes_ago} minutes ago."
            )

        trend = error_rate.get("trend")
        if trend == "increasing" and version:
            sentences.append(
                "The increase in errors lines up with that deployment, which suggests "
                "the latest release as a potential contributor."
            )

        if incidents and incidents.get("incidents"):
            titles = ", ".join(i["title"] for i in incidents["incidents"])
            sentences.append(f"Related open incidents: {titles}.")

        sentences.append(
            "Further investigation would be required before confirming the root cause."
        )
        return " ".join(sentences)
