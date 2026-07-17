from datetime import datetime

from app.booking_service import calculate_checkout, calculate_price, calculate_stay_days


def test_checkout_uses_exact_24_hour_blocks():
    check_in = datetime(2026, 8, 1, 14, 30)
    assert calculate_checkout(check_in, 2) == datetime(2026, 8, 3, 14, 30)


def test_full_price_includes_five_percent_gst():
    subtotal, extra, gst, total = calculate_price(1899, 1, 2, 5)
    assert str(subtotal) == "3798.00"
    assert str(extra) == "0.00"
    assert str(gst) == "189.90"
    assert str(total) == "3987.90"


def test_checkout_rounds_up_to_billed_24_hour_days():
    check_in = datetime(2026, 8, 1, 14, 0)
    assert calculate_stay_days(check_in, datetime(2026, 8, 2, 14, 0)) == 1
    assert calculate_stay_days(check_in, datetime(2026, 8, 2, 14, 15)) == 2


def test_extra_occupant_is_charged_per_room_per_day_before_gst():
    subtotal, extra, gst, total = calculate_price(1899, 2, 2, 5, 3, 500)
    assert str(extra) == "2000.00"
    assert str(subtotal) == "9596.00"
    assert str(gst) == "479.80"
    assert str(total) == "10075.80"
