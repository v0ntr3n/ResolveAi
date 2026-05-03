from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.models import Order
from app.services.cache import get_order_cache

EDITABLE_STATUSES = {"pending", "processing"}


class AddressChangeNotAllowed(Exception):
    """Raised when an order can no longer be modified."""


def get_order_by_id(session: Session, order_id: str, use_cache: bool = True) -> Order | None:
    """Get order by ID with optional caching."""
    cache = get_order_cache()
    
    # Query database first (we need the actual session-bound object for modifications)
    order = session.scalar(select(Order).where(Order.order_id == order_id))
    
    # Cache result for future reads
    if use_cache and order:
        cache.set_order(order_id, {
            "order_id": order.order_id,
            "customer_email": order.customer_email,
            "customer_name": order.customer_name,
            "status": order.status,
            "tracking_number": order.tracking_number,
            "amount": order.amount,
            "currency": order.currency,
            "payment_status": order.payment_status,
            "refund_status": order.refund_status,
            "refund_eligible": order.refund_eligible,
            "refund_reason": order.refund_reason,
            "shipping_address": order.shipping_address,
            "address_change_allowed": order.address_change_allowed,
            "risk_flag": order.risk_flag,
            "evidence_required": order.evidence_required,
        })
    
    return order


def update_shipping_address(session: Session, order_id: str, new_address: str) -> Order:
    """Update shipping address and invalidate cache."""
    cache = get_order_cache()
    
    order = get_order_by_id(session, order_id, use_cache=False)
    if order is None:
        raise AddressChangeNotAllowed("Order not found")
    if order.status not in EDITABLE_STATUSES or not order.address_change_allowed or order.risk_flag == "high":
        raise AddressChangeNotAllowed("Order is no longer eligible for address changes")

    order.shipping_address = new_address
    session.add(order)
    session.commit()
    session.refresh(order)
    
    # Invalidate cache
    cache.invalidate_order(order_id)
    
    return order
