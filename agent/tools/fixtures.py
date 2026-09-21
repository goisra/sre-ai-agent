"""Fictitious service data used by the tools.

This is a demo application: there is no real infrastructure to query, so
tools read from this in-memory fixture set instead of making network calls.
Swapping this module for real API/metrics clients would not require any
change to the agent or the tool interfaces.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

_NOW = datetime(2026, 9, 19, 12, 0, 0, tzinfo=UTC)

SERVICES: dict[str, dict[str, Any]] = {
    "payments": {
        "status": "degraded",
        "error_rate": 8.4,
        "latency_ms": 480,
        "baseline_error_rate": 0.5,
        "deployments": [
            {"version": "v2.8.1", "minutes_ago": 12, "status": "success"},
            {"version": "v2.8.0", "minutes_ago": 60 * 24 * 3, "status": "success"},
        ],
        "incidents": [
            {
                "id": "INC-1042",
                "title": "Elevated error rate after v2.8.1 rollout",
                "severity": "high",
                "status": "investigating",
                "minutes_ago": 8,
            }
        ],
    },
    "auth": {
        "status": "operational",
        "error_rate": 0.2,
        "latency_ms": 90,
        "baseline_error_rate": 0.3,
        "deployments": [
            {"version": "v5.1.0", "minutes_ago": 60 * 24, "status": "success"},
        ],
        "incidents": [],
    },
    "search": {
        "status": "operational",
        "error_rate": 1.1,
        "latency_ms": 210,
        "baseline_error_rate": 1.0,
        "deployments": [
            {"version": "v3.4.2", "minutes_ago": 60 * 6, "status": "success"},
        ],
        "incidents": [],
    },
    "notifications": {
        "status": "critical",
        "error_rate": 22.7,
        "latency_ms": 1250,
        "baseline_error_rate": 0.8,
        "deployments": [
            {"version": "v1.9.0", "minutes_ago": 25, "status": "failed"},
        ],
        "incidents": [
            {
                "id": "INC-1041",
                "title": "Notification delivery failures spiking",
                "severity": "critical",
                "status": "identified",
                "minutes_ago": 20,
            }
        ],
    },
}

DEFAULT_SERVICE: dict[str, Any] = {
    "status": "unknown",
    "error_rate": 0.0,
    "latency_ms": 0,
    "baseline_error_rate": 0.0,
    "deployments": [],
    "incidents": [],
}


def get_service(name: str) -> dict[str, Any]:
    return SERVICES.get(name.strip().lower(), DEFAULT_SERVICE)


def known_services() -> list[str]:
    return list(SERVICES.keys())


def service_parameter_schema() -> dict[str, Any]:
    """Shared JSON-schema fragment for the 'service' tool parameter.

    The `enum` constrains a real LLM provider to one of our known fixture
    services regardless of what language/wording the user asked in (e.g.
    "pagos" -> the model still has to pick "payments"), instead of relying
    on hardcoded keyword matching.
    """
    return {
        "type": "string",
        "description": "Canonical name of the service.",
        "enum": known_services(),
    }


def iso_timestamp_minutes_ago(minutes_ago: int) -> str:
    return (_NOW - timedelta(minutes=minutes_ago)).isoformat()
