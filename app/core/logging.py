"""Structured logging configuration using structlog."""

import logging
import sys

import structlog
from structlog.types import Processor

from app.core.config import get_settings


def configure_logging(service_name: str = "resolveai-api") -> None:
    """Configure structured logging for the application.
    
    Args:
        service_name: Name of the service for logging context.
    """
    settings = get_settings()
    
    # Determine environment
    environment = "production" if settings.DEEPSEEK_API_KEY else "development"
    
    # Shared processors for all loggers
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.ExceptionRenderer(),
    ]
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer() if environment == "production"
            else structlog.dev.ConsoleRenderer(),
        ],
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Set service context
    structlog.contextvars.bind_contextvars(
        service=service_name,
        environment=environment,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Name of the logger (typically __name__).
        
    Returns:
        Configured structlog logger instance.
    """
    return structlog.get_logger(name)
