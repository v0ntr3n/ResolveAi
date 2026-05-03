from sqlalchemy.orm import Session

from app.data.models import Escalation


def create_escalation(
    session: Session,
    order_id: str | None,
    intent: str,
    reason: str,
    conversation_summary: str,
    evidence_needed: str = "none",
    sla_hours: int = 24,
    review_notes: str = "",
) -> Escalation:
    escalation = Escalation(
        order_id=order_id,
        intent=intent,
        reason=reason,
        conversation_summary=conversation_summary,
        evidence_needed=evidence_needed,
        sla_hours=sla_hours,
        review_notes=review_notes,
    )
    session.add(escalation)
    session.commit()
    session.refresh(escalation)
    return escalation
