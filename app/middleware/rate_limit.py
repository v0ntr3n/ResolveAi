"""Rate limiting middleware for API endpoints."""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Callable

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Thread-safe rate limiter using sliding window algorithm."""
    
    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, client_id: str) -> tuple[bool, dict[str, int]]:
        """Check if request is allowed for client."""
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        with self.lock:
            # Clean old requests
            self.requests[client_id] = [
                timestamp
                for timestamp in self.requests[client_id]
                if timestamp > window_start
            ]
            
            # Check burst limit
            recent_requests = [
                timestamp
                for timestamp in self.requests[client_id]
                if timestamp > current_time - 1  # Last 1 second
            ]
            
            if len(recent_requests) >= self.burst_size:
                return False, {
                    "limit": self.requests_per_minute,
                    "remaining": 0,
                    "reset": int(window_start + 60),
                }
            
            # Check rate limit
            if len(self.requests[client_id]) >= self.requests_per_minute:
                return False, {
                    "limit": self.requests_per_minute,
                    "remaining": 0,
                    "reset": int(window_start + 60),
                }
            
            # Allow request
            self.requests[client_id].append(current_time)
            remaining = self.requests_per_minute - len(self.requests[client_id])
            
            return True, {
                "limit": self.requests_per_minute,
                "remaining": remaining,
                "reset": int(window_start + 60),
            }
    
    def get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try X-Forwarded-For header first (for reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Fall back to client host
        if request.client:
            return request.client.host
        
        return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app, requests_per_minute: int = 60, burst_size: int = 10):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute, burst_size)
        self.exempt_paths = {"/health", "/metrics", "/docs", "/openapi.json", "/redoc"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through rate limiter."""
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Skip rate limiting for non-POST requests (read-only)
        if request.method != "POST":
            return await call_next(request)
        
        # Check rate limit
        client_id = self.limiter.get_client_id(request)
        allowed, info = self.limiter.is_allowed(client_id)
        
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "details": info,
                },
            )
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(info["reset"])
            response.headers["Retry-After"] = str(info["reset"] - int(time.time()))
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
        
        return response


def setup_rate_limiting(app, requests_per_minute: int = 60, burst_size: int = 10) -> None:
    """Setup rate limiting middleware for FastAPI app."""
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=requests_per_minute,
        burst_size=burst_size,
    )
