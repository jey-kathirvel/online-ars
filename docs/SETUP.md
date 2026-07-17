# Local setup

## Prerequisites

- Python 3.12+
- PostgreSQL 16 when testing shared inventory
- Git
- Razorpay test account for payment-flow testing

## Installation

```powershell
git clone https://github.com/jey-kathirvel/online-ars.git
cd online-ars
git switch develop
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `DATABASE_URL` to the ADS ERP database when integration testing. SQLite may be used for page-only development, but it does not validate ERP synchronization.

```powershell
python -m uvicorn app:app --reload
python -m pytest -q
```

## Razorpay

Use credentials whose key begins with `rzp_test_`. Restart the application after changing `.env`. Never paste the secret into logs, screenshots, documentation or Git.

## Shared database expectations

The ADS ERP migrations must be at the Phase 2 Alembic head before this application is started against production. Room types and rooms are managed in ERP; this application reads them and creates online bookings, room allocations and captured-payment records.
