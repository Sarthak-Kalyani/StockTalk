# StockTalk — B2B Inventory and Supplier Communication Platform

**B.Tech Final Year Project · Session 2026–27**  
Institute: G.L. Bajaj Institute of Technology & Management, Greater Noida  
Department: Computer Science & Engineering · Group ID: GC_2026_018

A unified B2B platform for inventory, bill scanning, nearby vendors, communication, and payments.

## Repository layout

```
StockTalk/
├── backend/              # Express.js + TypeScript backend (Node.js)
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
| 2 | Authentication & role-based profiles (Express JWT, shopkeeper/vendor, business profiles, SQLite) | Done |
| 3–8 | Inventory, OCR/bills, vendor discovery, chat, orders/payments, integration/QA | In backlog |

See `StockTalk_AI_Rules_and_Milestones.md` §6 for full exit criteria per milestone.

## Quick start — Backend (Express.js + TypeScript + SQLite)

```powershell
cd backend
cp .env.example .env   # edit JWT_SECRET for production
npm install
npm run dev            # tsx watch on http://localhost:8000
```

Or build and run the production server:

```powershell
cd backend
npm run build
npm start
```

- Health check: `http://localhost:8000/health`
- Auth: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`

Backend uses a local SQLite database persisted in `backend/data/`.

### Docker

```powershell
# From the repo root
docker-compose up --build
```

## Quick start — Frontend

```powershell
cd frontend
npm install
npm run dev   # Vite dev server, calls backend at VITE_API_URL (default http://localhost:8000)
```

## Testing

The Express backend has no Python test suite. Type-check with:

```powershell
cd backend
npx tsc --noEmit
```

## Tech stack

- **Frontend:** React 19 + Vite + Tailwind CSS
- **Backend:** Node.js + Express.js + TypeScript
- **Database:** SQLite (via better-sqlite3)
- **Auth:** Local JWT authentication (bcryptjs password hashing + jsonwebtoken)
- **Payments:** Razorpay test mode (planned)
- **File storage:** Local (planned: Supabase Storage)

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
