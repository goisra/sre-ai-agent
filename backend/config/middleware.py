"""Cross-cutting request middleware: request IDs and structured access logs."""

from __future__ import annotations

import logging
import time
import uuid

logger = logging.getLogger("sre_agent")

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware:
    """Attaches a request_id to every request, reusing an inbound header if present."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        response = self.get_response(request)
        response[REQUEST_ID_HEADER] = request.request_id
        return response


class RequestLoggingMiddleware:
    """Logs one structured event per request with timing and status."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = time.perf_counter()
        response = self.get_response(request)
        duration_ms = int((time.perf_counter() - started_at) * 1000)

        logger.info(
            "request_completed",
            extra={
                "event": "request_completed",
                "request_id": getattr(request, "request_id", None),
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
