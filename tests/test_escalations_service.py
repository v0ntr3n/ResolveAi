from app.services.escalations import create_escalation


def test_create_escalation_persists_record(session):
    escalation = create_escalation(
        session,
        order_id="ORD-000001",
        intent="refund",
        reason="Refund above threshold",
        conversation_summary="Customer requested a 95 USD refund.",
        evidence_needed="photo_of_item",
        sla_hours=24,
    )

    assert escalation.id is not None
    assert escalation.status == "open"
    assert escalation.evidence_needed == "photo_of_item"
    assert escalation.sla_hours == 24
