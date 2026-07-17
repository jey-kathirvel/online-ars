from datetime import datetime, timedelta
from uuid import uuid4

import razorpay
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from razorpay.errors import SignatureVerificationError
from sqlalchemy.orm import Session

from .booking_models import Booking, BookingPayment, BookingRoom, RoomType
from .booking_service import (
    available_rooms, calculate_price, calculate_stay_days, lock_room_type,
    release_expired_holds,
)
from .config import get_settings
from .database import get_db
from .email_service import BookingEmail, send_booking_confirmation


router = APIRouter(prefix="/api/booking", tags=["booking"])
settings = get_settings()


class BookingRequest(BaseModel):
    guest_name: str = Field(min_length=2, max_length=150)
    mobile: str
    email: str = Field(max_length=254)
    room_type_id: int = Field(gt=0)
    check_in_at: datetime
    check_out_at: datetime
    number_of_rooms: int = Field(ge=1, le=5)
    occupants_per_room: int = Field(ge=1, le=3)

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, value: str) -> str:
        value = value.strip()
        if len(value) != 10 or not value.isdigit():
            raise ValueError("Enter a valid 10-digit mobile number")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address")
        return value


class ConfirmationRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


def payment_client():
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(503, "Online payment is temporarily unavailable")
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


def get_active_room_type(db: Session, room_type_id: int):
    room_type = db.query(RoomType).filter(
        RoomType.id == room_type_id, RoomType.is_active.is_(True)
    ).first()
    if room_type is None:
        raise HTTPException(404, "Room type not found")
    return room_type


@router.get("/availability")
def availability(room_type_id: int, check_in_at: datetime, check_out_at: datetime,
                 number_of_rooms: int = 1, occupants_per_room: int = 2,
                 db: Session = Depends(get_db)):
    if not 1 <= number_of_rooms <= 5 or not 1 <= occupants_per_room <= 3:
        raise HTTPException(400, "Invalid stay details")
    if check_in_at < datetime.utcnow() - timedelta(minutes=5):
        raise HTTPException(400, "Check-in must be in the future")
    try:
        number_of_days = calculate_stay_days(check_in_at, check_out_at)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    room_type = get_active_room_type(db, room_type_id)
    rooms = available_rooms(db, room_type_id, check_in_at, check_out_at)
    subtotal, extra_charge, gst, total = calculate_price(
        room_type.room_rate, number_of_rooms, number_of_days, settings.booking_gst_percent,
        occupants_per_room, settings.extra_occupant_rate,
    )
    return {
        "available": len(rooms) >= number_of_rooms,
        "available_count": len(rooms),
        "check_out_at": check_out_at.isoformat(), "number_of_days": number_of_days,
        "room_rate": float(room_type.room_rate),
        "subtotal": float(subtotal), "extra_occupant_charge": float(extra_charge),
        "gst_percent": settings.booking_gst_percent,
        "gst_amount": float(gst), "total": float(total),
    }


@router.get("/calendar")
def booking_calendar(
    room_type_id: int,
    start_date: str | None = None,
    days: int = 30,
    stay_days: int = 1,
    check_in_time: str = "12:00",
    number_of_rooms: int = 1,
    db: Session = Depends(get_db),
):
    if not 1 <= days <= 365:
        raise HTTPException(
            400,
            "Calendar range must be between 1 and 365 days",
        )

    if not 1 <= stay_days <= 30:
        raise HTTPException(
            400,
            "Stay duration must be between 1 and 30 days",
        )

    if not 1 <= number_of_rooms <= 5:
        raise HTTPException(
            400,
            "Number of rooms must be between 1 and 5",
        )

    try:
        calendar_start = (
            datetime.strptime(start_date, "%Y-%m-%d").date()
            if start_date
            else datetime.utcnow().date()
        )
    except ValueError as exc:
        raise HTTPException(
            400,
            "Start date must use YYYY-MM-DD format",
        ) from exc

    try:
        arrival_time = datetime.strptime(
            check_in_time,
            "%H:%M",
        ).time()
    except ValueError as exc:
        raise HTTPException(
            400,
            "Check-in time must use HH:MM format",
        ) from exc

    room_type = get_active_room_type(
        db,
        room_type_id,
    )

    inventory = []
    disabled_dates = []
    next_available_date = None

    for offset in range(days):
        current_date = calendar_start + timedelta(days=offset)

        check_in_at = datetime.combine(
            current_date,
            arrival_time,
        )

        check_out_at = check_in_at + timedelta(
            days=stay_days,
        )

        rooms = available_rooms(
            db,
            room_type_id,
            check_in_at,
            check_out_at,
        )

        available_count = len(rooms)
        is_available = available_count >= number_of_rooms
        date_value = current_date.isoformat()

        inventory.append({
            "date": date_value,
            "available": is_available,
            "available_count": available_count,
        })

        if not is_available:
            disabled_dates.append(date_value)
        elif next_available_date is None:
            next_available_date = date_value

    return {
        "room_type_id": room_type.id,
        "room_type": room_type.name,
        "start_date": calendar_start.isoformat(),
        "days": days,
        "stay_days": stay_days,
        "check_in_time": check_in_time,
        "number_of_rooms": number_of_rooms,
        "disabled_dates": disabled_dates,
        "next_available_date": next_available_date,
        "inventory": inventory,
    }


@router.post("/order")
def create_order(payload: BookingRequest, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    if payload.check_in_at < now - timedelta(minutes=5):
        raise HTTPException(400, "Check-in must be in the future")
    try:
        number_of_days = calculate_stay_days(payload.check_in_at, payload.check_out_at)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    lock_room_type(db, payload.room_type_id)
    release_expired_holds(db)
    room_type = get_active_room_type(db, payload.room_type_id)
    rooms = available_rooms(db, payload.room_type_id, payload.check_in_at, payload.check_out_at)
    if len(rooms) < payload.number_of_rooms:
        raise HTTPException(409, "The requested room is no longer available")
    selected = rooms[:payload.number_of_rooms]
    subtotal, extra_charge, gst, total = calculate_price(
        room_type.room_rate, payload.number_of_rooms, number_of_days,
        settings.booking_gst_percent, payload.occupants_per_room,
        settings.extra_occupant_rate,
    )
    amount_paise = round(float(total) * 100)
    try:
        order = payment_client().order.create({
            "amount": amount_paise, "currency": "INR",
            "receipt": f"online-{uuid4().hex[:24]}",
            "notes": {"purpose": "online_hotel_booking"},
        })
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, "Unable to start payment") from exc
    expires_at = now + timedelta(minutes=settings.booking_hold_minutes)
    booking = Booking(
        booking_no="ON-" + now.strftime("%Y%m%d%H%M%S") + uuid4().hex[:5].upper(),
        guest_name=payload.guest_name.strip(), mobile=payload.mobile, email=payload.email,
        check_in_at=payload.check_in_at, check_out_at=payload.check_out_at,
        number_of_days=number_of_days, room_type_id=payload.room_type_id,
        number_of_rooms=payload.number_of_rooms, room_rate=room_type.room_rate,
        subtotal_amount=subtotal, gst_percent=settings.booking_gst_percent, gst_amount=gst,
        total_amount=total, advance_amount=0, payment_mode="RAZORPAY",
        booking_source="ONLINE", payment_expires_at=expires_at,
        provider_order_id=order["id"], status="RESERVED",
        notes=(f"Occupants per room: {payload.occupants_per_room}; "
               f"extra occupant charge: {extra_charge}"),
        created_at=now, updated_at=now,
    )
    db.add(booking)
    db.flush()
    for room in selected:
        db.add(BookingRoom(booking_id=booking.id, room_id=room.id, status="ACTIVE",
                           cancelled_at=None, cancellation_reason=None, created_at=now))
    db.commit()
    return {
        "key_id": settings.razorpay_key_id, "order_id": order["id"],
        "amount": amount_paise, "currency": "INR", "expires_at": expires_at.isoformat(),
        "booking_no": booking.booking_no,
    }


@router.post("/confirm")
def confirm_payment(payload: ConfirmationRequest, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(
        Booking.provider_order_id == payload.razorpay_order_id,
        Booking.booking_source == "ONLINE",
    ).with_for_update().first()
    if booking is None:
        raise HTTPException(404, "Booking hold not found")
    existing = db.query(BookingPayment).filter(
        BookingPayment.provider_payment_id == payload.razorpay_payment_id
    ).first()
    if existing:
        return {"booking_no": booking.booking_no, "status": "CONFIRMED"}
    if booking.status != "RESERVED" or not booking.payment_expires_at or booking.payment_expires_at <= datetime.utcnow():
        raise HTTPException(409, "The room hold has expired; please contact us with your payment ID")
    client = payment_client()
    try:
        client.utility.verify_payment_signature(payload.model_dump())
        order = client.order.fetch(payload.razorpay_order_id)
        payment = client.payment.fetch(payload.razorpay_payment_id)
    except SignatureVerificationError as exc:
        raise HTTPException(400, "Payment verification failed") from exc
    except Exception as exc:
        raise HTTPException(502, "Unable to verify payment") from exc
    expected = round(float(booking.total_amount) * 100)
    if (order.get("amount") != expected or order.get("currency") != "INR"
            or payment.get("amount") != expected
            or payment.get("order_id") != payload.razorpay_order_id
            or payment.get("status") != "captured"):
        raise HTTPException(400, "Payment is not captured or the full amount was not paid")
    now = datetime.utcnow()
    booking.status = "CONFIRMED"
    booking.advance_amount = booking.total_amount
    booking.payment_expires_at = None
    booking.updated_at = now
    db.add(BookingPayment(
        booking_id=booking.id, provider="RAZORPAY",
        provider_order_id=payload.razorpay_order_id,
        provider_payment_id=payload.razorpay_payment_id,
        amount=booking.total_amount, currency="INR", status="CAPTURED", created_at=now,
    ))
    db.commit()
    send_booking_confirmation(BookingEmail(
        recipient=booking.email or "", guest_name=booking.guest_name,
        booking_no=booking.booking_no, room_type=get_active_room_type(db, booking.room_type_id).name,
        check_in_at=booking.check_in_at, check_out_at=booking.check_out_at,
        number_of_rooms=booking.number_of_rooms, number_of_days=booking.number_of_days,
        subtotal_amount=booking.subtotal_amount, gst_amount=booking.gst_amount,
        total_amount=booking.total_amount, paid_amount=booking.total_amount,
        payment_mode="Razorpay", payment_id=payload.razorpay_payment_id,
    ))
    return {"booking_no": booking.booking_no, "status": "CONFIRMED"}
