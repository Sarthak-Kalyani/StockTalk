# Plan: Professional B2B SaaS Authentication for StockTalk

## STATUS: COMPLETE

## Architecture decision
Kept **Supabase Auth** (existing backend `app/auth.py` verifies Supabase JWTs via JWKS). Frontend uses `@supabase/supabase-js` for email/password signup + login + password recovery, then sends the resulting access token to FastAPI via `Authorization: Bearer <token>`. Backend JWKS verification is the source of truth.

## Files changed

### Frontend (new/modified)
- `frontend/package.json` — added `@supabase/supabase-js@2.118.0`
- `frontend/.env.example` (new) — `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- `frontend/src/supabaseClient.ts` (new) — Supabase client singleton (anon key only)
- `frontend/src/auth.ts` — replaced JWT-paste flow with Supabase session management: `signIn`, `signUp`, `signOut`, `requestPasswordReset`, `getSession`, `isAuthenticated`, `onAuthStateChange`, `mapAuthUser`
- `frontend/src/services/api.ts` — attaches Bearer token from Supabase session; 401 → sign-out; `authMe`, `authProfile`, `authLogout`; re-exports `supabase`
- `frontend/src/components/FormField.tsx` (new) — accessible form field with label/input/error/password toggle
- `frontend/src/components/SignInForm.tsx` (new) — email/password sign-in with show/hide, validation, loading, error states
- `frontend/src/components/SignUpForm.tsx` (new) — full name, email, password, confirm password, business name, inline password-strength guidance, mismatch validation
- `frontend/src/components/AuthPage.tsx` (new) — split-screen desktop / single-column mobile, brand + benefits + auth card
- `frontend/src/App.tsx` — session restore from Supabase, protected dashboard, logout, /auth/me profile load, 401 handling
- `frontend/src/index.css` — B2B SaaS design tokens (indigo/navy on neutral)
- `frontend/tailwind.config.js` — design-token color/radius/shadow/font theme
- `frontend/src/Login.tsx` — DELETED (replaced by component flow)

### Backend (modified)
- `backend/app/api/auth.py` — added `POST /api/v1/auth/logout` endpoint

## Verification
- `tsc --noEmit` clean
- `npm run build` succeeds
- Backend: 13 tests pass (after clearing stale test.db)
- `http://localhost:8000/health` → 200 OK
- `http://localhost:5173/` → 200 OK
- CORS preflight from 5173 → 200 OK

## Environment variables to configure
Frontend `.env.local` (copy from `.env.example`):
- `VITE_API_URL=http://localhost:8000`
- `VITE_SUPABASE_URL=https://your-project.supabase.co`
- `VITE_SUPABASE_ANON_KEY=your-anon-public-key`

Backend `.env` (already present as `.env.example`):
- `SUPABASE_URL`, `SUPABASE_JWKS_URL`, `SUPABASE_JWT_SECRET`, `CORS_ORIGINS`

## Commands
- Backend: `docker compose up -d --build` → `http://localhost:8000`
- Frontend: `cd frontend && npm install && npm run dev` → `http://localhost:5173`
- Tests: backend `cd backend && $env:PYTHONPATH="."; pytest tests/ -q`; frontend `npm run build`

## Authentication flow
1. User signs up/signs in via Supabase Auth (email/password) — real provider, not mock
2. Supabase issues a JWT access_token (never shown to user)
3. Frontend sends it as `Authorization: Bearer <token>` to FastAPI
4. FastAPI verifies via Supabase JWKS (existing `app/auth.py`)
5. `/auth/me` returns user role/status (backend source of truth for authorization)
6. Logout clears Supabase session; 401 auto-logs out
7. Password recovery: Supabase sends reset email (`requestPasswordReset`)

## Notes
- Role selection NOT shown during registration: backend does not support user-selected roles at signup; roles are enforced server-side (`require_role` dependencies return 403)
- 8 of the pre-existing backend tests fail only when run twice without clearing `test.db` (duplicate fixed IDs) — pre-existing test-hygiene, not caused by these changes; all 13 pass on a clean DB
- Password reset email delivery requires a configured Supabase project; without one the "Forgot password" link calls a real Supabase endpoint but email delivery depends on Supabase config
