from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import app
from app import booking_routes
from app.booking_models import Base, Booking, BookingPayment, BookingRoom, Room, RoomType
from app.database import get_db


engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


class FakeOrder:
    def create(self, data):
        assert data["amount"] == 199395
        return {"id": "order_test", **data}

    def fetch(self, order_id):
        return {"id": order_id, "amount": 199395, "currency": "INR"}


class FakePayment:
    def fetch(self, payment_id):
        return {"id": payment_id, "amount": 199395, "order_id": "order_test", "status": "captured"}


class FakeUtility:
    def verify_payment_signature(self, data):
        assert data["razorpay_signature"] == "valid"


class FakeClient:
    order = FakeOrder()
    payment = FakePayment()
    utility = FakeUtility()


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def setup_function():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = TestingSession()
    now = datetime.utcnow()
    room_type = RoomType(id=1, name="Double Bed AC", total_rooms=1, room_rate=1899,
                         is_active=True, created_at=now)
    db.add(room_type)
    db.add(Room(id=1, room_number="1", room_type_id=1, is_active=True, created_at=now))
    db.commit()
    db.close()


def test_online_booking_holds_room_and_requires_full_payment(monkeypatch):
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(booking_routes, "payment_client", lambda: FakeClient())
    client = TestClient(app)
    check_in = (datetime.utcnow() + timedelta(days=1)).replace(microsecond=0)
    request = {
        "guest_name": "Akshat Guest", "mobile": "9092977055",
        "email": "guest@example.com", "room_type_id": 1,
        "check_in_at": check_in.isoformat(),
        "check_out_at": (check_in + timedelta(days=1)).isoformat(),
        "number_of_rooms": 1, "occupants_per_room": 2,
    }
    order = client.post("/api/booking/order", json=request)
    assert order.status_code == 200
    assert order.json()["amount"] == 199395
    unavailable = client.get("/api/booking/availability", params={
        "room_type_id": 1, "check_in_at": check_in.isoformat(),
        "check_out_at": (check_in + timedelta(days=1)).isoformat(),
        "number_of_rooms": 1, "occupants_per_room": 2,
    })
    assert unavailable.json()["available"] is False
    confirmation = client.post("/api/booking/confirm", json={
        "razorpay_order_id": "order_test", "razorpay_payment_id": "pay_test",
        "razorpay_signature": "valid",
    })
    assert confirmation.status_code == 200
    db = TestingSession()
    booking = db.query(Booking).one()
    assert booking.booking_source == "ONLINE"
    assert booking.status == "CONFIRMED"
    assert float(booking.advance_amount) == float(booking.total_amount) == 1993.95
    assert db.query(BookingRoom).count() == 1
    assert db.query(BookingPayment).count() == 1
    db.close()
    app.dependency_overrides.clear()
