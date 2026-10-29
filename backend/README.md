# StockTalk Backend

Express.js + TypeScript backend with JWT-based local authentication and SQLite persistence for the StockTalk B2B Inventory and Supplier Communication Platform.

## Tech Stack

- **Runtime:** Node.js 20
- **Framework:** Express.js 4
- **Language:** TypeScript
- **Database:** SQLite (via `better-sqlite3`)
- **Auth:** bcryptjs password hashing + jsonwebtoken (JWT)
- **Validation:** express-validator

## Project Structure

```
backend/
├── src/
│   ├── index.ts              # App entry point: Express server, CORS, routes, health
│   ├── config.ts             # Environment configuration
│   ├── database.ts           # SQLite connection + schema initialization
│   ├── controllers/
│   │   └── authController.ts # register / login / logout / me / profile handlers
│   ├── middleware/
│   │   ├── auth.ts           # JWT verification + role-based access control
│   │   ├── error.ts          # Centralized error handler
│   │   └── validate.ts       # express-validator result handler
│   └── routes/
│       └── auth.ts           # /api/auth routes (register, login, logout, me, profile)
├── data/                     # SQLite database files (created at runtime, gitignored)
├── dist/                     # Compiled TypeScript output (gitignored)
├── package.json
├── tsconfig.json
├── Dockerfile
├── .env                      # Local environment (copy from .env.example, gitignored)
├── .env.example
└── .gitignore
```

## API Endpoints

### Auth
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/auth/register` | Create account + business profile | None |
| POST | `/api/auth/login` | Sign in, returns JWT access_token | None |
| POST | `/api/auth/logout` | Client clears token (stateless) | Required |
| GET | `/api/auth/me` | Current user info | Required |
| GET | `/api/auth/me/profile` | Current business profile | Required |
| PATCH | `/api/auth/me/profile` | Update business profile | Required |
| POST | `/api/auth/me/profile/complete` | Complete profile setup | Required |

### Health
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/health` | Health check | None |

## Setup

### Local development

```powershell
# From the backend directory
cp .env.example .env
# Edit .env if needed (JWT_SECRET should be changed for production)

# Install dependencies
npm install

# Run in development (watch mode)
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The server listens on `http://localhost:8000` by default (override with `PORT`).

### Docker

```powershell
# From the repo root
docker-compose up --build
```

The backend container exposes port 8000 and persists SQLite data in a Docker volume (`stocktalk_dev_data`) mounted at `/app/data`.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | StockTalk Backend | Application name |
| `PORT` | 8000 | Server port |
| `NODE_ENV` | development | Environment |
| `DATABASE_FILE` | ./data/stocktalk_dev.db | SQLite database file path |
| `JWT_SECRET` | change-me-in-production | JWT signing secret (change in production!) |
| `JWT_EXPIRES_IN` | 7d | Token expiry |
| `CORS_ORIGINS` | http://localhost:5173,http://localhost:5174,http://localhost:3000 | Allowed CORS origins |

Never commit `.env`.

## Running with the Frontend

1. Start the backend: `cd backend && npm run dev`
2. Start the frontend: `cd frontend && npm run dev`
3. Frontend connects to `http://localhost:8000` via `VITE_API_URL` (default)

## Start / Stop / Test (PowerShell)

```powershell
# Start backend (dev, watches for changes)
cd backend
npm run dev

# Start backend (production build)
cd backend
npm run build
npm start

# Stop: Ctrl+C in the terminal running the server

# Build frontend
cd frontend
npm run build

# Preview frontend build
cd frontend
npm run preview
```

## Security Notes

- Passwords are hashed with bcryptjs (10 salt rounds) before storage.
- JWTs are signed with `JWT_SECRET` and expire after `JWT_EXPIRES_IN`.
- Change `JWT_SECRET` from the default in production.
- Logout is client-side: the token is cleared from memory and localStorage. Because JWTs are stateless, the server does not maintain sessions.
