# StockTalk — B2B Inventory and Supplier Communication Platform

**B.Tech Final Year Project · Session 2026–27**  
Institute: G.L. Bajaj Institute of Technology & Management, Greater Noida  
Department: Computer Science & Engineering · Group ID: GC_2026_018

A unified B2B platform for inventory, bill scanning, nearby vendors, communication, and payments.

## Repository layout

```
StockTalk/
├── backend/              # FastAPI backend (Python)
├── docs/                 # Architecture, schema, API contracts, decisions
├── frontend/             # React + Vite + Tailwind frontend (scaffold)
├── prd.md                # Product Requirements Document
├── StockTalk_AI_Rules_and_Milestones.md  # AI usage rules + milestones
└── README.md             # this file
```

## Milestones

| Milestone | Focus | Status |
|-----------|-------|--------|
| 0 | Scope & team agreement | Done |
| 1 | Project foundation (backend skeleton, health check, DB config, tests, frontend skeleton) | Done |
| 2 | Authentication & role-based profiles (Supabase JWT, shopkeeper/vendor, business profiles) | Done |
| 3–8 | Inventory, OCR/bills, vendor discovery, chat, orders/payments, integration/QA | In backlog |

See `StockTalk_AI_Rules_and_Milestones.md` §6 for full exit criteria per milestone.

## Quick start — Backend

```bash
cd backend
cp .env.example .env   # fill in real values for Supabase / Razorpay / OCR if needed
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- Run tests: `pytest`

Backend defaults to a local SQLite DB (`stocktalk_dev.db`) so you can run without any cloud credentials. Supabase/Razorpay/OCR credentials are only needed for live external services.

## Quick start — Frontend

```bash
cd frontend
npm install
npm run dev   # Vite dev server, calls backend at VITE_API_URL
```

## Testing

Backend tests use `pytest`. Run from `backend/`:

```bash
pytest
```

## Tech stack

- **Frontend:** React 18 + Vite + Tailwind CSS
- **Backend:** Python + FastAPI
- **Database:** PostgreSQL (Supabase); SQLite for local dev/tests
- **Auth:** Supabase Auth (JWT), validated via JWKS
- **OCR:** Google Cloud Vision API
- **Payments:** Razorpay test mode
- **File storage:** Supabase Storage (private buckets)

## Conventions

- Keep `main` deployable; work on short-lived feature branches (`feat/...`, `fix/...`) and open PRs.
- Never commit `.env`, credentials, bills, or personal data. `.env.example` holds placeholder names only.
- One auth approach and one real-time approach for the MVP (Supabase Auth + Supabase Realtime).
- Validate input on the backend; verify payments server-side.

## Docs

- `docs/ARCHITECTURE.md` — components, data flow, tech choices
- `docs/DATABASE_SCHEMA.md` — tables & relationships
- `docs/API_CONTRACTS.md` — endpoints, request/response examples, error format
- `docs/DECISIONS.md` — dated decision log
