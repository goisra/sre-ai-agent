"""Bridges the Django layer to the framework-agnostic agent core.

View -> Serializer -> Service (this file) -> Agent -> LLM / Tools
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from agent.agent import Agent, AgentResult
from agent.providers.factory import get_llm_provider

from apps.conversations.models import Conversation, Message, ToolCallRecord
from config.exceptions import APIError

logger = logging.getLogger("sre_agent")

HISTORY_LIMIT = 10


@dataclass
class ChatResult:
    conversation_id: UUID
    message: str
    tool_calls: list[dict]


class ChatService:
    """Orchestrates persistence around a single agent turn."""

    def __init__(self, agent: Agent | None = None) -> None:
        self._agent = agent or Agent(get_llm_provider())

    def handle_chat(
        self, message: str, conversation_id: UUID | None, request_id: str | None
    ) -> ChatResult:
        conversation = self._get_or_create_conversation(conversation_id)
        history = self._load_history(conversation)

        Message.objects.create(conversation=conversation, role=Message.Role.USER, content=message)

        try:
            result: AgentResult = self._agent.run(message, history=history)
        except Exception:
            logger.exception(
                "agent_execution_failed",
                extra={"event": "agent_execution_failed", "request_id": request_id},
            )
            raise APIError(
                code="AGENT_UNAVAILABLE",
                message="The AI agent is temporarily unavailable.",
                status_code=503,
            ) from None

        assistant_message = Message.objects.create(
            conversation=conversation, role=Message.Role.ASSISTANT, content=result.response
        )

        tool_calls_data = []
        for call in result.tool_calls:
            ToolCallRecord.objects.create(
                message=assistant_message,
                tool_name=call.tool,
                arguments=call.arguments,
                result=call.result,
                duration_ms=call.duration_ms,
            )
            logger.info(
                "tool_execution",
                extra={
                    "event": "tool_execution",
                    "tool": call.tool,
                    "duration_ms": call.duration_ms,
                    "request_id": request_id,
                },
            )
            tool_calls_data.append({"tool": call.tool, "duration_ms": call.duration_ms})

        return ChatResult(
            conversation_id=conversation.id, message=result.response, tool_calls=tool_calls_data
        )

    @staticmethod
    def _get_or_create_conversation(conversation_id: UUID | None) -> Conversation:
        if conversation_id is None:
            return Conversation.objects.create()

        conversation, _ = Conversation.objects.get_or_create(id=conversation_id)
        return conversation

    @staticmethod
    def _load_history(conversation: Conversation) -> list[dict[str, str]]:
        messages = conversation.messages.order_by("-created_at")[:HISTORY_LIMIT]
        return [{"role": m.role, "content": m.content} for m in reversed(messages)]
