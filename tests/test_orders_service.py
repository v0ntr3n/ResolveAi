import pytest

from app.services.orders import AddressChangeNotAllowed, get_order_by_id, update_shipping_address


def test_get_order_by_id_returns_matching_order(session, sample_order):
    order = get_order_by_id(session, "ORD-000001")

    assert order is not None
    assert order.customer_name == "Alice Nguyen"


def test_update_shipping_address_changes_processing_order(session, sample_order):
    updated = update_shipping_address(session, "ORD-000001", "456 New Street, Hanoi")

    assert updated.shipping_address == "456 New Street, Hanoi"


def test_update_shipping_address_rejects_shipped_order(session, sample_order):
    sample_order.status = "shipped"
    session.add(sample_order)
    session.commit()

    with pytest.raises(AddressChangeNotAllowed):
        update_shipping_address(session, "ORD-000001", "456 New Street, Hanoi")


def test_update_shipping_address_rejects_risky_order(session, sample_order):
    sample_order.risk_flag = "high"
    sample_order.address_change_allowed = False
    session.add(sample_order)
    session.commit()

    with pytest.raises(AddressChangeNotAllowed):
        update_shipping_address(session, "ORD-000001", "456 New Street, Hanoi")
