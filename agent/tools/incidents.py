"""Tool: get_recent_incidents."""

from __future__ import annotations

from typing import Any

from agent.tools.fixtures import get_service, iso_timestamp_minutes_ago, service_parameter_schema

NAME = "get_recent_incidents"

SCHEMA: dict[str, Any] = {
    "name": NAME,
    "description": "Get recent incidents reported for a service.",
    "parameters": {
        "type": "object",
        "properties": {"service": service_parameter_schema()},
        "required": ["service"],
    },
}


def get_recent_incidents(arguments: dict[str, Any]) -> dict[str, Any]:
    service_name = arguments["service"]
    incidents = get_service(service_name)["incidents"]
    return {
        "service": service_name,
        "incidents": [
            {
                "id": incident["id"],
                "title": incident["title"],
                "severity": incident["severity"],
                "status": incident["status"],
                "reported_at": iso_timestamp_minutes_ago(incident["minutes_ago"]),
            }
            for incident in incidents
        ],
    }
