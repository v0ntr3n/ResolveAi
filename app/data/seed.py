from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from faker import Faker
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.data.db import Base
from app.data.models import Order

ORDER_STATUSES = ["pending", "processing", "shipped", "out_for_delivery", "delivered"]
PAYMENT_STATUSES = ["paid", "paid", "paid", "failed"]
REFUND_REASONS = ["", "", "damaged", "wrong_item", "missing_items", "not_received"]
SPECIAL_HANDLING = ["standard", "standard", "fragile", "restricted_air"]
RISK_FLAGS = ["low", "low", "low", "medium", "high"]


def _build_order(fake: Faker, rng: random.Random, index: int) -> Order:
    status = rng.choice(ORDER_STATUSES)
    amount = round(rng.uniform(12.0, 180.0), 2)
    created_at = datetime.now(UTC) - timedelta(days=rng.randint(1, 30))
    refund_eligible = status == "delivered" and amount <= 120
    refund_reason = rng.choice(REFUND_REASONS) if refund_eligible else ""
    special_handling = rng.choice(SPECIAL_HANDLING)
    risk_flag = rng.choice(RISK_FLAGS)
    address_change_allowed = status in {"pending", "processing"} and risk_flag != "high"
    evidence_required = "photo_of_item" if refund_reason in {"damaged", "wrong_item"} else "none"
    return Order(
        order_id=f"ORD-{index:06d}",
        customer_email=fake.email(),
        customer_name=fake.name(),
        language_preference=rng.choice(["en", "vi"]),
        status=status,
        tracking_number=f"TRK{rng.randint(100000, 999999)}",
        created_at=created_at,
        updated_at=created_at,
        amount=amount,
        currency="USD",
        payment_status=rng.choice(PAYMENT_STATUSES),
        refund_status="not_requested",
        refund_eligible=refund_eligible,
        refund_reason=refund_reason,
        shipping_address=fake.address(),
        special_handling=special_handling,
        address_change_allowed=address_change_allowed,
        risk_flag=risk_flag,
        evidence_required=evidence_required,
    )


def seed_orders(session: Session, total_orders: int = 1000, seed: int = 42) -> None:
    # Check if ORD-* orders already exist
    existing_order = session.scalar(select(Order.id).where(Order.order_id.like("ORD-%")).limit(1))
    if existing_order is not None:
        return

    fake = Faker()
    Faker.seed(seed)
    rng = random.Random(seed)

    orders = [_build_order(fake, rng, index) for index in range(1, total_orders + 1)]
    session.add_all(orders)
    session.commit()


def main() -> None:
    settings = get_settings()
    database_url = settings.DATABASE_URL
    if database_url.startswith("sqlite:///./"):
        database_url = database_url.replace("sqlite:///./", "sqlite:///")
    engine = create_engine(database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_orders(session)


if __name__ == "__main__":
    main()
