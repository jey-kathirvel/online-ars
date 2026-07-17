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


def test_active_test_room_type_appears_in_public_dropdown():
    app.dependency_overrides[get_db] = override_db
    db = TestingSession()
    now = datetime.utcnow()
    db.add(RoomType(id=2, name="E2E Test Room", total_rooms=1, room_rate=5,
                    is_active=True, created_at=now))
    db.add(Room(id=2, room_number="TEST-01", room_type_id=2,
                is_active=True, created_at=now))
    db.commit()
    db.close()

    response = TestClient(app).get("/book")

    assert response.status_code == 200
    assert "E2E Test Room" in response.text
    assert "5.0/night" in response.text
    check_in = (datetime.utcnow() + timedelta(days=2)).replace(microsecond=0)
    availability = TestClient(app).get("/api/booking/availability", params={
        "room_type_id": 2,
        "check_in_at": check_in.isoformat(),
        "check_out_at": (check_in + timedelta(days=1)).isoformat(),
        "number_of_rooms": 1,
        "occupants_per_room": 2,
    })
    assert availability.status_code == 200
    assert availability.json()["total"] == 5.25
    app.dependency_overrides.clear()


def test_booking_calendar_returns_sold_out_and_next_available_date(monkeypatch):
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(
        booking_routes,
        "payment_client",
        lambda: FakeClient(),
    )

    client = TestClient(app)

    check_in = (
        datetime.utcnow() + timedelta(days=3)
    ).replace(
        hour=10,
        minute=0,
        second=0,
        microsecond=0,
    )

    order_response = client.post(
        "/api/booking/order",
        json={
            "guest_name": "Calendar Test Guest",
            "mobile": "9092977055",
            "email": "calendar@example.com",
            "room_type_id": 1,
            "check_in_at": check_in.isoformat(),
            "check_out_at": (
                check_in + timedelta(days=1)
            ).isoformat(),
            "number_of_rooms": 1,
            "occupants_per_room": 2,
        },
    )

    assert order_response.status_code == 200

    calendar_response = client.get(
        "/api/booking/calendar",
        params={
            "room_type_id": 1,
            "start_date": check_in.date().isoformat(),
            "days": 3,
            "stay_days": 1,
            "check_in_time": "10:00",
            "number_of_rooms": 1,
        },
    )

    assert calendar_response.status_code == 200

    result = calendar_response.json()

    sold_out_date = check_in.date().isoformat()
    next_date = (
        check_in.date() + timedelta(days=1)
    ).isoformat()

    assert sold_out_date in result["disabled_dates"]
    assert result["next_available_date"] == next_date

    assert result["inventory"][0] == {
        "date": sold_out_date,
        "available": False,
        "available_count": 0,
    }

    assert result["inventory"][1] == {
        "date": next_date,
        "available": True,
        "available_count": 1,
    }

    app.dependency_overrides.clear()


def test_booking_calendar_rejects_invalid_room_type():
    app.dependency_overrides[get_db] = override_db

    response = TestClient(app).get(
        "/api/booking/calendar",
        params={
            "room_type_id": 99999,
            "days": 30,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Room type not found"

    app.dependency_overrides.clear()


def test_booking_calendar_validates_calendar_range():
    app.dependency_overrides[get_db] = override_db

    response = TestClient(app).get(
        "/api/booking/calendar",
        params={
            "room_type_id": 1,
            "days": 366,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Calendar range must be between 1 and 365 days"
    )

    app.dependency_overrides.clear()
