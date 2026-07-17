from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from .booking_models import Booking, BookingRoom, Room


ACTIVE_STATUSES = ("RESERVED", "CONFIRMED", "CHECKED_IN")


def calculate_checkout(check_in: datetime, days: int) -> datetime:
    if days < 1:
        raise ValueError("Stay must be at least one day")
    return check_in + timedelta(hours=24 * days)


def calculate_price(rate, rooms: int, days: int, gst_percent: float):
    subtotal = (Decimal(str(rate)) * rooms * days).quantize(Decimal("0.01"))
    gst = (subtotal * Decimal(str(gst_percent)) / 100).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return subtotal, gst, subtotal + gst


def lock_room_type(db: Session, room_type_id: int) -> None:
    if db.bind and db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 800000 + room_type_id})


def release_expired_holds(db: Session) -> None:
    now = datetime.utcnow()
    expired = db.query(Booking).filter(
        Booking.status == "RESERVED",
        Booking.booking_source == "ONLINE",
        Booking.payment_expires_at.isnot(None),
        Booking.payment_expires_at <= now,
    ).all()
    for booking in expired:
        booking.status = "CANCELLED"
        booking.updated_at = now
        db.query(BookingRoom).filter(BookingRoom.booking_id == booking.id).update(
            {BookingRoom.status: "CANCELLED", BookingRoom.cancelled_at: now,
             BookingRoom.cancellation_reason: "Online payment window expired"},
            synchronize_session=False,
        )


def available_rooms(db: Session, room_type_id: int, check_in: datetime, check_out: datetime):
    occupied = db.query(BookingRoom.room_id).join(
        Booking, Booking.id == BookingRoom.booking_id
    ).filter(
        Booking.status.in_(ACTIVE_STATUSES),
        BookingRoom.status == "ACTIVE",
        or_(
            Booking.status != "RESERVED",
            Booking.payment_expires_at.is_(None),
            Booking.payment_expires_at > datetime.utcnow(),
        ),
        Booking.check_in_at < check_out,
        Booking.check_out_at > check_in,
    )
    return db.query(Room).filter(
        Room.room_type_id == room_type_id,
        Room.is_active.is_(True),
        ~Room.id.in_(occupied),
    ).order_by(Room.id).all()
