from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.data.db import Base
from app.data.models import Order
from app.data.seed import seed_orders


def test_seed_orders_creates_expected_rows():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        seed_orders(session, total_orders=25, seed=7)
        count = session.scalar(select(func.count()).select_from(Order))
        assert count == 25

        first_order = session.scalars(select(Order).limit(1)).first()
        assert first_order is not None
        assert first_order.order_id.startswith("ORD-")
        assert first_order.language_preference in {"en", "vi"}
        assert first_order.special_handling in {"standard", "fragile", "restricted_air"}
        assert isinstance(first_order.address_change_allowed, bool)
