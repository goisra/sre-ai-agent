"""Tool: get_error_rate."""

from __future__ import annotations

from typing import Any

from agent.tools.fixtures import get_service, service_parameter_schema

NAME = "get_error_rate"

SCHEMA: dict[str, Any] = {
    "name": NAME,
    "description": "Get detailed error rate metrics for a service, including trend vs. baseline.",
    "parameters": {
        "type": "object",
        "properties": {"service": service_parameter_schema()},
        "required": ["service"],
    },
}


def get_error_rate(arguments: dict[str, Any]) -> dict[str, Any]:
    service_name = arguments["service"]
    service = get_service(service_name)
    current = service["error_rate"]
    baseline = service["baseline_error_rate"]
    trend = "increasing" if current > baseline else "stable"
    return {
        "service": service_name,
        "current_error_rate": current,
        "baseline_error_rate": baseline,
        "trend": trend,
    }
