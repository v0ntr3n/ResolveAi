"""Request logging middleware for HTTP request/response tracking."""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import structlog

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and log request/response details.
        
        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.
            
        Returns:
            HTTP response.
        """
        # Log request
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None,
        )
        
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log response
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            
            return response
            
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                error_type=type(exc).__name__,
                duration_ms=round(duration_ms, 2),
            )
            raise
