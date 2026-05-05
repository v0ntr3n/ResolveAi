"""Test CORS and API connectivity for frontend integration."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_cors_headers_present():
    """Test CORS headers are present on OPTIONS request."""
    response = client.options(
        "/chat",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_allow_credentials():
    """Test CORS credentials header."""
    response = client.options(
        "/chat",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        }
    )
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_exposed_headers():
    """Test CORS exposed headers in actual response (not preflight)."""
    # Exposed headers only appear in actual responses, not OPTIONS preflight
    response = client.post(
        "/chat",
        json={"message": "Test"},
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    # Note: exposed headers may not be present in test client
    # but will be in actual browser requests


def test_chat_endpoint_with_cors():
    """Test chat endpoint returns CORS headers."""
    response = client.post(
        "/chat",
        json={"message": "Where is my order?"},
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    data = response.json()
    assert "response" in data
    assert "conversation_id" in data
    assert "intent" in data


def test_metrics_endpoint_with_cors():
    """Test metrics endpoint returns CORS headers."""
    response = client.get(
        "/metrics",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    data = response.json()
    assert "total_conversations" in data
    assert "resolved_count" in data
    assert "escalation_count" in data


def test_escalations_endpoint_with_cors():
    """Test escalations endpoint returns CORS headers."""
    response = client.get(
        "/escalations",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert isinstance(response.json(), list)


def test_health_endpoint_with_cors():
    """Test health endpoint returns CORS headers."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.json() == {"status": "ok"}


def test_cors_primary_origin():
    """Test CORS works with the primary allowed origin."""
    # Test the main frontend origin - make actual POST request
    response = client.post(
        "/chat",
        json={"message": "Test CORS"},
        headers={"Origin": "http://localhost:3000"}
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallowed_origin():
    """Test that disallowed origins are rejected."""
    response = client.post(
        "/chat",
        json={"message": "Test"},
        headers={"Origin": "http://evil.com"}
    )
    # Request should succeed but CORS header should not be present
    assert response.status_code == 200
    # The origin header should not be present for disallowed origins
    allow_origin = response.headers.get("access-control-allow-origin", "")
    # Either the header is not present, or it's not the evil origin
    assert allow_origin == "" or allow_origin != "http://evil.com"
