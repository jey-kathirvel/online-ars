# Akshat Royal Stay Online

Public hotel website and full-payment online booking application for [online.akshatroyalstay.in](https://online.akshatroyalstay.in). It shares room inventory with ADS ERP so staff and online bookings cannot allocate the same room for overlapping dates.

## Highlights

- Responsive peacock-themed hotel website with optimized room and destination photography.
- Public booking form displayed in a modal iframe from `/book?embed=1`.
- Live room availability from the shared ADS ERP PostgreSQL database.
- Explicit check-in/check-out date and 12-hour AM/PM time selection.
- One to five rooms; maximum three occupants per room.
- Two occupants included; third occupant costs ₹500 per room per billed day, plus GST.
- Exact 24-hour billing blocks; partial blocks round up to the next billed day.
- Full Razorpay payment only for online bookings.
- Ten-minute room hold while online payment is pending.
- Payment signature, captured amount, currency and order ownership verification.
- Online bookings recorded with `booking_source=ONLINE` for ERP reporting.

## Technology

- Python 3.12, FastAPI, Jinja2 and SQLAlchemy
- PostgreSQL in production; SQLite is supported for local presentation testing
- Razorpay Checkout
- Gunicorn with Uvicorn workers
- Apache reverse proxy and systemd on Ubuntu 24.04

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`. Run tests with:

```powershell
python -m pytest -q
```

## Configuration

Create `.env` from `.env.example`. Never commit `.env`, database passwords or Razorpay credentials.

Important settings:

| Variable | Purpose |
|---|---|
| `APP_ENV` | `development`, `test` or `production` |
| `APP_URL` | Public application URL |
| `DATABASE_URL` | Shared ADS ERP PostgreSQL connection URL |
| `RAZORPAY_KEY_ID` | Razorpay test/live public key |
| `RAZORPAY_KEY_SECRET` | Razorpay secret |
| `BOOKING_GST_PERCENT` | GST percentage; currently `5` |
| `BOOKING_HOLD_MINUTES` | Payment hold duration; currently `10` |
| `EXTRA_OCCUPANT_RATE` | Third-occupant rate per room/day; currently `500` |

The application must be restarted after `.env` changes.

## Documentation

- [Detailed setup](docs/SETUP.md)
- [VPS deployment and rollback](docs/DEPLOYMENT.md)
- [Booking and payment flow](docs/BOOKING_FLOW.md)
- [Testing checklist](docs/TESTING.md)

## Branch workflow

```text
feature branch → develop → VPS testing → main
```

Use `develop` for integration testing. Promote to `main` only after online booking, ERP synchronization and Razorpay test-mode verification succeed.

## Security

- Do not log or display Razorpay secrets.
- Do not commit `.env`.
- Rotate any credential shared through an insecure channel.
- Use Razorpay test keys until acceptance testing is complete.
- Back up PostgreSQL before migrations or production releases.

## Repository

[github.com/jey-kathirvel/online-ars](https://github.com/jey-kathirvel/online-ars)

## Phase 3: booking confirmation email

After a Razorpay payment is captured in full, the public booking service sends a branded HTML confirmation to the guest. The message includes the booking reference, stay dates, room and tax totals, captured payment reference, embedded peacock logo, and the cancellation/refund policy. Email delivery failure is logged and does not roll back a confirmed payment.

Configure Hostinger SMTP in `.env` using the variables documented in `.env.example`. Create the `akshatroyalstay@ads-ai.in` mailbox first and set `SMTP_PASSWORD` to its mailbox password. Never commit the password. Restart `online-ars.service` after changing `.env`.

Public policy pages are available at `/terms` and `/refund-policy`. Review the operating policy with the property owner before production launch.
