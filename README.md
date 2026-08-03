# Fin Buddy

Production-grade personal finance app for tracking **multiple credit cards**, **billing cycles**, a **full spend ledger**, and **friend lending balances** (India / INR first).

Personal daily driver first → wider public release later.

## Product docs

- [PRD](docs/prd/2026-07-27-fin-buddy-prd.md)

## Architecture

```text
┌─────────────────────┐     JWT (Supabase)      ┌──────────────────────┐
│  frontend/ (Next.js)│ ──────────────────────► │  backend/ (FastAPI)   │
│  Vercel             │                         │  FastAPI Cloud        │
└──────────┬──────────┘                         └──────────┬───────────┘
           │                                               │
           │ Supabase Auth                                 │ JWT verify +
           │                                               │ service role
           ▼                                               ▼
                    ┌────────────────────────────┐
                    │  Supabase                   │
                    │  Postgres + RLS + Storage   │
                    └────────────────────────────┘
```

| Piece | Tech |
|-------|------|
| Frontend | Next.js, TypeScript, Tailwind, shadcn/ui, Aceternity UI (selected) — **bun** |
| Backend | FastAPI, Pydantic — **uv** |
| Data / Auth | Supabase (Postgres, Auth, Storage) |
| Deploy | Vercel + FastAPI Cloud |

## Repository layout

```text
fin-buddy/
├── docs/prd/          # Product requirements
├── frontend/          # Next.js app
├── backend/           # FastAPI app
└── README.md
```

One git repository, two sibling apps (no monorepo tooling).

## Quick start

### Prerequisites

- [Bun](https://bun.sh) 1.x+ (frontend)
- Python 3.12+ and [uv](https://github.com/astral-sh/uv) (backend)
- A Supabase project (Phase 1+)

### Backend (uv)

```bash
cd backend
uv sync --group dev
cp .env.example .env
# Fill DATABASE_URL + Supabase keys (see backend/README.md)
uv run uvicorn app.main:app --reload --port 8000
```

On startup the API runs **Alembic migrations** and **seeders** automatically (`AUTO_MIGRATE` / `AUTO_SEED`).

- Health: http://localhost:8000/api/v1/health  
- OpenAPI: http://localhost:8000/docs  

**Supabase values for `backend/.env`:**

| Variable | Supabase location |
|----------|-------------------|
| `SUPABASE_URL` | Project Settings → API → Project URL |
| `SUPABASE_ANON_KEY` | Project Settings → API → `anon` public |
| `SUPABASE_SERVICE_ROLE_KEY` | Project Settings → API → `service_role` secret |
| `SUPABASE_JWT_SECRET` | Project Settings → API → JWT Secret |
| `DATABASE_URL` | Project Settings → Database → Connection string (URI) |
| `PLATFORM_ADMIN_EMAILS` | Your email(s), comma-separated — grants admin panel access |

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

### Frontend (bun)

```bash
cd frontend
bun install
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
# Auth is handled by the backend (Supabase keys live only in backend/.env)
bun run dev
```

- App: http://localhost:3000  
- Login: http://localhost:3000/login  
- Dashboard (auth required): http://localhost:3000/app  

**Auth flow:** browser → FastAPI (`/api/v1/auth/*`) → Supabase (server-side).  
Session cookies are stored on the Next.js origin after the backend returns tokens.

In Supabase → **Authentication → URL Configuration** (for OAuth / magic-link redirects only):

- Site URL: `http://localhost:3000`
- Redirect URLs: `http://localhost:3000/auth/callback`

Enable Email (and optionally Google) under **Authentication → Providers**.

```bash
bun run lint
bun run typecheck
bun run build
```

## Phase roadmap

| Phase | Scope |
|-------|--------|
| **0** (done) | PRD + scaffolds + foundations |
| **1** (done) | Supabase auth + multi-tenant orgs + app shell |
| **2** (done) | Cards, billing cycles, dashboard |
| **3** (done) | Contacts, transactions, settlements |
| **4** (done) | Statement PDF upload + review import |
| **5** (done) | Polish, empty states, notifications, settings, deploy docs |
| **Later** | Issuer-specific parsers, public packaging, external reminders |

## Docker Compose (local / personal production)

Runs **frontend** (`:3000`) and **backend** (`:8000`) against your existing Supabase project (Postgres + Auth stay external).

```bash
# Secrets: use existing backend/.env (local API), OR copy root template:
#   cp .env.example .env   # only if you want docker-specific overrides

docker compose up -d --build
# UI  → http://localhost:3000
# API → http://localhost:8000/api/v1/health
# Logs: docker compose logs -f
# Stop:  docker compose down
```

Compose injects `backend/.env` into the API container (plus optional root `.env`).
Do not put `DATABASE_URL=${DATABASE_URL:?…}` style host interpolation on secrets — that
requires a root `.env` even when `backend/.env` already has the values.

| Piece | Path |
|-------|------|
| Compose | `docker-compose.yml` |
| Env template | `.env.example` |
| API image | `backend/Dockerfile` |
| Web image | `frontend/Dockerfile` |

Notes:

- Statement PDFs persist in the `fin-buddy-statement-data` volume.
- Migrations run once on backend start (`RUN_MIGRATIONS=true`); workers are multi-process via `WEB_CONCURRENCY`.
- Rebuild the frontend image after changing `NEXT_PUBLIC_*` or public URLs (they are build-time).
- In Supabase Auth URL config, allow `http://localhost:3000` / `http://localhost:3000/auth/callback` (or your real host).

## Personal production deploy

### 1. Supabase (already used in local)

- Keep **pooler** `DATABASE_URL` for the API.
- Auth → URL Configuration:
  - Site URL: `https://your-app.vercel.app`
  - Redirect URLs: `https://your-app.vercel.app/auth/callback`
- Add production origins to backend `CORS_ORIGINS`.

### 2. Backend → FastAPI Cloud (or any ASGI host)

```bash
cd backend
# Set secrets to match backend/.env.example:
#   DATABASE_URL, SUPABASE_*, JWT secret, CORS_ORIGINS (include Vercel URL)
#   ENVIRONMENT=production
#   DEBUG=false
#   AUTO_MIGRATE=true   # single instance
#   AUTO_SEED=false     # optional in prod
#   DEMO_LOGIN disabled in production by default
```

Health probe: `GET /api/v1/health`

Statement PDFs are stored under `STATEMENT_STORAGE_DIR` (local disk by default). For durable multi-instance deploys, mount persistent volume or point storage at object storage later.

### 3. Frontend → Vercel

```bash
cd frontend
# Root directory: frontend
# Build: bun run build  (or npm/pnpm equivalent if you adapt)
# Env:
#   NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
#   NEXT_PUBLIC_API_URL=https://your-api.example.com
#   BACKEND_URL=https://your-api.example.com   # server-side rewrite target
```

Do **not** put Supabase service role or JWT secret in the frontend.

### 4. Smoke checklist after deploy

1. Sign in (demo is off in production — use email/Google).
2. Add a card → dashboard KPIs populate.
3. Add contact + purchase → contact outstanding updates.
4. Upload sample statement → review → import.
5. Open **Notifications** (bell) and **Settings** thresholds.

See also [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md).

## Security notes

- Never store full card numbers, CVV, or PIN — last 4 + metadata only.
- Money is stored as integer **paise**.
- All domain data is organization-scoped (RLS + API checks).
- In-app notifications only in v1 (no email/SMS/WhatsApp).

## License

Private / personal for now. To be decided before public release.
