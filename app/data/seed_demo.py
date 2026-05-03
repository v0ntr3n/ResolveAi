#!/usr/bin/env python3
"""Seed demo orders for testing ResolveAI customer support system.

This script loads predefined demo orders from data/demo_orders.json
into the database for testing various scenarios.

Usage:
    python -m app.data.seed_demo

Scenarios covered:
    - Standard delivered orders (refund eligible)
    - Damaged items requiring photo evidence
    - Pending orders (address change allowed)
    - High value orders (not auto-refund eligible)
    - High risk orders (manual review required)
    - Vietnamese language customers
    - Failed payment scenarios
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.data.db import Base
from app.data.models import Order


def load_demo_orders() -> list[dict]:
    """Load demo orders from JSON file."""
    demo_path = Path(__file__).parent.parent.parent / "data" / "demo_orders.json"
    with open(demo_path) as f:
        data = json.load(f)
    return data.get("orders", [])


def create_order_from_dict(order_data: dict) -> Order:
    """Create an Order model instance from dictionary data."""
    return Order(
        order_id=order_data["order_id"],
        customer_email=order_data["customer_email"],
        customer_name=order_data["customer_name"],
        language_preference=order_data.get("language_preference", "en"),
        status=order_data["status"],
        tracking_number=order_data["tracking_number"],
        amount=order_data["amount"],
        currency=order_data.get("currency", "USD"),
        payment_status=order_data.get("payment_status", "paid"),
        refund_status=order_data.get("refund_status", "not_requested"),
        refund_eligible=order_data.get("refund_eligible", False),
        refund_reason=order_data.get("refund_reason", ""),
        shipping_address=order_data["shipping_address"],
        special_handling=order_data.get("special_handling", "standard"),
        address_change_allowed=order_data.get("address_change_allowed", False),
        risk_flag=order_data.get("risk_flag", "low"),
        evidence_required=order_data.get("evidence_required", "none"),
    )


def seed_demo_orders(session: Session, clear_existing: bool = False) -> int:
    """Seed demo orders into the database.
    
    Args:
        session: SQLAlchemy session
        clear_existing: If True, delete existing DEMO-* orders first
        
    Returns:
        Number of orders seeded
    """
    if clear_existing:
        # Delete existing demo orders
        session.execute(
            Order.__table__.delete().where(Order.order_id.like("DEMO-%"))
        )
        session.commit()
    else:
        # Check if demo orders already exist
        existing = session.scalar(
            select(Order.id).where(Order.order_id == "DEMO-001")
        )
        if existing is not None:
            print("Demo orders already exist. Use clear_existing=True to reseed.")
            return 0
    
    demo_orders_data = load_demo_orders()
    orders = [create_order_from_dict(data) for data in demo_orders_data]
    
    session.add_all(orders)
    session.commit()
    
    return len(orders)


def main() -> None:
    """Main entry point for seeding demo orders."""
    settings = get_settings()
    database_url = settings.DATABASE_URL
    
    # Handle SQLite relative path
    if database_url.startswith("sqlite:///./"):
        database_url = database_url.replace("sqlite:///./", "sqlite:///")
    
    engine = create_engine(database_url)
    
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    
    with Session(engine) as session:
        count = seed_demo_orders(session, clear_existing=True)
        print(f"Successfully seeded {count} demo orders")
        
        # Print summary
        print("\nDemo Orders Summary:")
        print("=" * 60)
        orders = session.scalars(
            select(Order).where(Order.order_id.like("DEMO-%")).order_by(Order.order_id)
        ).all()
        
        for order in orders:
            status_markers = {
                "pending": "[PENDING]",
                "processing": "[PROCESSING]",
                "shipped": "[SHIPPED]",
                "out_for_delivery": "[OUT FOR DELIVERY]",
                "delivered": "[DELIVERED]",
            }
            marker = status_markers.get(order.status, "[UNKNOWN]")
            refund_marker = " [REFUND OK]" if order.refund_eligible else ""
            address_marker = " [ADDR OK]" if order.address_change_allowed else ""
            lang_marker = " VI" if order.language_preference == "vi" else " EN"
            
            print(
                f"{marker} {order.order_id}: {order.status.title()} | "
                f"${order.amount:.2f} |{lang_marker} |"
                f"{refund_marker}{address_marker}"
            )


if __name__ == "__main__":
    main()
