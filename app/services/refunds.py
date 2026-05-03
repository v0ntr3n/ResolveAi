from enum import StrEnum

from sqlalchemy.orm import Session

from app.services.orders import get_order_by_id


class RefundDecision(StrEnum):
    APPROVED = "approved"
    REQUIRES_HUMAN_APPROVAL = "requires_human_approval"
    REJECTED = "rejected"


def process_refund_request(session: Session, order_id: str, threshold: float) -> RefundDecision:
    order = get_order_by_id(session, order_id)
    if order is None:
        return RefundDecision.REJECTED
    if not order.refund_eligible or order.status != "delivered":
        return RefundDecision.REJECTED
    if not order.refund_reason:
        return RefundDecision.REJECTED
    if order.amount > threshold or order.risk_flag in {"medium", "high"}:
        return RefundDecision.REQUIRES_HUMAN_APPROVAL

    order.refund_status = "refunded"
    session.commit()
    return RefundDecision.APPROVED
