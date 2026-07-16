from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_public_pages_render() -> None:
    for path in ["/", "/rooms", "/book", "/explore", "/contact"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "Akshat Royal Stay" in response.text

def test_partner_booking_reference_is_removed() -> None:
    for path in ["/", "/rooms", "/book", "/explore", "/contact"]:
        assert "booking.akshatroyalstay.in" not in client.get(path).text
