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
# Set BACKEND_URL=http://localhost:8000 (server-only BFF upstream)
# Auth is handled by the backend (Supabase keys live only in backend/.env)
bun run dev
```

- App: http://localhost:3000  
- Login: http://localhost:3000/login  
- Dashboard (auth required): http://localhost:3000/app  

**Auth flow:** browser → FastAPI (`/api/v1/auth/*`) → Supabase (server-side).  
The same-origin Next.js BFF stores session tokens in HttpOnly cookies and never returns them to browser JavaScript.

In Supabase → **Authentication → URL Configuration** (required for production auth emails):

- **Site URL:** `https://fin-buddy-dev.vercel.app`
- **Redirect URLs:** include
  - `https://fin-buddy-dev.vercel.app/auth/callback`
  - `http://localhost:3000/auth/callback` (local)
- Do **not** leave Site URL as `http://localhost:3000` once you use the Vercel app — dashboard “Send Magic Link” and confirmation emails use Site URL.

Also set on FastAPI Cloud:

```bash
fastapi cloud env set FRONTEND_APP_URL "https://fin-buddy-dev.vercel.app"
fastapi cloud env set CORS_ORIGINS ""
```

And on Vercel (rebuild after changing):

- `NEXT_PUBLIC_APP_URL=https://fin-buddy-dev.vercel.app`
- `BACKEND_URL=https://fin-buddy.fastapicloud.dev` (server-only BFF upstream)

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

## Statement sample format

For reliable imports (demos and personal use), upload a `.txt` file starting with `FINBUDDY_STATEMENT`:

```text
FINBUDDY_STATEMENT
CARD:4821
PERIOD:2026-06-15..2026-07-14
STATEMENT_DATE:2026-07-15
DUE_DATE:2026-08-04
---
2026-07-01|purchase|SWIGGY BANGALORE|2450.00
2026-07-05|purchase|AMAZON PAY|1299.00
2026-07-10|refund|AMAZON PAY|500.00
2026-07-12|payment_to_issuer|PAYMENT THANK YOU|15000.00
```

Body rows are `date|type|merchant|amount_inr`. Supported types: `purchase`, `refund`, `fee`, `interest`, `payment_to_issuer`, `opening_balance`. Issuer bank PDFs still go through the generic text extractor (imperfect by design — review before import).

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

See **[docs/DEPLOY.md](docs/DEPLOY.md)** for the full Vercel + FastAPI Cloud + Supabase runbook.

### 1. Supabase (already used in local)

- Keep **pooler** `DATABASE_URL` for the API.
- Auth → URL Configuration:
  - Site URL: `https://your-app.vercel.app`
  - Redirect URLs: `https://your-app.vercel.app/auth/callback`
- Leave backend `CORS_ORIGINS` empty: browser traffic uses the same-origin Next.js BFF.

### 2. Backend → FastAPI Cloud (or any ASGI host)

```bash
cd backend
# Set secrets to match backend/.env.example:
#   DATABASE_URL, SUPABASE_*, JWT secret; CORS_ORIGINS must remain empty for BFF traffic
#   ENVIRONMENT=production
#   DEBUG=false
#   AUTO_MIGRATE=false  # run `uv run alembic upgrade head` once before serving
#   AUTO_SEED=false     # optional in prod
#   DEMO_LOGIN disabled in production by default
```

Health probe: `GET /api/v1/health`

Statement PDFs are stored via `STATEMENT_STORAGE_BACKEND`:
- `local` — disk under `STATEMENT_STORAGE_DIR` (Compose volume works for single-host).
- `supabase` — private Storage bucket (`STATEMENT_STORAGE_BUCKET`, default `statements`)
  using the service role. **Required for FastAPI Cloud** (ephemeral disks).

Create the bucket in Supabase → Storage as **private**. The API uses the service
role key; no public read policies are required.

### 3. Frontend → Vercel

```bash
cd frontend
# Root directory: frontend
# Build: bun run build  (or npm/pnpm equivalent if you adapt)
# Env:
#   NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
#   NEXT_PUBLIC_API_URL=https://your-api.example.com
#   BACKEND_URL=https://your-api.example.com   # server-only BFF upstream
```

Do **not** put Supabase service role or JWT secret in the frontend.

### 4. Smoke checklist after deploy

1. Sign in (demo is off in production — use email/Google).
2. Add a card → dashboard KPIs populate.
3. Add contact + purchase → contact outstanding updates.
4. Upload sample statement → review → import.
5. Open **Notifications** (bell) and **Settings** thresholds.

See also [backend/README.md](backend/README.md), [frontend/README.md](frontend/README.md), and [docs/DEPLOY.md](docs/DEPLOY.md).

## Security notes

- Never store full card numbers, CVV, or PIN — last 4 + metadata only.
- Money is stored as integer **paise**.
- All domain data is organization-scoped (RLS + API checks).
- In-app notifications only in v1 (no email/SMS/WhatsApp).

## License

Private / personal for now. To be decided before public release.
