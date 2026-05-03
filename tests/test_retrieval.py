import pytest
from unittest.mock import patch, MagicMock


def test_retrieve_policy_context_keyword_fallback():
    """Test retrieval keyword fallback returns correct files."""
    from app.services.retrieval import PolicyRetriever
    
    # Create retriever and test keyword fallback directly
    retriever = PolicyRetriever()
    
    # Test refund keyword
    result = retriever._keyword_fallback("I want a refund for my order")
    assert "return_policy.md" in result["source"] or "refund" in result["content"].lower()
    
    # Test shipping keyword
    result = retriever._keyword_fallback("How long does shipping take?")
    assert "shipping_policy.md" in result["source"] or "ship" in result["content"].lower()
    
    # Test address keyword
    result = retriever._keyword_fallback("I need to change my address")
    assert "address_change_policy.md" in result["source"] or "address" in result["content"].lower()


def test_retrieve_policy_context_returns_valid_result():
    """Test retrieval returns a valid result with source and content."""
    from app.services.retrieval import retrieve_policy_context
    
    result = retrieve_policy_context("What is the refund policy?")

    assert "source" in result
    assert "content" in result
    assert len(result["content"]) > 0
