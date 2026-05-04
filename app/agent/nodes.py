from __future__ import annotations

import re
from functools import lru_cache
from time import perf_counter
from typing import Any

from langsmith.run_helpers import traceable

from app.agent.llm import generate_policy_answer, classify_intent_with_llm
from app.agent.state import SupportState
from app.core.config import get_settings
from app.services.analytics import log_conversation
from app.services.escalations import create_escalation
from app.services.orders import AddressChangeNotAllowed, get_order_by_id, update_shipping_address
from app.services.refunds import RefundDecision, process_refund_request
from app.services.retrieval import retrieve_policy_context

ORDER_ID_PATTERN = re.compile(r"(?:ORD-\d{6}|DEMO-\d{3})", re.IGNORECASE)
VIETNAMESE_MARKERS = ("cho tôi", "đơn", "hoàn tiền", "địa chỉ", "chính sách", "giao hàng")
EVIDENCE_REQUIRED_REASONS = {"damaged", "wrong_item"}

# Performance tracking
_node_timings: dict[str, list[float]] = {}


def track_performance(node_name: str):
    """Decorator to track node execution time."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = perf_counter()
            result = func(*args, **kwargs)
            elapsed = perf_counter() - start
            
            if node_name not in _node_timings:
                _node_timings[node_name] = []
            _node_timings[node_name].append(elapsed)
            
            return result
        return wrapper
    return decorator


def get_node_performance_stats() -> dict[str, dict[str, float]]:
    """Get performance statistics for all nodes."""
    stats = {}
    for node_name, timings in _node_timings.items():
        if timings:
            stats[node_name] = {
                "count": len(timings),
                "total": sum(timings),
                "avg": sum(timings) / len(timings),
                "min": min(timings),
                "max": max(timings),
            }
    return stats


@lru_cache(maxsize=1000)
def detect_language_cached(message: str) -> str:
    """Cached language detection for better performance."""
    lowered = message.lower()
    return "vi" if any(marker in lowered for marker in VIETNAMESE_MARKERS) else "en"


def detect_language(message: str) -> str:
    """Detect language with caching."""
    return detect_language_cached(message)


@lru_cache(maxsize=1000)
def classify_intent_cached(message: str) -> str:
    """Cached intent classification for better performance."""
    return _classify_intent_impl(message)


def _classify_intent_impl(message: str) -> str:
    """Internal implementation of intent classification."""
    settings = get_settings()
    
    # Use LLM-based classification if API key is available
    if settings.DEEPSEEK_API_KEY:
        try:
            return classify_intent_with_llm(message, settings.DEEPSEEK_API_KEY)
        except Exception:
            pass  # Fallback to rule-based
    
    # Rule-based fallback
    lowered = message.lower()
    if "policy" in lowered or "chính sách" in lowered:
        return "policy_question"
    if "refund" in lowered or "hoàn tiền" in lowered:
        return "refund"
    if "address" in lowered or "địa chỉ" in lowered:
        return "address_change"
    if "where is" in lowered or "track" in lowered or "ở đâu" in lowered or "vận đơn" in lowered:
        return "order_status"
    return "policy_question"


def classify_intent(message: str) -> str:
    """Classify intent using LLM if available, otherwise fallback to rules."""
    return classify_intent_cached(message)


def extract_order_id(message: str) -> str | None:
    match = ORDER_ID_PATTERN.search(message)
    return match.group(0).upper() if match else None


def extract_new_address(message: str) -> str | None:
    normalized = re.sub(r"\s+", " ", message).strip()
    patterns = [
        r"\bto\b (?P<address>.+)$",
        r"\bđến\b (?P<address>.+)$",
        r"\blà\b (?P<address>.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return match.group("address").strip()
    return None


@traceable(name="classify_node", run_type="chain")
def classify_node(state: SupportState) -> SupportState:
    """Classify node with LangSmith tracing."""
    message = state["message"]
    return {
        "language": detect_language(message),
        "intent": classify_intent(message),
        "order_id": extract_order_id(message),
        "new_address": extract_new_address(message),
        "confidence_score": 0.9,
        "resolved": False,
        "requires_human": False,
    }


@traceable(name="retrieve_policy_node", run_type="chain")
def retrieve_policy_node(state: SupportState) -> SupportState:
    """Retrieve policy node with LangSmith tracing."""
    return {"policy_context": retrieve_policy_context(state["message"])}


@traceable(name="order_status_node", run_type="chain")
def execute_order_status_node(state: SupportState) -> SupportState:
    """Order status node with LangSmith tracing."""
    session = state["db_session"]
    order_id = state.get("order_id")
    order = get_order_by_id(session, order_id) if order_id else None
    if order is None:
        return {
            "tool_used": "get_order_status",
            "response": "Please provide a valid order ID." if state["language"] == "en" else "Vui lòng cung cấp mã đơn hàng hợp lệ.",
            "resolved": False,
            "requires_human": True,
        }

    message = (
        f"Order {order.order_id} is currently {order.status}. Tracking number: {order.tracking_number}."
        if state["language"] == "en"
        else f"Đơn hàng {order.order_id} hiện ở trạng thái {order.status}. Mã vận đơn: {order.tracking_number}."
    )
    return {"tool_used": "get_order_status", "response": message, "resolved": True}


@traceable(name="refund_node", run_type="chain")
def execute_refund_node(state: SupportState) -> SupportState:
    """Refund node with LangSmith tracing."""
    session = state["db_session"]
    order_id = state.get("order_id")
    if not order_id:
        return {
            "tool_used": "process_refund",
            "response": "Please provide an order ID for the refund request."
            if state["language"] == "en"
            else "Vui lòng cung cấp mã đơn hàng để yêu cầu hoàn tiền.",
            "resolved": False,
            "requires_human": True,
        }

    order = get_order_by_id(session, order_id)
    if order is None:
        return {
            "tool_used": "process_refund",
            "response": "Order not found." if state["language"] == "en" else "Không tìm thấy đơn hàng.",
            "resolved": False,
            "requires_human": True,
        }
    required_evidence = (
        "photo_of_item"
        if order.refund_reason in EVIDENCE_REQUIRED_REASONS
        else order.evidence_required
    )
    if required_evidence != "none" and "photo" not in state["message"].lower() and "ảnh" not in state["message"].lower():
        create_escalation(
            session,
            order_id=order_id,
            intent="refund",
            reason="Evidence required before refund review",
            conversation_summary=state["message"],
            evidence_needed=required_evidence,
            sla_hours=24,
        )
        response = (
            f"Refund for {order_id} needs supporting evidence before review. Please provide a photo and a human agent will continue."
            if state["language"] == "en"
            else f"Yêu cầu hoàn tiền cho {order_id} cần bằng chứng hỗ trợ trước khi xem xét. Vui lòng gửi ảnh và nhân viên sẽ tiếp tục xử lý."
        )
        return {"tool_used": "process_refund", "response": response, "resolved": False, "requires_human": True}

    decision = process_refund_request(session, order_id, threshold=50.0)
    if decision == RefundDecision.APPROVED:
        response = (
            f"Refund for {order_id} has been approved and processed."
            if state["language"] == "en"
            else f"Yêu cầu hoàn tiền cho {order_id} đã được phê duyệt và xử lý."
        )
        return {"tool_used": "process_refund", "response": response, "resolved": True}

    if decision == RefundDecision.REQUIRES_HUMAN_APPROVAL:
        create_escalation(
            session,
            order_id=order_id,
            intent="refund",
            reason="Refund amount exceeds automatic threshold",
            conversation_summary=state["message"],
            evidence_needed=required_evidence,
            sla_hours=24,
        )
        response = (
            f"Refund for {order_id} requires human approval because the amount is above the threshold."
            if state["language"] == "en"
            else f"Yêu cầu hoàn tiền cho {order_id} cần nhân viên phê duyệt vì giá trị vượt ngưỡng tự động."
        )
        return {"tool_used": "process_refund", "response": response, "resolved": False, "requires_human": True}

    # Build detailed rejection reason - show primary reason only to avoid redundancy
    if order.status != "delivered":
        primary_reason = f"order status is '{order.status}' (only delivered orders are eligible for refund)"
    elif not order.refund_eligible:
        primary_reason = "this order is marked as not eligible for refund by our system"
    elif not order.refund_reason:
        primary_reason = "no refund reason has been specified (e.g., damaged, wrong item, missing items)"
    else:
        primary_reason = "does not meet refund policy requirements"

    if state["language"] == "en":
        response = (
            f"Refund for {order_id} is not eligible. "
            f"Reason: {primary_reason}. "
            f"Order amount: ${order.amount:.2f}, Status: {order.status}."
        )
    else:
        # Vietnamese translation of primary_reason
        if order.status != "delivered":
            vi_reason = f"trạng thái đơn hàng là '{order.status}' (chỉ đơn hàng đã giao mới được hoàn tiền)"
        elif not order.refund_eligible:
            vi_reason = "đơn hàng này không đủ điều kiện hoàn tiền theo hệ thống"
        elif not order.refund_reason:
            vi_reason = "chưa có lý do hoàn tiền (ví dụ: hỏng, sai hàng, thiếu hàng)"
        else:
            vi_reason = "không đáp ứng yêu cầu chính sách hoàn tiền"
        
        response = (
            f"Yêu cầu hoàn tiền cho {order_id} không đủ điều kiện. "
            f"Lý do: {vi_reason}. "
            f"Giá trị đơn hàng: ${order.amount:.2f}, Trạng thái: {order.status}."
        )
    return {"tool_used": "process_refund", "response": response, "resolved": False}


@traceable(name="address_change_node", run_type="chain")
def execute_address_change_node(state: SupportState) -> SupportState:
    """Address change node with LangSmith tracing."""
    session = state["db_session"]
    order_id = state.get("order_id")
    new_address = state.get("new_address")
    if not order_id or not new_address:
        return {
            "tool_used": "update_shipping_address",
            "response": "Please provide both an order ID and a full replacement address."
            if state["language"] == "en"
            else "Vui lòng cung cấp cả mã đơn hàng và địa chỉ thay thế đầy đủ.",
            "resolved": False,
            "requires_human": True,
        }

    try:
        updated = update_shipping_address(session, order_id, new_address)
    except AddressChangeNotAllowed:
        create_escalation(
            session,
            order_id=order_id,
            intent="address_change",
            reason="Address change not allowed for current order state",
            conversation_summary=state["message"],
            evidence_needed="none",
            sla_hours=12,
        )
        response = (
            f"Address change for {order_id} requires human support because the order can no longer be edited."
            if state["language"] == "en"
            else f"Yêu cầu đổi địa chỉ cho {order_id} cần nhân viên hỗ trợ vì đơn hàng không còn có thể chỉnh sửa."
        )
        return {"tool_used": "update_shipping_address", "response": response, "resolved": False, "requires_human": True}

    response = (
        f"Shipping address for {updated.order_id} has been updated to: {updated.shipping_address}."
        if state["language"] == "en"
        else f"Địa chỉ giao hàng của {updated.order_id} đã được cập nhật thành: {updated.shipping_address}."
    )
    return {"tool_used": "update_shipping_address", "response": response, "resolved": True}


@traceable(name="policy_node", run_type="chain")
def execute_policy_node(state: SupportState) -> SupportState:
    """Policy node with LangSmith tracing.
    
    CRITICAL FIX: Properly extract language-specific content from bilingual files.
    Handles various file formats:
    - Format 1: # Title\n## English\n...\n## Vietnamese\n...
    - Format 2: # Title\n...\n## Vietnamese\n...
    """
    context = state["policy_context"] or {"content": "", "source": "unknown"}
    settings = get_settings()
    
    # Properly extract language-specific sections
    content = context["content"]
    
    # Try different section extraction methods
    if "## Vietnamese" in content:
        # Split on Vietnamese section
        parts = content.split("## Vietnamese")
        english_part = parts[0]
        vietnamese_part = parts[1] if len(parts) > 1 else ""
        
        # Clean up English section - remove "## English" header if present
        if "## English" in english_part:
            english_parts = english_part.split("## English")
            # Take content after "## English" header
            english_text = english_parts[1].strip() if len(english_parts) > 1 else english_part.strip()
        else:
            english_text = english_part.strip()
        
        vietnamese_text = vietnamese_part.strip()
    elif "## English" in content:
        # Only English section
        english_parts = content.split("## English")
        english_text = english_parts[1].strip() if len(english_parts) > 1 else content.strip()
        vietnamese_text = english_text  # Fallback to English
    else:
        # No language sections - use full content for both
        english_text = content.strip()
        vietnamese_text = content.strip()
    
    # Select appropriate language content
    selected_context = english_text if state["language"] == "en" else vietnamese_text
    
    response = generate_policy_answer(
        question=state["message"],
        policy_context=selected_context,
        language=state["language"],
        api_key=settings.DEEPSEEK_API_KEY,
    )
    return {"tool_used": "retrieve_policy_context", "response": response, "resolved": True}


@traceable(name="log_node", run_type="chain")
def log_node(state: SupportState) -> SupportState:
    """Log node with LangSmith tracing."""
    session = state["db_session"]
    started_at = perf_counter()
    log_conversation(
        session,
        conversation_id=state["conversation_id"],
        user_message=state["message"],
        detected_language=state["language"],
        intent=state["intent"],
        resolved=state["resolved"],
        tool_used=state["tool_used"],
        confidence_score=state["confidence_score"],
        human_intervention_required=state["requires_human"],
        latency_ms=int((perf_counter() - started_at) * 1000),
    )
    return {}
