# Personal production deploy runbook

This complements the root README. Follow in order for Vercel + FastAPI Cloud + Supabase.

## 0. Prerequisites

- Private GitHub repo with this codebase pushed
- Supabase project (prefer a dedicated **prod** project if local DB has demo junk)
- FastAPI Cloud account
- Vercel account
- Google OAuth client (if using Google sign-in)

## 1. Supabase

1. Create private Storage bucket named `statements` (or match `STATEMENT_STORAGE_BUCKET`).
2. No public read policies required — API uses the service role key.
3. Auth → URL Configuration:
   - Site URL: `https://<your-app>.vercel.app`
   - Redirect URLs: `https://<your-app>.vercel.app/auth/callback`
4. Enable Email (+ Google if needed) under Authentication → Providers.
5. Copy pooler `DATABASE_URL`, project URL, anon key, service role key, JWT secret.

## 2. Backend → FastAPI Cloud

From `backend/`:

```bash
uv lock
uv sync --group dev
# Verify CLI extras (required by FastAPI Cloud):
uv run python -c "import fastapi_cli; print('ok')"
fastapi login
fastapi deploy
```

**Required deps:** `fastapi[standard]` **and** a lockfile that actually installs `fastapi-cli`. If Cloud logs say `pip install "fastapi[standard]"`, the deployed lock is stale — run `uv lock` locally and redeploy. Python is pinned to **3.12** via `.python-version` / `requires-python` (avoid 3.14 on Cloud).

Set env (use `--secret` for secrets):

```bash
fastapi cloud env set ENVIRONMENT production
fastapi cloud env set DEBUG false
# Run Alembic as a one-off release step; never let every application replica
# compete to migrate during startup.
fastapi cloud env set AUTO_MIGRATE false
fastapi cloud env set AUTO_SEED false
fastapi cloud env set DEMO_AUTH_ENABLED false
fastapi cloud env set STATEMENT_STORAGE_BACKEND supabase
fastapi cloud env set STATEMENT_STORAGE_BUCKET statements
fastapi cloud env set CORS_ORIGINS ""
fastapi cloud env set PLATFORM_ADMIN_EMAILS "you@example.com"
fastapi cloud env set --secret JOB_RUNNER_SECRET "generate-a-long-random-value"
fastapi cloud env set --secret DATABASE_URL "postgresql://..."
fastapi cloud env set --secret SUPABASE_URL "https://....supabase.co"
fastapi cloud env set --secret SUPABASE_ANON_KEY "..."
fastapi cloud env set --secret SUPABASE_SERVICE_ROLE_KEY "..."
fastapi cloud env set --secret SUPABASE_JWT_SECRET "..."
```

Run the migration exactly once against the target Supabase database before scaling or serving API traffic:

```bash
uv run alembic upgrade head
```

Redeploy after env changes if required by the platform. Configure your trusted
scheduler to send `X-Job-Secret` with `POST /api/v1/jobs/send-reminders`; the
endpoint is intentionally unavailable until `JOB_RUNNER_SECRET` is set. Probe:

`GET https://<your-api>/api/v1/health`

## 3. Frontend → Vercel

- Root directory: `frontend`
- Framework preset: **Next.js** (do not leave as Other / unset)
- Install: `bun install` / Build: `bun run build`
- Env (Production) — browser calls the same-origin `/api/backend/*` BFF route. The BFF reads `BACKEND_URL` server-side and attaches HttpOnly-session credentials to FastAPI:

| Variable | Value |
|----------|--------|
| `NEXT_PUBLIC_APP_URL` | `https://fin-buddy-dev.vercel.app` |
| `BACKEND_URL` | `https://fin-buddy.fastapicloud.dev` |

Do **not** put service role or JWT secret in Vercel.

`BACKEND_URL` is server-only. Do not put service-role or JWT secrets in Vercel, and do not configure cross-origin browser CORS for the BFF topology. Redeploy Vercel after changing environment variables.

**Gotcha:** `output: "standalone"` is Docker-only (`DOCKER_BUILD=1`). Enabling it on Vercel can yield a green build that still returns platform `404 NOT_FOUND`.

## 4. Smoke checklist

1. Sign in (email and/or Google). Demo login must be unavailable.
2. Add a card → dashboard KPIs populate.
3. Add contact + purchase → contact outstanding updates.
4. Upload FinBuddy sample `.txt` or PDF → review → import.
5. Restart / redeploy API → re-open the statement detail (file still loads from Supabase Storage).
6. Open Notifications and Settings thresholds.

## 5. Local quality gates before push

```bash
cd backend && uv lock && uv sync --group dev && uv run pytest && uv run ruff check . && uv run mypy app
cd frontend && bun run lint && bun run typecheck && bun run build
./scripts/smoke-prod.sh   # set API_URL / APP_URL for deployed hosts
```
