"""The agent: a small tool-calling loop, decoupled from Django and from
any specific LLM SDK.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from agent.providers.base import LLMProvider, ToolResult
from agent.tools.registry import execute_tool, tool_specs

MAX_STEPS = 5


@dataclass
class ToolCallInfo:
    tool: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    duration_ms: int


@dataclass
class AgentResult:
    response: str
    tool_calls: list[ToolCallInfo] = field(default_factory=list)


class Agent:
    """Receives a message, optionally calls tools, and returns an answer."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        self._llm_provider = llm_provider
        self._tools = tool_specs()

    def run(self, message: str, history: list[dict[str, str]] | None = None) -> AgentResult:
        history = history or []
        tool_results: list[ToolResult] = []
        tool_calls: list[ToolCallInfo] = []

        for _ in range(MAX_STEPS):
            decision = self._llm_provider.decide(
                user_message=message,
                history=history,
                tool_results=tool_results,
                tools=self._tools,
            )

            if decision.kind == "final_answer":
                return AgentResult(response=decision.content or "", tool_calls=tool_calls)

            started_at = time.perf_counter()
            result = execute_tool(decision.tool_name, decision.arguments)
            duration_ms = int((time.perf_counter() - started_at) * 1000)

            tool_results.append(
                ToolResult(tool=decision.tool_name, arguments=decision.arguments, result=result)
            )
            tool_calls.append(
                ToolCallInfo(
                    tool=decision.tool_name,
                    arguments=decision.arguments,
                    result=result,
                    duration_ms=duration_ms,
                )
            )

        return AgentResult(
            response="I gathered some data but couldn't reach a conclusive answer in time. "
            "Please try narrowing your question.",
            tool_calls=tool_calls,
        )
