# Personal production deploy runbook

> **Status:** Operational runbook · **Last reviewed:** 2026-09-03

This complements the [root README](../README.md). Follow the sections in order
for Vercel + FastAPI Cloud + Supabase. The latest release-owner decision and
validation evidence are in the [release-readiness review](reviews/2026-08-11-release-readiness.md).

## Before you begin

- Use a dedicated production Supabase project when the local database contains demo data.
- Keep secrets in deployment configuration or local `.env` files; never commit them.
- Apply the reviewed Alembic migration exactly once before serving production API traffic.
- Use the [smoke checklist](reviews/2026-08-11-release-readiness.md#release-owner-checklist) after both services are deployed.

## 0. Prerequisites

- Private GitHub repo with this codebase pushed
- Supabase project (prefer a dedicated **prod** project if local DB has demo junk)
- FastAPI Cloud account
- Vercel account
- Google OAuth client (if using Google sign-in)

## 1. Supabase

1. Create a **private** Storage bucket named `statements` (or match `STATEMENT_STORAGE_BUCKET`).
2. Set the bucket restrictions to **15 MiB** and these MIME types:
   `application/pdf`, `text/plain`, `text/csv`, `text/tab-separated-values`, and
   `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
3. No public read policies are required — the API uses the service role only
   to issue signed upload URLs and inspect/delete objects.
3. Auth → URL Configuration:
   - Site URL: `https://fin-buddy-dev.vercel.app`
   - Redirect URLs: `https://fin-buddy-dev.vercel.app/auth/callback`
3. Enable Email (+ Google if needed) under Authentication → Providers.
4. Copy Session Pooler `DATABASE_URL` (Project Settings → Database → Connection string → URI → Mode: Session), project URL, publishable/anon key, service role key, JWT secret.

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
# Non-secret environment variables (run from backend/ directory)
uv run fastapi cloud env set ENVIRONMENT production --path .
uv run fastapi cloud env set DEBUG false --path .
# Run Alembic as a one-off release step; never let every application replica
# compete to migrate during startup.
uv run fastapi cloud env set AUTO_MIGRATE false --path .
uv run fastapi cloud env set AUTO_SEED false --path .
uv run fastapi cloud env set DEMO_AUTH_ENABLED false --path .
uv run fastapi cloud env set STATEMENT_STORAGE_BACKEND supabase --path .
uv run fastapi cloud env set STATEMENT_STORAGE_BUCKET statements --path .
uv run fastapi cloud env set STATEMENT_MAX_UPLOAD_BYTES 15728640 --path .
uv run fastapi cloud env set STATEMENT_UPLOAD_TTL_SECONDS 900 --path .
uv run fastapi cloud env set STATEMENT_ABANDON_AFTER_SECONDS 3600 --path .
uv run fastapi cloud env set CORS_ORIGINS "" --path .
uv run fastapi cloud env set PLATFORM_ADMIN_EMAILS "you@example.com" --path .
uv run fastapi cloud env set JWT_VERIFICATION_MODE jwks_only --path .
uv run fastapi cloud env set SUPABASE_URL "https://<project-ref>.supabase.co" --path .

# Secret variables (enter secret via stdin to prevent credentials from appearing in shell history)
uv run fastapi cloud env set JOB_RUNNER_SECRET --value-stdin --secret --path .
uv run fastapi cloud env set DATABASE_URL --value-stdin --secret --path .
uv run fastapi cloud env set SUPABASE_PUBLISHABLE_KEY --value-stdin --secret --path .
uv run fastapi cloud env set SUPABASE_SERVICE_ROLE_KEY --value-stdin --secret --path .

# SUPABASE_JWT_SECRET is optional in production when JWT_VERIFICATION_MODE=jwks_only.
# If configured for hybrid/HS256 local compatibility:
uv run fastapi cloud env set SUPABASE_JWT_SECRET --value-stdin --secret --path .
```

There is no new database migration for US-P06: the existing statement metadata
columns and idempotency table are sufficient. If a release includes another
reviewed migration, run it exactly once against the target Supabase database
before scaling or serving API traffic:

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

### Keepalive probe (optional Vercel Cron)

A low-frequency database activity probe is defined in `frontend/vercel.json` (`/api/cron/supabase-keepalive` scheduled at `0 5 * * *` UTC / 10:30 AM IST).

| Variable | Optional? | Description |
|---|---|---|
| `CRON_SECRET` | Recommended | Secret token automatically sent by Vercel Cron (`Authorization: Bearer <CRON_SECRET>`). If unset, the route fails closed (HTTP 503). |
| `ENABLE_KEEPALIVE_CRON` | Optional | Set to `"false"` to disable the keepalive probe with zero code changes (returns HTTP 200 without calling backend). |

**Caveats & Guardrails:**
- Bounded to once daily (`0 5 * * *`) to stay within Vercel Hobby tier quotas.
- Calls backend `/api/v1/ready` using `cache: "no-store"`, stripped of all user cookies and credentials.
- Excluded from `api_request_logs` table writes and writes zero dummy application data.
- **Best-effort only**: Supabase Free pauses projects after ~7 days of inactivity; this probe provides an activity signal but **does not guarantee** that Supabase will never pause, nor does it keep FastAPI Cloud warm (FastAPI Cloud Hobby scales to zero).

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
