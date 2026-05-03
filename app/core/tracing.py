"""LangSmith tracing configuration for distributed tracing."""

import os
from langsmith import Client
from app.core.config import get_settings


def configure_tracing():
    """Configure LangSmith tracing for the application.
    
    Returns:
        LangSmith client if configured, None otherwise.
    """
    settings = get_settings()
    
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT or "resolveai-production"
        
        # Initialize LangSmith client
        client = Client()
        return client
    
    return None


def get_trace_url(run_id: str) -> str:
    """Get LangSmith trace URL for a specific run.
    
    Args:
        run_id: The run ID from LangSmith.
        
    Returns:
        URL to the trace in LangSmith dashboard.
    """
    settings = get_settings()
    if settings.LANGSMITH_API_KEY and settings.LANGSMITH_ORG:
        return (
            f"https://smith.langchain.com/o/{settings.LANGSMITH_ORG}"
            f"/projects/p/{settings.LANGSMITH_PROJECT}/r/{run_id}"
        )
    return ""
