"""Explicit tool registry.

The agent can only call tools listed here. This is a deliberate security
boundary: there is no dynamic dispatch to arbitrary functions or system
commands, only to the callables registered below.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, NamedTuple

from agent.providers.base import ToolSpec
from agent.tools import deployments, error_rate, incidents, service_status


class RegisteredTool(NamedTuple):
    func: Callable[[dict[str, Any]], dict[str, Any]]
    schema: ToolSpec


TOOL_REGISTRY: dict[str, RegisteredTool] = {
    service_status.NAME: RegisteredTool(service_status.get_service_status, service_status.SCHEMA),
    deployments.NAME: RegisteredTool(deployments.get_recent_deployments, deployments.SCHEMA),
    incidents.NAME: RegisteredTool(incidents.get_recent_incidents, incidents.SCHEMA),
    error_rate.NAME: RegisteredTool(error_rate.get_error_rate, error_rate.SCHEMA),
}


def tool_specs() -> list[ToolSpec]:
    return [tool.schema for tool in TOOL_REGISTRY.values()]


class UnknownToolError(Exception):
    pass


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    tool = TOOL_REGISTRY.get(name)
    if tool is None:
        raise UnknownToolError(f"Tool '{name}' is not registered.")
    return tool.func(arguments)
