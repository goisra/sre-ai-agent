"""LLM provider abstraction.

The agent never talks to a specific LLM SDK directly. It only knows about
this interface, so the underlying model/provider can be swapped through
configuration (LLM_PROVIDER env var) without touching agent logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict


class ToolSpec(TypedDict):
    """JSON-schema-ish description of a tool the agent may call."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class ToolResult:
    """Record of a tool that was already executed in the current run."""

    tool: str
    arguments: dict[str, Any]
    result: dict[str, Any]


@dataclass
class LLMDecision:
    """What the model wants to do next."""

    kind: Literal["tool_call", "final_answer"]
    tool_name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    content: str | None = None


class LLMProvider(ABC):
    """Decides the agent's next step: call a tool, or answer the user."""

    @abstractmethod
    def decide(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]],
        tool_results: list[ToolResult],
        tools: list[ToolSpec],
    ) -> LLMDecision:
        """Return the next action given the conversation and tool results so far.

        Args:
            user_message: the latest message from the user.
            history: prior turns as [{"role": "user"|"assistant", "content": str}].
            tool_results: tools already executed during this turn, in order.
            tools: tools the agent is allowed to call.
        """
        raise NotImplementedError
