"""Property-based tests for intent classification using Hypothesis."""

from hypothesis import given, strategies as st, settings

from app.agent.nodes import classify_intent, detect_language


# Define strategies for generating test data
message_strategy = st.text(min_size=1, max_size=500)
order_id_strategy = st.from_regex(r"ORD-\d{6}")


@given(message=message_strategy)
@settings(deadline=None, max_examples=50)
def test_classify_intent_always_returns_valid_intent(message):
    """Property: Classification always returns a valid intent."""
    result = classify_intent(message)
    assert result in {"order_status", "refund", "address_change", "policy_question"}


@given(message=message_strategy)
def test_language_detection_is_deterministic(message):
    """Property: Language detection is deterministic."""
    result1 = detect_language(message)
    result2 = detect_language(message)
    assert result1 == result2
    assert result1 in {"en", "vi"}


@given(message=st.text(min_size=1, max_size=100))
def test_language_detection_returns_valid_code(message):
    """Property: Language detection always returns valid language code."""
    result = detect_language(message)
    assert result in {"en", "vi"}


# Test with Vietnamese markers
@given(prefix=st.text(min_size=0, max_size=50))
def test_vietnamese_detection_with_markers(prefix):
    """Property: Messages with Vietnamese markers are detected as Vietnamese."""
    vietnamese_markers = ["cho tôi", "đơn", "hoàn tiền", "địa chỉ", "chính sách", "giao hàng"]
    for marker in vietnamese_markers:
        message = f"{prefix} {marker} {prefix}"
        result = detect_language(message)
        assert result == "vi"


# Test with English keywords
@given(prefix=st.text(min_size=0, max_size=50, alphabet=st.characters(whitelist_categories=('Ll', 'Lu'))))
def test_english_detection_no_vietnamese_markers(prefix):
    """Property: Messages without Vietnamese markers are detected as English."""
    # Generate message without Vietnamese markers
    message = prefix.lower()
    # Skip if empty
    if not message.strip():
        return
    # If message doesn't contain Vietnamese markers, should be English
    vietnamese_markers = ("cho tôi", "đơn", "hoàn tiền", "địa chỉ", "chính sách", "giao hàng")
    if not any(marker in message for marker in vietnamese_markers):
        result = detect_language(message)
        assert result == "en"
