from app.services.refunds import RefundDecision, process_refund_request


def test_process_refund_request_auto_refunds_eligible_order(session, sample_order):
    sample_order.status = "delivered"
    sample_order.amount = 25.0
    sample_order.refund_eligible = True
    sample_order.refund_reason = "damaged"
    sample_order.risk_flag = "low"
    session.add(sample_order)
    session.commit()

    decision = process_refund_request(session, "ORD-000001", threshold=50.0)

    assert decision == RefundDecision.APPROVED


def test_process_refund_request_escalates_high_value_order(session, sample_order):
    sample_order.status = "delivered"
    sample_order.amount = 95.0
    sample_order.refund_eligible = True
    sample_order.refund_reason = "missing_items"
    sample_order.risk_flag = "low"
    session.commit()

    decision = process_refund_request(session, "ORD-000001", threshold=50.0)

    assert decision == RefundDecision.REQUIRES_HUMAN_APPROVAL


def test_process_refund_request_escalates_risky_order(session, sample_order):
    sample_order.status = "delivered"
    sample_order.amount = 25.0
    sample_order.refund_eligible = True
    sample_order.refund_reason = "damaged"
    sample_order.risk_flag = "high"
    session.commit()

    decision = process_refund_request(session, "ORD-000001", threshold=50.0)

    assert decision == RefundDecision.REQUIRES_HUMAN_APPROVAL


def test_process_refund_request_rejects_missing_reason(session, sample_order):
    sample_order.status = "delivered"
    sample_order.amount = 25.0
    sample_order.refund_eligible = True
    sample_order.refund_reason = ""
    sample_order.risk_flag = "low"
    session.commit()

    decision = process_refund_request(session, "ORD-000001", threshold=50.0)

    assert decision == RefundDecision.REJECTED
