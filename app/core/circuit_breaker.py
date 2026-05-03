"""Circuit breaker implementation for fault tolerance."""

import time
from enum import Enum
from functools import wraps
from typing import Any, Callable

import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance.
    
    Implements the circuit breaker pattern to prevent cascading failures
    and provide fast failure when services are unavailable.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        expected_exceptions: tuple = (Exception,),
    ):
        """Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker for logging.
            failure_threshold: Number of failures before opening circuit.
            recovery_timeout: Seconds to wait before attempting recovery.
            expected_exceptions: Exceptions that count as failures.
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = CircuitState.CLOSED
    
    def _should_allow_request(self) -> bool:
        """Check if request should be allowed based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if self.last_failure_time and \
               time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("circuit_breaker_half_open", circuit_name=self.name)
                return True
            return False
        
        return True  # HALF_OPEN
    
    def _record_success(self):
        """Record successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("circuit_breaker_recovered", circuit_name=self.name)
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _record_failure(self, exc: Exception):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("circuit_breaker_opened", circuit_name=self.name)
        elif self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                "circuit_breaker_opened",
                circuit_name=self.name,
                failure_count=self.failure_count,
            )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute.
            *args: Positional arguments for function.
            **kwargs: Keyword arguments for function.
            
        Returns:
            Function result.
            
        Raises:
            CircuitBreakerOpenError: If circuit is open.
        """
        if not self._should_allow_request():
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exceptions as exc:
            self._record_failure(exc)
            raise


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 30,
    expected_exceptions: tuple = (Exception,),
):
    """Decorator for circuit breaker pattern.
    
    Args:
        name: Name of the circuit breaker.
        failure_threshold: Failures before opening.
        recovery_timeout: Seconds before recovery attempt.
        expected_exceptions: Exceptions that count as failures.
        
    Returns:
        Decorated function with circuit breaker protection.
    """
    cb = CircuitBreaker(name, failure_threshold, recovery_timeout, expected_exceptions)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        return wrapper
    return decorator
