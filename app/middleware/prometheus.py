"""Prometheus middleware for automatic request metrics collection."""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for all HTTP requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and collect metrics.
        
        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.
            
        Returns:
            The HTTP response.
        """
        # Skip metrics endpoint itself to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Record start time
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.perf_counter() - start_time

        # Record request metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        return response
