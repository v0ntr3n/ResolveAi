from app.services.analytics import aggregate_metrics, log_conversation


def test_aggregate_metrics_counts_resolved_and_escalated(session):
    log_conversation(
        session,
        conversation_id="c1",
        user_message="Where is my order?",
        detected_language="en",
        intent="order_status",
        resolved=True,
        tool_used="get_order_status",
        confidence_score=0.91,
        human_intervention_required=False,
        latency_ms=300,
    )
    log_conversation(
        session,
        conversation_id="c2",
        user_message="Refund order ORD-000001",
        detected_language="en",
        intent="refund",
        resolved=False,
        tool_used="process_refund",
        confidence_score=0.88,
        human_intervention_required=True,
        latency_ms=450,
    )

    metrics = aggregate_metrics(session)

    assert metrics["total_conversations"] == 2
    assert metrics["resolved_count"] == 1
    assert metrics["escalation_count"] == 1
