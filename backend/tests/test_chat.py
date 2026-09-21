import pytest

from apps.conversations.models import Conversation, Message, ToolCallRecord


@pytest.mark.django_db
def test_chat_creates_a_new_conversation_when_none_is_given(api_client):
    response = api_client.post(
        "/api/v1/chat", {"message": "Why is payments failing?"}, format="json"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["conversation_id"]
    assert "payments" in body["message"]
    assert {c["tool"] for c in body["tool_calls"]} == {
        "get_service_status",
        "get_recent_deployments",
        "get_error_rate",
    }

    conversation = Conversation.objects.get(id=body["conversation_id"])
    assert Message.objects.filter(conversation=conversation).count() == 2
    assistant_message = Message.objects.get(conversation=conversation, role=Message.Role.ASSISTANT)
    assert ToolCallRecord.objects.filter(message=assistant_message).count() == 3


@pytest.mark.django_db
def test_chat_reuses_an_existing_conversation(api_client):
    first = api_client.post("/api/v1/chat", {"message": "status of auth"}, format="json").json()

    second = api_client.post(
        "/api/v1/chat",
        {"message": "and now payments?", "conversation_id": first["conversation_id"]},
        format="json",
    ).json()

    assert second["conversation_id"] == first["conversation_id"]
    assert Message.objects.filter(conversation_id=first["conversation_id"]).count() == 4


@pytest.mark.django_db
def test_chat_rejects_blank_message(api_client):
    response = api_client.post("/api/v1/chat", {"message": ""}, format="json")

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in body


@pytest.mark.django_db
def test_chat_returns_json_error_when_agent_raises(api_client, monkeypatch):
    def _boom(self, message, history=None):
        raise RuntimeError("provider exploded")

    monkeypatch.setattr("agent.agent.Agent.run", _boom)

    response = api_client.post("/api/v1/chat", {"message": "status of payments"}, format="json")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AGENT_UNAVAILABLE"
