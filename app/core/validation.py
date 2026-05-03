"""Input validation utilities."""
from __future__ import annotations

import re
from typing import Any

from app.core.exceptions import ValidationError


# Patterns
ORDER_ID_PATTERN = re.compile(r"^ORD-\d{6}$", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
TRACKING_PATTERN = re.compile(r"^[A-Z0-9]{8,20}$", re.IGNORECASE)


def validate_order_id(order_id: str | None) -> str:
    """Validate order ID format."""
    if not order_id:
        raise ValidationError("Order ID is required", field="order_id")
    
    if not isinstance(order_id, str):
        raise ValidationError("Order ID must be a string", field="order_id")
    
    order_id = order_id.strip().upper()
    
    if not ORDER_ID_PATTERN.match(order_id):
        raise ValidationError(
            "Order ID must be in format ORD-XXXXXX (e.g., ORD-000123)",
            field="order_id",
            details={"provided": order_id, "expected_format": "ORD-XXXXXX"},
        )
    
    return order_id


def validate_email(email: str) -> str:
    """Validate email format."""
    if not email:
        raise ValidationError("Email is required", field="email")
    
    if not isinstance(email, str):
        raise ValidationError("Email must be a string", field="email")
    
    email = email.strip().lower()
    
    if not EMAIL_PATTERN.match(email):
        raise ValidationError(
            "Invalid email format",
            field="email",
            details={"provided": email},
        )
    
    return email


def validate_address(address: str) -> str:
    """Validate shipping address."""
    if not address:
        raise ValidationError("Address is required", field="address")
    
    if not isinstance(address, str):
        raise ValidationError("Address must be a string", field="address")
    
    address = address.strip()
    
    if len(address) < 10:
        raise ValidationError(
            "Address must be at least 10 characters long",
            field="address",
            details={"length": len(address), "minimum": 10},
        )
    
    if len(address) > 500:
        raise ValidationError(
            "Address must be less than 500 characters",
            field="address",
            details={"length": len(address), "maximum": 500},
        )
    
    return address


def validate_refund_reason(reason: str) -> str:
    """Validate refund reason."""
    if not reason:
        raise ValidationError("Refund reason is required", field="refund_reason")
    
    if not isinstance(reason, str):
        raise ValidationError("Refund reason must be a string", field="refund_reason")
    
    valid_reasons = {
        "damaged",
        "wrong_item",
        "not_as_described",
        "defective",
        "missing_parts",
        "changed_mind",
        "better_price",
        "other",
    }
    
    reason = reason.strip().lower()
    
    if reason not in valid_reasons:
        raise ValidationError(
            "Invalid refund reason",
            field="refund_reason",
            details={"provided": reason, "valid_reasons": list(valid_reasons)},
        )
    
    return reason


def validate_amount(amount: float, min_value: float = 0.0, max_value: float = 100000.0) -> float:
    """Validate monetary amount."""
    if amount is None:
        raise ValidationError("Amount is required", field="amount")
    
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValidationError("Amount must be a valid number", field="amount")
    
    if amount < min_value:
        raise ValidationError(
            f"Amount must be at least {min_value}",
            field="amount",
            details={"value": amount, "minimum": min_value},
        )
    
    if amount > max_value:
        raise ValidationError(
            f"Amount must not exceed {max_value}",
            field="amount",
            details={"value": amount, "maximum": max_value},
        )
    
    return round(amount, 2)


def validate_message(message: str, max_length: int = 2000) -> str:
    """Validate user message."""
    if not message:
        raise ValidationError("Message is required", field="message")
    
    if not isinstance(message, str):
        raise ValidationError("Message must be a string", field="message")
    
    message = message.strip()
    
    if len(message) == 0:
        raise ValidationError("Message cannot be empty", field="message")
    
    if len(message) > max_length:
        raise ValidationError(
            f"Message must not exceed {max_length} characters",
            field="message",
            details={"length": len(message), "maximum": max_length},
        )
    
    return message


def validate_language(language: str) -> str:
    """Validate language code."""
    if not language:
        raise ValidationError("Language is required", field="language")
    
    valid_languages = {"en", "vi"}
    language = language.strip().lower()
    
    if language not in valid_languages:
        raise ValidationError(
            "Invalid language code",
            field="language",
            details={"provided": language, "valid_languages": list(valid_languages)},
        )
    
    return language


def validate_risk_flag(risk_flag: str) -> str:
    """Validate risk flag."""
    if not risk_flag:
        return "low"
    
    valid_flags = {"low", "medium", "high"}
    risk_flag = risk_flag.strip().lower()
    
    if risk_flag not in valid_flags:
        raise ValidationError(
            "Invalid risk flag",
            field="risk_flag",
            details={"provided": risk_flag, "valid_flags": list(valid_flags)},
        )
    
    return risk_flag


def sanitize_input(value: Any) -> str:
    """Sanitize input string to prevent injection attacks."""
    if not isinstance(value, str):
        return str(value)
    
    # Remove null bytes
    value = value.replace("\x00", "")
    
    # Remove control characters except newlines and tabs
    value = "".join(char for char in value if char.isprintable() or char in "\n\t")
    
    return value.strip()
