"""Custom exceptions and error handling utilities."""
from __future__ import annotations

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    """Standardized error codes for the application."""
    INVALID_INPUT = "INVALID_INPUT"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    ADDRESS_CHANGE_NOT_ALLOWED = "ADDRESS_CHANGE_NOT_ALLOWED"
    REFUND_NOT_ALLOWED = "REFUND_NOT_ALLOWED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    LLM_ERROR = "LLM_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"


class BaseAppException(Exception):
    """Base exception for all application errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(BaseAppException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: str | None = None, details: dict[str, Any] | None = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(message, ErrorCode.VALIDATION_ERROR, error_details)


class OrderNotFoundError(BaseAppException):
    """Raised when order is not found."""
    
    def __init__(self, order_id: str):
        super().__init__(
            f"Order '{order_id}' not found",
            ErrorCode.ORDER_NOT_FOUND,
            {"order_id": order_id},
        )


class AddressChangeNotAllowedError(BaseAppException):
    """Raised when address change is not allowed."""
    
    def __init__(self, order_id: str, reason: str):
        super().__init__(
            f"Address change not allowed for order '{order_id}': {reason}",
            ErrorCode.ADDRESS_CHANGE_NOT_ALLOWED,
            {"order_id": order_id, "reason": reason},
        )


class RefundNotAllowedError(BaseAppException):
    """Raised when refund is not allowed."""
    
    def __init__(self, order_id: str, reason: str):
        super().__init__(
            f"Refund not allowed for order '{order_id}': {reason}",
            ErrorCode.REFUND_NOT_ALLOWED,
            {"order_id": order_id, "reason": reason},
        )


class LLMError(BaseAppException):
    """Raised when LLM operation fails."""
    
    def __init__(self, operation: str, details: str | None = None):
        super().__init__(
            f"LLM operation failed: {operation}",
            ErrorCode.LLM_ERROR,
            {"operation": operation, "details": details},
        )


class DatabaseError(BaseAppException):
    """Raised when database operation fails."""
    
    def __init__(self, operation: str, details: str | None = None):
        super().__init__(
            f"Database operation failed: {operation}",
            ErrorCode.DATABASE_ERROR,
            {"operation": operation, "details": details},
        )


class CacheError(BaseAppException):
    """Raised when cache operation fails."""
    
    def __init__(self, operation: str, details: str | None = None):
        super().__init__(
            f"Cache operation failed: {operation}",
            ErrorCode.CACHE_ERROR,
            {"operation": operation, "details": details},
        )


def format_error_response(error: Exception) -> dict[str, Any]:
    """Format any exception as a standard error response."""
    if isinstance(error, BaseAppException):
        return error.to_dict()
    
    # Convert unexpected exceptions to generic error
    return {
        "error": ErrorCode.INTERNAL_ERROR,
        "message": "An unexpected error occurred",
        "details": {"type": type(error).__name__},
    }
