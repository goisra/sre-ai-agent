import pytest
from agent.tools.deployments import get_recent_deployments
from agent.tools.error_rate import get_error_rate
from agent.tools.incidents import get_recent_incidents
from agent.tools.registry import TOOL_REGISTRY, UnknownToolError, execute_tool, tool_specs
from agent.tools.service_status import get_service_status


def test_get_service_status_returns_known_service_data():
    result = get_service_status({"service": "payments"})

    assert result == {
        "service": "payments",
        "status": "degraded",
        "error_rate": 8.4,
        "latency_ms": 480,
    }


def test_get_service_status_falls_back_for_unknown_service():
    result = get_service_status({"service": "does-not-exist"})

    assert result["status"] == "unknown"


def test_get_recent_deployments_returns_latest_deployment():
    result = get_recent_deployments({"service": "payments"})

    assert result["deployment"] == "v2.8.1"
    assert result["status"] == "success"
    assert result["timestamp"] is not None


def test_get_recent_incidents_returns_list_for_service():
    result = get_recent_incidents({"service": "payments"})

    assert len(result["incidents"]) == 1
    assert result["incidents"][0]["id"] == "INC-1042"


def test_get_recent_incidents_returns_empty_list_for_healthy_service():
    result = get_recent_incidents({"service": "auth"})

    assert result["incidents"] == []


def test_get_error_rate_flags_increasing_trend():
    result = get_error_rate({"service": "payments"})

    assert result["trend"] == "increasing"
    assert result["current_error_rate"] == 8.4


def test_get_error_rate_flags_stable_trend_for_healthy_service():
    result = get_error_rate({"service": "auth"})

    assert result["trend"] == "stable"


def test_registry_exposes_all_tools():
    assert set(TOOL_REGISTRY) == {
        "get_service_status",
        "get_recent_deployments",
        "get_recent_incidents",
        "get_error_rate",
    }


def test_tool_specs_include_name_and_parameters():
    specs = tool_specs()

    assert all("name" in spec and "parameters" in spec for spec in specs)


def test_execute_tool_dispatches_by_name():
    result = execute_tool("get_service_status", {"service": "payments"})

    assert result["service"] == "payments"


def test_execute_tool_raises_for_unregistered_tool():
    with pytest.raises(UnknownToolError):
        execute_tool("delete_everything", {})
