"""Consistent JSON error envelope for the whole API.

Response shape:
{
  "error": {"code": "...", "message": "..."},
  "request_id": "..."
}

Stack traces are never returned to the client; unexpected exceptions are
logged server-side and mapped to a generic message instead.
"""

from __future__ import annotations

import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("sre_agent")

_DEFAULT_CODES = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    429: "RATE_LIMITED",
}


class APIError(Exception):
    """Raise inside services to surface a specific error code/message to the client."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _request_id(context) -> str | None:
    request = context.get("request")
    return getattr(request, "request_id", None) if request else None


def api_exception_handler(exc, context):
    request_id = _request_id(context)

    if isinstance(exc, APIError):
        return Response(
            {"error": {"code": exc.code, "message": exc.message}, "request_id": request_id},
            status=exc.status_code,
        )

    response = drf_exception_handler(exc, context)

    if response is not None:
        code = _DEFAULT_CODES.get(response.status_code, "ERROR")
        detail = (
            response.data.get("detail", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        response.data = {"error": {"code": code, "message": str(detail)}, "request_id": request_id}
        return response

    logger.exception(
        "unhandled_exception",
        extra={"event": "unhandled_exception", "request_id": request_id},
    )
    return Response(
        {
            "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
            "request_id": request_id,
        },
        status=500,
    )
