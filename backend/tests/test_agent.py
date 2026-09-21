from agent.agent import Agent
from agent.providers.base import LLMDecision, LLMProvider
from agent.providers.mock_provider import MockProvider


def test_agent_investigates_a_degraded_service_before_answering():
    agent = Agent(MockProvider())

    result = agent.run("Why is payments failing?")

    called_tools = [call.tool for call in result.tool_calls]
    assert called_tools == ["get_service_status", "get_recent_deployments", "get_error_rate"]
    assert "payments" in result.response
    assert "8.4%" in result.response
    assert "v2.8.1" in result.response


def test_agent_skips_tools_for_healthy_service():
    agent = Agent(MockProvider())

    result = agent.run("What is the status of auth?")

    assert "operational" in result.response


def test_agent_answers_directly_when_no_service_is_mentioned():
    agent = Agent(MockProvider())

    result = agent.run("hello")

    assert result.tool_calls == []
    assert "service" in result.response.lower()


def test_agent_calls_incidents_tool_when_asked_about_incidents():
    agent = Agent(MockProvider())

    result = agent.run("Are there any incidents for notifications?")

    called_tools = {call.tool for call in result.tool_calls}
    assert "get_recent_incidents" in called_tools


class _AlwaysCallToolProvider(LLMProvider):
    """Stub that never returns a final answer, to exercise the safety cap."""

    def decide(self, *, user_message, history, tool_results, tools):
        return LLMDecision(
            kind="tool_call",
            tool_name="get_service_status",
            arguments={"service": "payments"},
        )


def test_agent_stops_after_max_steps_even_if_provider_never_answers():
    agent = Agent(_AlwaysCallToolProvider())

    result = agent.run("Why is payments failing?")

    assert len(result.tool_calls) == 5
    assert "couldn't reach a conclusive answer" in result.response
