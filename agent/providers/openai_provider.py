"""OpenAI-backed LLM provider, using native tool/function calling."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from agent.providers.base import LLMDecision, LLMProvider, ToolResult, ToolSpec

logger = logging.getLogger("sre_agent")

_SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.txt"


def _load_system_prompt() -> str:
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def _to_openai_tools(tools: list[ToolSpec]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            },
        }
        for tool in tools
    ]


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("LLM_API_KEY is required when LLM_PROVIDER=openai.")

        from openai import OpenAI  # imported lazily so it's an optional dependency at runtime

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def decide(
        self,
        *,
        user_message: str,
        history: list[dict[str, str]],
        tool_results: list[ToolResult],
        tools: list[ToolSpec],
    ) -> LLMDecision:
        messages = [{"role": "system", "content": _load_system_prompt()}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        for tool_result in tool_results:
            messages.append(
                {
                    "role": "assistant",
                    "content": (
                        f"[tool result] {tool_result.tool}({json.dumps(tool_result.arguments)}) "
                        f"=> {json.dumps(tool_result.result)}"
                    ),
                }
            )

        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=_to_openai_tools(tools),
            tool_choice="auto",
        )
        choice = response.choices[0].message

        logger.info(
            "llm_response",
            extra={
                "event": "llm_response",
                "requested_model": self._model,
                "served_by_model": response.model,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
            },
        )

        if choice.tool_calls:
            call = choice.tool_calls[0]
            return LLMDecision(
                kind="tool_call",
                tool_name=call.function.name,
                arguments=json.loads(call.function.arguments or "{}"),
            )

        return LLMDecision(kind="final_answer", content=choice.content or "")
