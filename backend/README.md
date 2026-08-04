# Fin Buddy API

Production-oriented FastAPI backend for Fin Buddy.

## Stack

- FastAPI + Uvicorn
- SQLAlchemy 2 (async) + Alembic migrations
- Supabase Auth (JWT) + Supabase Postgres
- Structlog, Pydantic Settings, Pytest, Ruff, Mypy
- Package manager: **uv**

## Architecture

```text
app/
  api/v1/           # HTTP routers (auth, domain, admin)
  bootstrap/        # auto migrate + seed on startup
  core/             # config, security, middleware, exceptions
  db/               # engine, sessions, base
  domain/           # pure domain helpers
  infrastructure/   # Supabase Auth client, etc.
  models/           # SQLAlchemy ORM
  schemas/          # Pydantic DTOs
  seeders/          # idempotent seed functions
  services/         # business logic
  workers/          # future background jobs
alembic/            # migrations
```

## What you need from Supabase

In the [Supabase Dashboard](https://supabase.com/dashboard) open your project:

| Env var | Where to find it |
|---------|------------------|
| `SUPABASE_URL` | **Project Settings → API → Project URL** |
| `SUPABASE_ANON_KEY` | **Project Settings → API → Project API keys → `anon` `public`** |
| `SUPABASE_SERVICE_ROLE_KEY` | **Project Settings → API → `service_role` `secret`** (backend only) |
| `SUPABASE_JWT_SECRET` | **Project Settings → API → JWT Settings → JWT Secret** |
| `DATABASE_URL` | **Project Settings → Database → Connection string → URI** (use your DB password) |

Also enable providers you want under **Authentication → Providers** (Email, Google, Phone).

Put them in `backend/.env` (see `.env.example`).

Optional:

```env
PLATFORM_ADMIN_EMAILS=your@email.com
```

Your email is promoted to `super_admin` on first successful login/bootstrap so you can call `/api/v1/admin/*`.

## Setup

```bash
cd backend
uv sync --group dev
cp .env.example .env
# edit .env with Supabase values
```

## Run

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On startup (when `AUTO_MIGRATE` / `AUTO_SEED` are true):

1. Connects with `DATABASE_URL`
2. Runs **Alembic upgrade head**
3. Applies pending **seeders** (tracked in `seed_history`)
4. Starts serving

- Health: http://localhost:8000/api/v1/health  
- OpenAPI: http://localhost:8000/docs  

### Manual migrations

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe change"
```

## Auth endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/signup` | Email + password signup |
| POST | `/api/v1/auth/login` | Email + password login |
| POST | `/api/v1/auth/magic-link` | Send magic link email |
| POST | `/api/v1/auth/otp/phone` | Send phone OTP |
| POST | `/api/v1/auth/otp/verify` | Verify email/phone OTP |
| POST | `/api/v1/auth/refresh` | Refresh tokens |
| POST | `/api/v1/auth/logout` | Invalidate session (Bearer) |
| GET | `/api/v1/auth/me` | Profile + orgs (Bearer) |
| GET | `/api/v1/auth/oauth/google?redirect_to=` | Google OAuth URL |

Send `Authorization: Bearer <access_token>` on protected routes.  
Optional org scoping: `X-Organization-Id: <uuid>`.

## Domain endpoints

Cards, contacts, transactions, settlements, statements, dashboard — all org-scoped.

## Admin endpoints (platform admin / super_admin)

| Method | Path |
|--------|------|
| GET | `/api/v1/admin/activity-logs` |
| GET | `/api/v1/admin/error-logs` |
| GET | `/api/v1/admin/request-logs` |
| GET | `/api/v1/admin/users` |
| PATCH | `/api/v1/admin/users/{id}/role?role=admin` |

## Test / lint / typecheck

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

## Deploy (FastAPI Cloud)

Set the same env vars as secrets (see `.env.example`). Minimum production set:

| Secret | Notes |
|--------|--------|
| `DATABASE_URL` | Supabase pooler URI |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_JWT_SECRET` | Auth |
| `CORS_ORIGINS` | Include `https://your-app.vercel.app` |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `AUTO_MIGRATE` | `true` for single instance; release-step migrate + `false` for multi-instance |
| `AUTO_SEED` | Prefer `false` in production |
| `PLATFORM_ADMIN_EMAILS` | Your email(s) |
| `STATEMENT_STORAGE_BACKEND` | `supabase` on FastAPI Cloud |
| `STATEMENT_STORAGE_BUCKET` | Private bucket name (default `statements`) |

Demo login is disabled when `ENVIRONMENT=production` (unless explicitly re-enabled).

Entrypoint is `app.main:app` (`[tool.fastapi]` in `pyproject.toml`). Deploy with `fastapi deploy` from this directory. Full runbook: [`docs/DEPLOY.md`](../docs/DEPLOY.md).

Health probe: `GET /api/v1/health`

Prefer `AUTO_MIGRATE=true` for single-instance personal deploys; for multi-instance, run migrations as a release step and set `AUTO_MIGRATE=false` on app processes if needed.
