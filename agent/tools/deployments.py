"""Tool: get_recent_deployments."""

from __future__ import annotations

from typing import Any

from agent.tools.fixtures import get_service, iso_timestamp_minutes_ago, service_parameter_schema

NAME = "get_recent_deployments"

SCHEMA: dict[str, Any] = {
    "name": NAME,
    "description": "Get the most recent deployment for a service.",
    "parameters": {
        "type": "object",
        "properties": {"service": service_parameter_schema()},
        "required": ["service"],
    },
}


def get_recent_deployments(arguments: dict[str, Any]) -> dict[str, Any]:
    service_name = arguments["service"]
    deployments = get_service(service_name)["deployments"]
    if not deployments:
        return {"service": service_name, "deployment": None, "timestamp": None, "status": "none"}

    latest = deployments[0]
    return {
        "service": service_name,
        "deployment": latest["version"],
        "timestamp": iso_timestamp_minutes_ago(latest["minutes_ago"]),
        "minutes_ago": latest["minutes_ago"],
        "status": latest["status"],
    }
