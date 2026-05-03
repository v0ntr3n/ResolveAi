"""Test Week 3 enhancements: tracing, metrics, and RAGAS."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY, INTENT_CLASSIFICATION
from app.core.tracing import configure_tracing, get_trace_url


def test_prometheus_metrics_endpoint():
    """Test Prometheus metrics endpoint returns valid metrics."""
    client = TestClient(app)
    
    # Make a few requests to generate metrics
    response = client.get("/health")
    assert response.status_code == 200
    
    # Check prometheus metrics endpoint
    response = client.get("/prometheus")
    assert response.status_code == 200
    assert "resolveai_requests_total" in response.text
    assert "resolveai_request_latency_seconds" in response.text


def test_tracing_configuration():
    """Test LangSmith tracing configuration."""
    # Should not raise errors even without API key
    client = configure_tracing()
    assert client is None  # No API key configured in tests


def test_trace_url_generation():
    """Test trace URL generation."""
    url = get_trace_url("test-run-id")
    # Should return empty string without proper configuration
    assert url == ""


def test_metrics_registry():
    """Test Prometheus metrics registry."""
    # Verify metrics are properly registered
    from app.core.metrics import registry
    
    # Check that our custom metrics exist
    metrics = list(registry.collect())
    metric_names = [m.name for m in metrics]
    
    # Check for metric names (without _total suffix for counters)
    assert "resolveai_requests" in metric_names
    assert "resolveai_request_latency_seconds" in metric_names
    assert "resolveai_intent_classification" in metric_names
    assert "resolveai_resolutions" in metric_names
    assert "resolveai_escalations" in metric_names
    assert "resolveai_llm_call_duration_seconds" in metric_names
    assert "resolveai_cache_hits" in metric_names
    assert "resolveai_cache_misses" in metric_names
    assert "resolveai_node_execution_seconds" in metric_names


def test_health_endpoint_with_tracing():
    """Test that health endpoint works with tracing decorator."""
    client = TestClient(app)
    
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ragas_evaluator_initialization():
    """Test RAGAS evaluator can be initialized with proper error handling."""
    import os
    from app.evals.ragas_eval import RAGASEvaluator
    
    # Temporarily unset OPENAI_API_KEY to test error handling
    original_key = os.environ.get("OPENAI_API_KEY", "")
    os.environ["OPENAI_API_KEY"] = ""
    
    # Clear the settings cache to pick up new environment
    from app.core.config import get_settings
    get_settings.cache_clear()
    
    try:
        # Should raise ValueError without OpenAI API key
        with pytest.raises(ValueError, match="OPENAI_API_KEY required"):
            RAGASEvaluator()
    finally:
        # Restore original key
        os.environ["OPENAI_API_KEY"] = original_key
        get_settings.cache_clear()


def test_ragas_test_cases_exist():
    """Test RAGAS test cases file exists and has correct format."""
    import json
    from pathlib import Path
    
    test_cases_path = Path("data/evals/ragas_test_cases.json")
    assert test_cases_path.exists(), "RAGAS test cases file should exist"
    
    with open(test_cases_path, encoding="utf-8") as f:
        cases = json.load(f)
    
    assert len(cases) > 0, "Should have test cases"
    
    for case in cases:
        assert "id" in case
        assert "query" in case
        assert "expected_answer" in case
        assert "category" in case


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
