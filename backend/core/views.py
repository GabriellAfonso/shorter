"""Shared utility views."""
import logging
import time

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views import View

logger = logging.getLogger(__name__)


class HealthCheckView(View):
    """
    GET /api/v1/health/

    Returns HTTP 200 when DB and Redis are reachable; 503 otherwise.
    Used by Docker HEALTHCHECK, load balancers, and uptime monitors.
    """

    def get(self, request):
        checks = {}
        ok = True

        # ── Database ──────────────────────────────────────────────────────
        t0 = time.monotonic()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks["db"] = {"status": "ok", "latency_ms": round((time.monotonic() - t0) * 1000, 1)}
        except Exception as exc:
            logger.error("Health check DB failed: %s", exc)
            checks["db"] = {"status": "error", "detail": str(exc)}
            ok = False

        # ── Redis (via Django cache API) ───────────────────────────────────
        t0 = time.monotonic()
        try:
            cache.set("_health_check_ping", 1, timeout=10)
            val = cache.get("_health_check_ping")
            if val != 1:
                raise ValueError(f"Cache verification failed: got {val!r}")
            checks["redis"] = {"status": "ok", "latency_ms": round((time.monotonic() - t0) * 1000, 1)}
        except Exception as exc:
            logger.error("Health check Redis failed: %s", exc)
            checks["redis"] = {"status": "error", "detail": str(exc)}
            ok = False

        status_code = 200 if ok else 503
        return JsonResponse({"status": "ok" if ok else "degraded", "checks": checks}, status=status_code)
