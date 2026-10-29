# StockTalk Backend

FastAPI backend for the StockTalk B2B Inventory and Supplier Communication Platform.

## Prerequisites

- Python 3.10+
- `pip`

## Setup

```bash
# From the backend directory
cp .env.example .env
# Fill in values as needed. Local dev uses SQLite by default; Supabase/Razorpay/OCR
# credentials are only needed for live external services.

pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

- Health check: `http://localhost:8000/health`
- Interactive API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Run tests

```bash
pytest
```

Tests use a local SQLite file (`test.db`) and mock Supabase JWT verification, so no cloud account is required.

## Configuration

All settings come from `.env` (loaded via `pydantic-settings`). See `.env.example` for the full list:

| Variable | Purpose | Default |
|----------|---------|---------|
| `DATABASE_URL` | DB connection string | `sqlite:///./stocktalk_dev.db` |
| `SUPABASE_URL` / `SUPABASE_JWT_SECRET` / `SUPABASE_JWKS_URL` | Supabase Auth | (empty) |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Razorpay test mode | (empty) |
| `GOOGLE_CLOUD_VISION_CREDENTIALS` | OCR credentials | (empty) |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173,http://localhost:3000` |

Never commit `.env`. It is covered by `.gitignore`.

## Project structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py          # pydantic-settings based config
│   ├── database.py        # SQLAlchemy engine, SessionLocal, init_db
│   ├── main.py            # FastAPI app, routers, lifespan
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── auth.py            # Supabase JWT verification + role dependencies
│   ├── utils/responses.py # Response envelope helpers (data/meta, error)
│   └── api/               # route modules (auth, inventory, bills, vendors, chat, orders, payments, dashboard)
├── tests/                 # pytest suite
├── requirements.txt
├── pytest.ini
└── .env.example
```

## Milestones

- **M1 (foundation):** backend skeleton, health check, DB config, `.env.example`, tests — Done
- **M2 (auth/profiles):** Supabase JWT auth, shopkeeper/vendor roles, business profiles, protected routes — Done

See `StockTalk_AI_Rules_and_Milestones.md` §6 in the repo root for full exit criteria.
