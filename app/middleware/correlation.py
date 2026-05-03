"""Correlation ID middleware for request tracing."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import structlog


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to all requests for distributed tracing."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add correlation ID.
        
        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.
            
        Returns:
            HTTP response with correlation ID header.
        """
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Bind to logging context
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
