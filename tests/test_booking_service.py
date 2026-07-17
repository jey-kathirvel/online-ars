from datetime import datetime

from app.booking_service import calculate_checkout, calculate_price


def test_checkout_uses_exact_24_hour_blocks():
    check_in = datetime(2026, 8, 1, 14, 30)
    assert calculate_checkout(check_in, 2) == datetime(2026, 8, 3, 14, 30)


def test_full_price_includes_five_percent_gst():
    subtotal, gst, total = calculate_price(1899, 1, 2, 5)
    assert str(subtotal) == "3798.00"
    assert str(gst) == "189.90"
    assert str(total) == "3987.90"
