from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.data.db import Base
from app.data.models import Order


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def sample_order(session: Session) -> Order:
    order = Order(
        order_id="ORD-000001",
        customer_email="alice@example.com",
        customer_name="Alice Nguyen",
        language_preference="en",
        status="processing",
        tracking_number="TRK100001",
        amount=35.0,
        currency="USD",
        payment_status="paid",
        refund_status="not_requested",
        refund_eligible=False,
        refund_reason="",
        shipping_address="123 Old Street, Ho Chi Minh City",
        special_handling="standard",
        address_change_allowed=True,
        risk_flag="low",
        evidence_required="none",
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order
