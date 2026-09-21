from django.db import connections
from django.db.utils import OperationalError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class LivenessView(APIView):
    """Is the process up? Should never depend on external services."""

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class ReadinessView(APIView):
    """Is the process ready to serve traffic? Checks critical dependencies."""

    def get(self, request: Request) -> Response:
        db_ok = self._check_database()
        status_code = 200 if db_ok else 503
        return Response(
            {"status": "ok" if db_ok else "unavailable", "checks": {"database": db_ok}},
            status=status_code,
        )

    @staticmethod
    def _check_database() -> bool:
        try:
            connections["default"].ensure_connection()
            return True
        except OperationalError:
            return False
