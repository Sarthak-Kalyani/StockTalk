# StockTalk Decision Log

**Version:** 1.0  
**Purpose:** Record dated architectural, technical, and scope decisions for team alignment and future reference.

---

## Decision Template

Each entry should follow this format:

```
## YYYY-MM-DD: Short Title

**Context:** What situation prompted this decision?

**Options Considered:**
1. Option A — pros/cons
2. Option B — pros/cons
3. Option C — pros/cons

**Decision:** What was chosen.

**Rationale:** Why this option over others.

**Implications:** Follow-up work, migrations, breaking changes.

**Related:** Links to PRD sections, issues, PRs, other decisions.
```

---

## 2026-10-29: Authentication Approach — Supabase Auth with JWT

**Context:** Need to choose authentication for MVP. PRD recommends "Supabase Auth or secure JWT-based authentication; choose one approach."

**Options Considered:**
1. **Supabase Auth (chosen)** — Managed auth, built-in email/password, OAuth, MFA, JWT tokens, RLS integration
2. **Custom JWT (FastAPI + PyJWT)** — Full control, but build/maintain registration, login, password reset, email verification
3. **Firebase Auth** — Good but separate from Supabase stack
4. **Auth0** — Enterprise-grade, overkill and cost for student project

**Decision:** Use **Supabase Auth** for authentication, with FastAPI validating Supabase-issued JWTs via JWKS.

**Rationale:**
- Single vendor (Supabase) for auth + database + storage + realtime
- JWT validation is standard; FastAPI middleware can verify via Supabase JWKS endpoint
- Row Level Security (RLS) policies work natively with Supabase Auth UIDs
- Team already using Supabase for PostgreSQL and Storage
- Reduces custom auth code to maintain

**Implications:**
- Frontend uses Supabase JS client for signup/login
- Backend needs JWT verification middleware (JWKS caching)
- User table stores `supabase_uid` to link with `auth.users`
- RLS policies use `auth.uid()` for data isolation
- No password hashing in backend — Supabase handles it

**Related:** PRD §7, §5.1; ARCHITECTURE.md §3.1; DATABASE_SCHEMA.md §2.1

---

## 2026-10-29: Database — PostgreSQL on Supabase (Not Self-Hosted)

**Context:** PRD recommends "PostgreSQL (managed through Supabase if desired)."

**Options Considered:**
1. **Supabase Managed PostgreSQL (chosen)** — Free tier, built-in auth, storage, realtime, dashboard
2. **Self-hosted PostgreSQL (Docker/Railway/Render)** — Full control, but ops burden
3. **Neon / PlanetScale** — Serverless, but separate from auth/storage
4. **SQLite (dev only)** — Current backend uses this, not production-ready

**Decision:** Use **Supabase Managed PostgreSQL** for development and demo deployment.

**Rationale:**
- Unified platform: Auth + DB + Storage + Realtime + Edge Functions
- Free tier sufficient for student project (500MB DB, 1GB storage, 2M realtime messages)
- SQL dashboard for debugging
- Easy RLS policy management
- PostGIS extension available for vendor proximity

**Implications:**
- All team members connect to same Supabase project (or local via Supabase CLI)
- Migrations via Supabase CLI or Alembic
- Environment variables for `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`

**Related:** PRD §7; ARCHITECTURE.md §2, §7

---

## 2026-10-29: OCR Provider — Google Cloud Vision API

**Context:** PRD lists "Google Cloud Vision API; Tesseract as alternative."

**Options Considered:**
1. **Google Cloud Vision API (chosen)** — High accuracy, multi-language, structured output, generous free tier (1000 units/month)
2. **Tesseract (self-hosted)** — Free, open-source, but lower accuracy on complex invoices, needs preprocessing
3. **AWS Textract** — Good but separate AWS account
4. **Azure Form Recognizer** — Good but separate Azure account

**Decision:** Use **Google Cloud Vision API** for MVP. Keep Tesseract as fallback for local development without cloud credentials.

**Rationale:**
- Best accuracy for Indian invoice formats (GST, Hindi/English mixed)
- Structured `textAnnotations` + `fullTextAnnotation` with bounding boxes
- Easy integration via `google-cloud-vision` Python library
- Free tier covers demo needs
- Can swap adapter later if needed

**Implications:**
- Backend needs `GOOGLE_APPLICATION_CREDENTIALS` or API key
- OCR adapter pattern: `OCRProvider` interface with `GoogleVisionOCR` and `TesseractOCR` implementations
- Bill upload → Storage → OCR async job → Review screen

**Related:** PRD §5.3, §7, §13; ARCHITECTURE.md §3.3

---

## 2026-10-29: File Storage — Supabase Storage (Private Buckets)

**Context:** PRD recommends "Supabase Storage or equivalent private object storage."

**Options Considered:**
1. **Supabase Storage (chosen)** — Integrated with Supabase Auth, RLS on buckets, signed URLs, free tier (1GB)
2. **AWS S3** — Industry standard, but separate credentials, no native RLS
3. **Cloudflare R2** — Cheap, S3-compatible, but separate
4. **Local filesystem** — Dev only, not deployable

**Decision:** Use **Supabase Storage** with private buckets and signed URLs.

**Rationale:**
- Same project as Auth + DB — unified permissions
- RLS policies on storage objects (bucket policies)
- Signed URLs with expiry for secure file access
- Automatic CDN via Supabase
- Supports images, PDFs, documents

**Implications:**
- Buckets: `bills` (private), `chat-attachments` (private), `catalogue-images` (public or private)
- Backend generates signed URLs for frontend access
- Frontend uploads directly to Supabase Storage (client-side) or via backend proxy
- File validation (type, size) on both client and server

**Related:** PRD §5.3, §5.6, §7; ARCHITECTURE.md §3.3, §3.5

---

## 2026-10-29: Realtime Chat — Supabase Realtime

**Context:** PRD lists "Supabase Realtime or FastAPI WebSockets; choose one for MVP."

**Options Considered:**
1. **Supabase Realtime (chosen)** — Built on PostgreSQL replication, auto-scales, integrates with RLS, no separate WebSocket server
2. **FastAPI WebSockets** — Custom implementation, need to manage connections, scaling, auth
3. **Pusher / Ably** — Managed WebSocket, but extra cost/vendor
4. **Socket.io + Redis** — Self-hosted, complex

**Decision:** Use **Supabase Realtime** for chat message updates.

**Rationale:**
- Zero infrastructure: subscribes to PostgreSQL `INSERT` on `messages` table
- RLS ensures users only subscribe to their conversations
- Frontend uses `@supabase/supabase-js` `channel.on('postgres_changes', ...)`
- Falls back to polling if WebSocket fails
- Less backend code to maintain

**Implications:**
- Backend only handles REST API for messages (CRUD)
- Frontend subscribes to realtime on conversation open
- Need to enable Replication for `messages` table in Supabase dashboard
- Message `is_read` updates via REST, not realtime

**Related:** PRD §5.6, §7; ARCHITECTURE.md §3.5

---

## 2026-10-29: Payment Provider — Razorpay Test Mode

**Context:** PRD recommends "Razorpay test mode, subject to available UPI/payment support."

**Options Considered:**
1. **Razorpay Test Mode (chosen)** — Indian market focus, UPI/Card/NetBanking, easy test mode, webhooks, student-friendly
2. **Stripe Test Mode** — Global, but limited UPI support in test, INR not primary
3. **Cashfree / PayU** — Indian alternatives, but Razorpay has better docs/community
4. **Mock Payment (no provider)** — Simpler but less realistic demo

**Decision:** Use **Razorpay Test Mode** for payment integration.

**Rationale:**
- Native UPI support (critical for Indian B2B)
- Test mode works without KYC (test card numbers, test UPI)
- Webhook verification with signature
- Good Python SDK (`razorpay`)
- Team may have prior exposure

**Implications:**
- Backend creates Razorpay Order → frontend opens checkout → webhook verifies
- `payments` table stores provider refs, webhook payload for audit
- **Never trust frontend success** — always verify server-side via webhook
- Test mode clearly labeled in UI

**Related:** PRD §5.7, §7, §11, §13; ARCHITECTURE.md §3.6

---

## 2026-10-29: Nearby Search — PostGIS on Supabase

**Context:** PRD recommends "PostgreSQL location fields; PostGIS if proximity queries require it."

**Options Considered:**
1. **PostGIS on Supabase (chosen)** — Native geospatial queries, `ST_DWithin`, `ST_Distance`, GiST indexes, free on Supabase
2. **Haversine in SQL (current backend)** — Works for small datasets, no index support, slower at scale
3. **Application-level filtering** — Fetch all, filter in Python — not scalable
4. **Elasticsearch / Meilisearch** — Overkill, separate service

**Decision:** Enable **PostGIS extension** on Supabase and use `geography` type for vendor locations.

**Rationale:**
- Supabase supports PostGIS out of the box
- `ST_DWithin(geom, point, radius_meters)` uses GiST index — fast at scale
- `geography` type handles meters/degrees correctly (vs `geometry` planar)
- Can still fallback to manual city search when GPS denied
- Future: polygon search for service areas

**Implications:**
- Migration: `ALTER TABLE vendor_locations ADD COLUMN geom geography(POINT);`
- Index: `CREATE INDEX idx_vendor_locations_geom ON vendor_locations USING GIST (geom);`
- Query: `SELECT * FROM vendor_locations WHERE ST_DWithin(geom, ST_MakePoint(lon, lat)::geography, radius_meters);`
- Backend updates `geom` column on location save

**Related:** PRD §5.4, §7, §13; ARCHITECTURE.md §3.4; DATABASE_SCHEMA.md §2.4

---

## 2026-10-29: Cost Price Method — Weighted Average Cost (WAC)

**Context:** PRD §5.2: "Calculate stock value using a clearly defined cost-price method." Need to pick one for MVP.

**Options Considered:**
1. **Weighted Average Cost - WAC (chosen)** — Smooths price fluctuations, GAAP-compliant, single cost per product
2. **FIFO (First In, First Out)** — More accurate for perishables, but complex (track lots)
3. **LIFO** — Not IFRS compliant, rarely used in India
4. **Moving Average** — Similar to WAC but per time window
5. **Standard Cost** — Fixed, requires variance analysis

**Decision:** Use **Weighted Average Cost (WAC)** per product per business.

**Rationale:**
- Simple: `new_cost = (old_qty * old_cost + new_qty * new_cost) / (old_qty + new_qty)`
- Single `cost_price` column on `products` table
- Works for non-perishable and perishable goods
- Easy to explain in demo
- Price history (`price_records`) still tracks individual purchase prices for comparison

**Implications:**
- On bill confirmation: recalculate WAC for each product
- `cost_price` on `products` = current WAC
- `price_records` preserves each purchase price for history/comparison
- Selling price independent (set by shopkeeper)

**Related:** PRD §5.2, §5.5; DATABASE_SCHEMA.md §2.1, §2.3

---

## 2026-10-29: Duplicate Bill Detection — Vendor + Invoice Number + Date

**Context:** PRD §5.3: "Detect likely duplicate bills using vendor/invoice number and other available fields; do not silently apply the same bill twice."

**Options Considered:**
1. **Unique constraint on (vendor_id, invoice_number, invoice_date) (chosen)** — Database-level guarantee, simple
2. **Fuzzy matching (vendor + date + amount + line items)** — Catches OCR errors, but complex, false positives
3. **Content hash of bill file** — Catches exact re-upload, misses same bill different scan
4. **ML-based duplicate detection** — Overkill for MVP

**Decision:** **Database unique constraint** on `(vendor_id, invoice_number, invoice_date)` + application-level warning for near-matches.

**Rationale:**
- Invoice number + date is standard business key
- Unique constraint prevents duplicate confirmation at DB level (race-safe)
- Near-match detection: same vendor, similar amount, same day → show warning in review screen
- Simple to implement and explain

**Implications:**
- `purchase_bills` table: `UNIQUE (vendor_id, invoice_number, invoice_date)`
- On confirm: catch `IntegrityError` → return `409 CONFLICT` with existing bill ID
- Review screen: query for similar bills, show "Possible duplicate" banner

**Related:** PRD §5.3, §11, §13; ARCHITECTURE.md §3.3

---

## 2026-10-29: Frontend Framework — React + Vite + Tailwind CSS

**Context:** PRD §7 recommends "React.js + Tailwind CSS."

**Options Considered:**
1. **React + Vite + Tailwind (chosen)** — Standard, fast HMR, small bundle, team familiarity
2. **Next.js** — SSR/SSG, but overkill for dashboard-heavy app, adds complexity
3. **Vue 3 + Vite + Tailwind** — Good alternative, but team knows React
4. **SvelteKit** — Lightweight, but smaller ecosystem

**Decision:** **React 18 + Vite + Tailwind CSS** with TypeScript.

**Rationale:**
- Matches PRD recommendation exactly
- Vite: fast dev server, optimized builds
- Tailwind: rapid UI, consistent design system, small CSS
- TypeScript: type safety for API contracts
- Component libraries: `shadcn/ui` (Radix + Tailwind) for accessible components

**Implications:**
- Project structure: `frontend/src/{components,pages,hooks,services,types,utils}`
- API client: generated from OpenAPI spec or manual `fetch` wrapper
- State: React Query (TanStack Query) for server state, Zustand for client state
- Routing: React Router v6
- Forms: React Hook Form + Zod validation
- Charts: Recharts (per PRD)

**Related:** PRD §7; ARCHITECTURE.md §2

---

## 2026-10-29: API Documentation — OpenAPI/Swagger via FastAPI

**Context:** Need API contracts documented and testable.

**Options Considered:**
1. **FastAPI auto OpenAPI (chosen)** — Built-in, always in sync, Swagger UI at `/docs`, ReDoc at `/redoc`
2. **Postman Collection only** — Good for testing, but not source of truth
3. **Separate OpenAPI YAML** — Drifts from code
4. **GraphQL** — Not needed, REST sufficient

**Decision:** Use **FastAPI's automatic OpenAPI generation** as single source of truth. Export to Postman for testing.

**Rationale:**
- Zero maintenance — decorators define schema
- Interactive Swagger UI for manual testing
- Can generate TypeScript types for frontend (`openapi-typescript`)
- Postman can import OpenAPI JSON for collection
- CI can validate breaking changes

**Implications:**
- All endpoints use Pydantic models for request/response
- Tags for grouping in Swagger UI
- Examples in `Field(..., examples=[...])`
- Deprecation via `deprecated=True` in route decorator

**Related:** PRD §7, §10; ARCHITECTURE.md §5; API_CONTRACTS.md

---

## 2026-10-29: Testing Strategy — pytest + Postman

**Context:** PRD §7 lists "Postman, Git, GitHub — API checks, source control, and team collaboration."

**Options Considered:**
1. **pytest (backend) + Postman (API) + Vitest (frontend) (chosen)** — Layered testing
2. **Only Postman** — No unit tests, hard to catch regressions
3. **Only pytest** — No contract testing against running API
4. **Playwright/Cypress (E2E)** — Add later for critical flows

**Decision:** **pytest for unit/integration, Postman for API contract testing, Vitest for frontend components.**

**Rationale:**
- pytest: Fast, fixtures, parametrize, covers business logic, DB transactions
- Postman: Collection runs in CI, validates API contracts, team collaboration
- Vitest: Vite-native, fast, React Testing Library for components
- GitHub Actions runs all on PR

**Implications:**
- Backend: `tests/unit/`, `tests/integration/`, `conftest.py` with test DB
- Postman: Collection per module, environment variables for URLs
- Frontend: `src/**/*.test.tsx` with Vitest + RTL
- Coverage target: 80% backend, 60% frontend

**Related:** PRD §7, §10, §14; ARCHITECTURE.md

---

## 2026-10-29: Deployment — Vercel (FE) + Render (BE) + Supabase

**Context:** PRD §7 recommends "Vercel for frontend; Render/Railway for API; managed PostgreSQL/storage."

**Options Considered:**
1. **Vercel + Render + Supabase (chosen)** — Free tiers, GitHub integration, custom domains
2. **Vercel + Railway + Supabase** — Similar, Railway sometimes cheaper
3. **Netlify + Fly.io + Supabase** — Good alternatives
4. **All on Supabase (Edge Functions)** — Limited for FastAPI

**Decision:** **Vercel (Frontend) + Render (Backend) + Supabase (DB/Auth/Storage/Realtime)**

**Rationale:**
- Vercel: Best React/Vite deployment, preview deployments per PR
- Render: Free tier for web services (spins down), Docker support, auto-deploy
- Supabase: Already chosen for backend services
- All connect to GitHub for CI/CD

**Implications:**
- Frontend build: `npm run build` → `dist/` → Vercel
- Backend: Dockerfile → Render (or native Python)
- Environment variables in each platform dashboard
- Supabase project linked to both

**Related:** PRD §7, §10; ARCHITECTURE.md §7

---

*Add new decisions above this line. Keep chronological order (newest first).*