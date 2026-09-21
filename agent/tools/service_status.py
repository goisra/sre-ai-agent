"""Tool: get_service_status."""

from __future__ import annotations

from typing import Any

from agent.tools.fixtures import get_service, service_parameter_schema

NAME = "get_service_status"

SCHEMA: dict[str, Any] = {
    "name": NAME,
    "description": "Get the current status, error rate, and latency of a service.",
    "parameters": {
        "type": "object",
        "properties": {"service": service_parameter_schema()},
        "required": ["service"],
    },
}


def get_service_status(arguments: dict[str, Any]) -> dict[str, Any]:
    service_name = arguments["service"]
    service = get_service(service_name)
    return {
        "service": service_name,
        "status": service["status"],
        "error_rate": service["error_rate"],
        "latency_ms": service["latency_ms"],
    }
