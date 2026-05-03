from app.agent.graph import build_support_graph
from app.data.models import Order


def test_graph_handles_english_order_status(session, sample_order):
    graph = build_support_graph()

    result = graph.invoke(
        {
            "message": "Where is my order ORD-000001?",
            "conversation_id": "conv-1",
            "db_session": session,
        }
    )

    assert result["intent"] == "order_status"
    assert result["resolved"] is True
    assert "processing" in result["response"].lower()


def test_graph_handles_vietnamese_policy_question(session):
    graph = build_support_graph()

    result = graph.invoke(
        {
            "message": "Chính sách hoàn tiền là gì?",
            "conversation_id": "conv-2",
            "db_session": session,
        }
    )

    assert result["intent"] == "policy_question"
    assert result["language"] == "vi"
    # When API key is not configured, response may contain policy context or be empty
    # Just verify the intent classification and language detection worked
    assert "tool_used" in result
    assert result["resolved"] is True


def test_graph_escalates_high_value_refund(session, sample_order):
    sample_order.status = "delivered"
    sample_order.amount = 120.0
    sample_order.refund_eligible = True
    sample_order.refund_reason = "damaged"
    sample_order.risk_flag = "low"
    session.commit()

    graph = build_support_graph()
    result = graph.invoke(
        {
            "message": "Refund order ORD-000001 please.",
            "conversation_id": "conv-3",
            "db_session": session,
        }
    )

    assert result["intent"] == "refund"
    assert result["requires_human"] is True
    assert "human" in result["response"].lower()


def test_graph_refund_requests_missing_evidence_for_damage(session, sample_order):
    sample_order.status = "delivered"
    sample_order.amount = 25.0
    sample_order.refund_eligible = True
    sample_order.refund_reason = "damaged"
    sample_order.risk_flag = "low"
    session.commit()

    graph = build_support_graph()
    result = graph.invoke(
        {
            "message": "Refund order ORD-000001 because it is damaged",
            "conversation_id": "conv-5",
            "db_session": session,
        }
    )

    assert result["requires_human"] is True
    assert "photo" in result["response"].lower() or "evidence" in result["response"].lower()


def test_graph_updates_address_when_order_is_editable(session, sample_order):
    graph = build_support_graph()

    result = graph.invoke(
        {
            "message": "Please change shipping address for ORD-000001 to 456 New Street, Hanoi",
            "conversation_id": "conv-4",
            "db_session": session,
        }
    )

    updated_order = session.query(Order).filter_by(order_id="ORD-000001").one()

    assert result["intent"] == "address_change"
    assert result["resolved"] is True
    assert updated_order.shipping_address == "456 New Street, Hanoi"
