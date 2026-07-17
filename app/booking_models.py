from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RoomType(Base):
    __tablename__ = "room_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    total_rooms: Mapped[int] = mapped_column(Integer)
    room_rate: Mapped[float] = mapped_column(Numeric(12, 2))
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Room(Base):
    __tablename__ = "rooms"
    id: Mapped[int] = mapped_column(primary_key=True)
    room_number: Mapped[str] = mapped_column(String(20))
    room_type_id: Mapped[int] = mapped_column(ForeignKey("room_types.id"))
    is_active: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_no: Mapped[str] = mapped_column(String(30), unique=True)
    guest_name: Mapped[str] = mapped_column(String(150))
    mobile: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(254))
    check_in_at: Mapped[datetime] = mapped_column(DateTime)
    check_out_at: Mapped[datetime] = mapped_column(DateTime)
    number_of_days: Mapped[int] = mapped_column(Integer)
    room_type_id: Mapped[int] = mapped_column(ForeignKey("room_types.id"))
    number_of_rooms: Mapped[int] = mapped_column(Integer)
    room_rate: Mapped[float] = mapped_column(Numeric(12, 2))
    subtotal_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    gst_percent: Mapped[float] = mapped_column(Numeric(5, 2))
    gst_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    advance_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    payment_mode: Mapped[str | None] = mapped_column(String(50))
    booking_source: Mapped[str] = mapped_column(String(20))
    payment_expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    provider_order_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    status: Mapped[str] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)


class BookingRoom(Base):
    __tablename__ = "booking_rooms"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    status: Mapped[str] = mapped_column(String(30))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class BookingPayment(Base):
    __tablename__ = "booking_payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True)
    provider: Mapped[str] = mapped_column(String(30))
    provider_order_id: Mapped[str] = mapped_column(String(100), unique=True)
    provider_payment_id: Mapped[str] = mapped_column(String(100), unique=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DateTime)
