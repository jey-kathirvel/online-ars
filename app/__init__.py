from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import get_settings
from .booking_routes import router as booking_router


BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(booking_router)
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

    common = {
        "settings": settings,
        "phone_display": "+91 90929 77055",
        "whatsapp_url": (
            "https://wa.me/919092977055?text=Hello%20Akshat%20Royal%20Stay!%20"
            "I%20would%20like%20to%20book%20a%20room."
        ),
    }

    def render(request: Request, template: str, **context: object) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name=template,
            context={**common, **context},
        )

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request) -> HTMLResponse:
        return render(request, "home.html", active="home", title="A warm stay at the gateway to the hills")

    @app.get("/rooms", response_class=HTMLResponse)
    async def rooms(request: Request) -> HTMLResponse:
        return render(request, "rooms.html", active="rooms", title="Rooms & rates")

    @app.get("/book", response_class=HTMLResponse)
    async def book(request: Request) -> HTMLResponse:
        return render(
            request, "book.html", active="book", title="Book your stay",
            room_types=(
                {"id": 1, "name": "AC Double Room", "rate": 1899},
                {"id": 2, "name": "Non-AC Double Room", "rate": 1499},
                {"id": 3, "name": "Non-AC Single Room", "rate": 1099},
            ),
        )

    @app.get("/booking/confirmed", response_class=HTMLResponse)
    async def booking_confirmed(request: Request, booking_no: str = "") -> HTMLResponse:
        return render(
            request, "booking_confirmed.html", active="book",
            title="Booking confirmed", booking_no=booking_no[:30],
        )

    @app.get("/explore", response_class=HTMLResponse)
    async def explore(request: Request) -> HTMLResponse:
        return render(request, "explore.html", active="explore", title="Explore from Bodinayakanur")

    @app.get("/contact", response_class=HTMLResponse)
    async def contact(request: Request) -> HTMLResponse:
        return render(request, "contact.html", active="contact", title="Contact Akshat Royal Stay")

    @app.get("/terms", response_class=HTMLResponse)
    async def terms(request: Request) -> HTMLResponse:
        return render(request, "terms.html", active="", title="Terms & conditions")

    @app.get("/refund-policy", response_class=HTMLResponse)
    async def refund_policy(request: Request) -> HTMLResponse:
        return render(request, "refund_policy.html", active="", title="Cancellation & refund policy")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
