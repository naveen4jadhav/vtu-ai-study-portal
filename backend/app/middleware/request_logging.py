"""
Request logging middleware.

Logs every incoming request/response with method, path, status code,
client host, and processing time. Also injects an `X-Process-Time`
response header for observability.
"""
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs request/response metadata and measures response time."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        client_host = request.client.host if request.client else "unknown"
        logger.info(
            "request_started id=%s method=%s path=%s client=%s",
            request_id,
            request.method,
            request.url.path,
            client_host,
        )

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "request_failed id=%s method=%s path=%s duration_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed id=%s method=%s path=%s status=%d duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
