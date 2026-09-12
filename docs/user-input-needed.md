# Fin Buddy — user input needed

This is the tracked handoff between the implementation loops and the project
owner. Agents should update the status, instructions, and evidence links as
they discover new blockers. They must never write secret values here.

## How the owner provides an input

1. Use the exact dashboard or secret-manager path in the relevant row below.
2. Tell the agent only that the value/decision has been provided, or provide a
   non-secret identifier such as a project ref. Do not paste a client secret,
   service-role key, database password, JWT secret, scheduler secret, or API
   token into chat, Git, an issue, or this file.
3. The agent changes `needed` to `provided` and records the date plus the
   destination, never the value.
4. The agent changes `provided` to `verified` only after a safe observable
   check succeeds, such as a provider status, a redacted environment-key
   listing, a callback smoke test, or a deployment response. A successful
   existence check is not permission to print the secret.

Allowed statuses are `needed`, `provided`, `verified`, `blocked`, and `not
applicable`. Keep unresolved rows visible. If a later loop discovers another
human input, add a row with a stable ID rather than burying it in a story note.

## Current checklist

| ID | Input or decision | Status | Where the owner provides it | What the agent records |
| --- | --- | --- | --- | --- |
| `UI-01` | Release surface: production or staging | `provided` | State the decision in the next task message and then record the chosen hostname in the `Notes` column here. | 2026-09-05: Confirmed `https://fin-buddy-dev.vercel.app` is the production surface. |
| `UI-02` | Google OAuth Web client | `verified` | Follow the exact Google OAuth steps below. The client ID and client secret go into Supabase Auth, not this repo. | 2026-09-07: Verified live. Supabase reports Google provider enabled with client ID `1017490367160-eja7fk6vt7m9fioh0lj9rhfoha46b2uv.apps.googleusercontent.com`, redirecting to `accounts.google.com` with `response_type=code`. |
| `UI-03` | Intended Supabase project/data target | `provided` | Confirm the project name/ref in Supabase Dashboard before any migration or policy change. | 2026-09-05: Confirmed target `https://jklurueadteccrdycyiz.supabase.co` (`jklurueadteccrdycyiz`). |
| `UI-04` | FastAPI Cloud access and free-plan confirmation | `provided` | Log in through the FastAPI Cloud CLI or dashboard on the owner’s machine. Do not paste the token. | 2026-09-05: Authenticated CLI (`ffaranm15@gmail.com`), linked app `fin-buddy` (`db8c5e53-0f3a-4315-8b14-ee86b13ca2df`). |
| `UI-05` | Vercel project access and Hobby-plan confirmation | `provided` | Log in through Vercel CLI/dashboard on the owner’s machine. Do not paste a token. | 2026-09-05: Authenticated CLI (`faranheit15`), project `fin-buddy` confirmed Hobby tier. |
| `UI-06` | Household mutation policy | `verified` | Choose in task message: Tiered Collaborative Hybrid, Flat, or Strict RBAC. | 2026-09-08: Tiered Collaborative Hybrid implemented and verified. All members can create/edit daily transactions, splits, statements, settlements, debts, and EMI payments. Structural resources (accounts, cards, categories delete) and ledger balance corrections/reversals require Admin or Owner. Verified across 248 backend tests. |
| `UI-07` | Keepalive experiment approval | `verified` | Confirm whether one protected daily Vercel Cron probe may be enabled. | 2026-09-12: Verified in US-P07. Protected route `/api/cron/supabase-keepalive` added with once-daily schedule (`0 5 * * *` UTC), timing-safe `CRON_SECRET` verification, `ENABLE_KEEPALIVE_CRON` kill switch, bounded 2.5s DB timeout, HTTP 503 on degradation, and `api_request_logs` write suppression. |
| `UI-08` | Custom domain | `not applicable` | Keep the free Vercel and FastAPI Cloud hostnames unless the owner explicitly accepts domain cost. | Domain decision only. |
| `UI-09` | Disposable browser test identity | `verified` | Use a test Google account or local synthetic account in the owner’s password manager/local secret store; do not paste credentials. | 2026-09-07: Verified live browser login at `https://fin-buddy-dev.vercel.app/login?next=/app/cards` using disposable test Google identity. Flow redirected cleanly to `/app/cards`, URL was sanitized (no code/state/tokens in history or address bar), session persisted across page refresh, and logout cleared cookies safely. |
| `UI-10` | Rotate `DATABASE_URL` to Supabase Session Pooler URI | `verified` | Reset DB password in Supabase: Project Settings → Database. In **Connection string**, select **URI** and copy the current dashboard-generated **Session Pooler** connection string (Port 5432). Set via `uv run fastapi cloud env set DATABASE_URL --value-stdin --secret --path .` (enter value on stdin without writing to shell history). | 2026-09-07: Verified `is_secret: true` in FastAPI Cloud. Live probe verified HTTP 200 OK for `/health` and `/ready` using the current dashboard-generated Supabase Session Pooler URI. |
| `UI-11` | Rotate `SUPABASE_JWT_SECRET` | `verified` | Generate new JWT secret in Supabase: Project Settings → API → JWT Settings. In production `JWT_VERIFICATION_MODE=jwks_only`, ES256 tokens verify via Supabase JWKS, making this secret optional in production. | 2026-09-06: Verified `is_secret: true` in FastAPI Cloud. `JWT_VERIFICATION_MODE=jwks_only` active and verified. |
| `UI-12` | Rotate `SUPABASE_SERVICE_ROLE_KEY` | `verified` | Roll service_role key in Supabase: Project Settings → API. Set in FastAPI Cloud via `uv run fastapi cloud env set SUPABASE_SERVICE_ROLE_KEY --value-stdin --secret --path .` (enter value on stdin). | 2026-09-06: Verified `is_secret: true` in FastAPI Cloud (`sb_secret_` / opaque key handling verified). |
| `UI-13` | Confirm replacement secrets in FastAPI Cloud | `verified` | Verified non-secret metadata only (`is_secret: true`, `has_value: true`, `JWT_VERIFICATION_MODE=jwks_only`). | 2026-09-07: All replacement credentials verified; deployment `c016b96d` active and verified. |

## Google OAuth — exact setup

The current app does not need a Google client secret in a frontend `.env` file.
Google OAuth is brokered by Supabase Auth. The secret must be entered into the
Supabase provider settings and must never be exposed to browser JavaScript,
Vercel public variables, or this document.

### 1. Create or select the Google client

In [Google Cloud Console](https://console.cloud.google.com/):

1. Select the Google Cloud project that owns Fin Buddy, or create a personal
   project without enabling a paid service.
2. Open **APIs & Services → OAuth consent screen** and complete the required
   consent configuration for a personal/test app.
3. Open **APIs & Services → Credentials → Create credentials → OAuth client ID**.
4. Choose **Web application**.
5. Add these authorized JavaScript origins:
   - `https://fin-buddy-dev.vercel.app`
   - `http://localhost:3000` only for local testing, if needed.
6. Add this authorized redirect URI, replacing `<project-ref>` after verifying
   the active project:
   - `https://<project-ref>.supabase.co/auth/v1/callback`
7. Copy the client ID and client secret only into the next Supabase step.

The project ref observed during the 2026-09-03 audit was
`jklurueadteccrdycyiz`; verify it in Supabase before using it. The Supabase
callback is not the same URL as the app route `/auth/callback`.

### 2. Enable Google in Supabase Auth

In [Supabase Dashboard](https://supabase.com/dashboard):

1. Select the verified Fin Buddy project.
2. Open **Authentication → Providers → Google**.
3. Enable Google.
4. Paste the Google **Client ID** and **Client Secret** into the two provider
   fields and save. Do not put them in `backend/.env`, Vercel, or Git.
5. Open **Authentication → URL Configuration** and set:
   - **Site URL:** `https://fin-buddy-dev.vercel.app` if that is the chosen
     production surface.
   - **Redirect URLs:** `https://fin-buddy-dev.vercel.app/auth/callback` and
     `http://localhost:3000/auth/callback` for local testing, if needed.
6. Tell the agent that `UI-02` is provided. The agent will verify the provider
   status and test the browser callback without printing credentials.

At the last recorded audit, the live Google provider was disabled and the
application rejected its current callback before reaching Google. That is the
expected human blocker until these dashboard actions are complete; adding a
frontend env variable alone will not fix it.

There is also a code-level callback blocker to handle in `US-P02`: the current
frontend login flow can send `/auth/callback?next=...`, while the backend
callback validation rejects callback query parameters. Credentials alone will
not close Google sign-in until that contract is either made safe and tested or
the `next` parameter is removed from the provider redirect.

## Deployment inputs and exact destinations

### Supabase

Use **Project Settings → API** and **Project Settings → Database → Connection
string** to identify the project URL, anon key, service-role key, JWT secret,
and pooler URI. Enter the backend-only values in **FastAPI Cloud → Fin Buddy
app → Environment variables/secrets**, or with the documented CLI commands in
[`DEPLOY.md`](DEPLOY.md). The service-role key, JWT secret, database password,
and pooler URI are backend secrets. Never put them in Vercel browser variables.

### FastAPI Cloud

Authenticate locally using the FastAPI Cloud CLI or dashboard. Set runtime
values and secrets in the app’s environment settings. The repository’s
`backend/.env.example` is a names-only template for local development; copy it
to a gitignored local file only if needed. Verify `ENVIRONMENT=production`,
`DEBUG=false`, `DEMO_AUTH_ENABLED=false`, `AUTO_SEED=false`,
`STATEMENT_STORAGE_BACKEND=supabase`, and the real secrets in the cloud
environment without printing their values.

### Vercel

Use the Vercel project’s **Settings → Environment Variables** for Production.
The server-only BFF needs `BACKEND_URL`; the public app URL is
`NEXT_PUBLIC_APP_URL`. If the protected daily probe is approved, `CRON_SECRET`
belongs in Vercel’s server-side environment and the schedule belongs in the
frontend deployment configuration. Do not add Supabase service-role, JWT, or
database secrets to Vercel.

### Local development files

- Backend local values belong in the ignored file
  `/home/faran/Workspace/fin-buddy/backend/.env`, copied from
  [`backend/.env.example`](../backend/.env.example). Do not read or paste its
  secret values into an agent session.
- Frontend local values, when needed, belong in the ignored file
  `/home/faran/Workspace/fin-buddy/frontend/.env.local`. The repository does
  not currently ship a `frontend/.env.example`; do not invent production
  secrets to fill that documentation gap.
- Root `.env` is for Docker Compose overrides. Keep Supabase service-role,
  JWT, database-password, OAuth-secret, and scheduler-secret values out of it
  unless a reviewed local Docker workflow explicitly requires them.

The current frontend uses the same-origin BFF and reads `BACKEND_URL`
server-side; do not ask the owner to configure an unused `NEXT_PUBLIC_API_URL`
just because it appears in CI.

## Free-only and AI-only guardrails

This plan targets `$0 billed cost`, not an unconditional uptime guarantee. The
owner must keep Vercel on Hobby for personal/non-commercial use, FastAPI Cloud
on Hobby, and Supabase on Free. Do not enable paid plans, custom domains, paid
add-ons, paid email/monitoring/cache/queue providers, or paid AI APIs. Record a
quota snapshot before releases. If a quota approaches its limit, disable the
optional keepalive, analytics, reminders, or other non-essential jobs before
adding capacity.

Supabase Free may pause low-activity projects after roughly a week; Vercel
Hobby Cron runs at most once daily with approximate timing; FastAPI Cloud Hobby
scales to zero. A daily `/ready` probe is an optional, bounded, best-effort
activity experiment. It must not write dummy financial data and it cannot
guarantee that Supabase stays active.

## Compromised credential rotation instructions (UI-10, UI-11, UI-12, UI-13)

Per security incident procedure, `DATABASE_URL`, `SUPABASE_JWT_SECRET`, and `SUPABASE_SERVICE_ROLE_KEY` are treated as compromised. No new deployment will be triggered until the replacement secrets are confirmed in FastAPI Cloud.

Never print, inspect, or paste these secrets into chat, Git, or agent context.

### 1. Rotate Database Password (UI-10)
1. Open Supabase Dashboard: `https://supabase.com/dashboard/project/jklurueadteccrdycyiz/settings/database`.
2. Scroll to **Database password** and click **Reset database password**. Generate a secure random password and save.
3. In **Connection string**, select **URI** and copy the current dashboard-generated Session Pooler URI (Port 5432).
4. Set the new connection URI in FastAPI Cloud from `backend/`:
   ```bash
   uv run fastapi cloud env set DATABASE_URL --value-stdin --secret --path .
   ```
   *(Enter or paste the secret on stdin without saving it to shell history)*

### 2. Rotate JWT Secret (UI-11)
1. Open Supabase Dashboard: `https://supabase.com/dashboard/project/jklurueadteccrdycyiz/settings/api`.
2. Under **JWT Settings**, locate **JWT Secret** and click **Generate a new secret** (32+ character high-entropy secret).
   *Note: In production `JWT_VERIFICATION_MODE=jwks_only`, tokens verify via Supabase JWKS (ES256), making `SUPABASE_JWT_SECRET` optional in production. If configuring for local hybrid compatibility:*
3. Set the new secret in FastAPI Cloud from `backend/`:
   ```bash
   uv run fastapi cloud env set SUPABASE_JWT_SECRET --value-stdin --secret --path .
   ```
   *(Enter or paste the secret on stdin without saving it to shell history)*

### 3. Rotate Service Role Key (UI-12)
1. Open Supabase Dashboard: `https://supabase.com/dashboard/project/jklurueadteccrdycyiz/settings/api`.
2. Under **Project API keys**, locate the `service_role` key and roll/regenerate the key.
3. Set the new key in FastAPI Cloud from `backend/`:
   ```bash
   uv run fastapi cloud env set SUPABASE_SERVICE_ROLE_KEY --value-stdin --secret --path .
   ```
   *(Enter or paste the secret on stdin without saving it to shell history)*

### 4. Confirm Replacement Secrets (UI-13)
* Inform the agent once the secrets have been set in FastAPI Cloud. The agent will verify metadata presence (`has_value: true`, `is_secret: true`) and `JWT_VERIFICATION_MODE=jwks_only` without printing values before clearing deployment.

## Agent update log

| Date | Agent/task | Change | Evidence or blocker |
| --- | --- | --- | --- |
| 2026-09-05 | Productionization planning | Created this handoff and documented the current Google OAuth blocker. | Provider credentials and deployment-plan confirmations are still needed. |
| 2026-09-05 | Read-only live OAuth probe | Rechecked the deployed Google authorization path without exposing the returned public key material. | OAuth URL builder returned successfully; the Supabase authorize request returned HTTP 400. Confirm the Google provider status and exact callback in Supabase before US-P02. |
| 2026-09-05 | US-P01 Production release gate | Owner confirmed UI-01 (prod URL), UI-03 (Supabase project), UI-04 (FastAPI Cloud login), UI-05 (Vercel login), and UI-07 (Keepalive probe). FastAPI Cloud env set to production matrix (`ENVIRONMENT=production`, `DEBUG=false`, etc.). Code fail-closed guards and unit tests implemented. | Remote FastAPI Cloud image build failed during `fastapi deploy` with `Installing Python interpreter (os error 2)` (deployment `8b4d5e61-5e7e-45b4-8248-c5c3e8d4f3d4`). Story left in_progress awaiting cloud deploy fix. |
| 2026-09-05 | US-P01 Security remediation | DATABASE_URL, SUPABASE_JWT_SECRET, and SUPABASE_SERVICE_ROLE_KEY treated as compromised. Added UI-10 through UI-13 for owner rotation. Deployment locked until confirmed. | Required rotation actions documented. No secrets printed or inspected. |
| 2026-09-05 | US-P01 Secret verification | Safe CLI check revealed FastAPI Cloud rejects `env set --secret` when variable already exists. Deleted the 3 stale non-secret variables from cloud to clear collision. Awaiting `fastapi cloud env set --secret` from owner. | `is_secret: true` verification pending. |
| 2026-09-07 | US-P01 Release gate closure | Verified UI-10 and UI-13. Production deployment `c016b96d` active with HTTP 200 health and readiness, docs/OpenAPI disabled, demo auth disabled, frontend BFF verified, and Supabase Session Pooler URI verified. | US-P01 closed. UI-02 (Google OAuth) remains queued for US-P02. |
| 2026-09-07 | US-P02 Google OAuth loop | Verified UI-02 live (Google client ID active, Supabase redirect 302 to Google). Implemented fixed callback contract, origin-bound single-use state, PKCE S256 code exchange, same-origin relative path sanitization, backend tests (206 passed) and frontend tests (16 passed). Awaiting disposable test account for real browser sign-in. | UI-02 verified; UI-09 needed for browser verification. |
| 2026-09-07 | US-P02 Browser verification | Verified UI-09 live. Omitted custom state from Supabase /authorize to fix bad_oauth_state; guarded callback page with executedRef against Next.js searchParams re-render effect cancellation. Live browser sign-in succeeded from /login?next=/app/cards, URL sanitized, session established and persistent across refresh, and logout verified. | UI-09 verified; US-P02 complete. |
| 2026-09-07 | US-P03 Supabase security boundary | Reconciled 23 application tables, enforced RLS on all 17 remaining tables without FORCE, added symmetric WITH CHECK & DELETE policies, revoked public grants & routines, altered default privileges, and documented leaked-password protection $0 constraint. | Migration 20260907_0015 added and verified with 16 dedicated tests; 222 backend and 18 frontend tests passed; UI-06 queued for US-P04. |
| 2026-09-07 | US-P04 Tenant auth & lifecycle | Investigated organization-reference matrix, role/capability matrix, deletion lifecycle, and EMI actor ID. Documented explicit UI-06 choices (Option 1: Tiered Collaborative Hybrid, Option 2: Flat Collaborative, Option 3: Strict RBAC). | Matrices compiled; awaiting owner decision on UI-06 before making ambiguous role restriction changes. |
| 2026-09-08 | US-P04 Tenant auth & lifecycle completion | Closed cross-org reference gaps across contacts, cards, categories, transactions, settlements, and obligations; implemented UI-06 Tiered Collaborative Hybrid role enforcement; added DeletedAccount tombstone lifecycle preventing profile recreation; fixed EMI actor profile ID; added additive reversible migration 20260907_0016. | All 248 backend and 18 frontend tests passed, Ruff clean, Mypy clean, Turbopack build clean. UI-06 verified. |
| 2026-09-08 | US-P05 Safe financial mutations | Implemented RFC 9440 Idempotency-Key engine with SHA-256 payload hashing and cached replay; added row-level locking (with_for_update) across reversals, drafts, EMIs, obligations, statements, and balance corrections; added additive reversible migration `20260908_0017` with partial unique index on reversals; passed 9 real PostgreSQL concurrency/race tests and 257 backend tests; updated BFF and frontend forms with double-click prevention and key persistence. | Migration `20260908_0017` explicitly applied and verified on Supabase project `jklurueadteccrdycyiz`: `public.alembic_version = 20260908_0017`, `public.idempotency_records` exists, and all four business-invariant indexes/constraints exist. Authenticated live replay and changed-payload `409` checks passed; FastAPI Cloud logs had no errors; `AUTO_MIGRATE=false` confirmed. |
| 2026-09-09 | US-P06 Durable statement ingestion | Verified the live Supabase `statements` bucket is private, restricted to 15 MB, and restricted to the five supported statement MIME types. Verified FastAPI Cloud non-secret configuration includes `STATEMENT_STORAGE_BACKEND=supabase`, bucket `statements`, `STATEMENT_MAX_UPLOAD_BYTES=15728640`, 15-minute upload TTL, one-hour abandonment window, and `AUTO_MIGRATE=false`; no new human input is needed. | Code commit `7ae1a1c` is pushed. Two manual FastAPI Cloud release attempts failed before startup in the provider image builder while installing Python (`No such file or directory (os error 2)`); no secrets were exposed and no live fixture was uploaded. |
| 2026-09-09 | US-P06 Durable statement ingestion — closure | No new human input is needed. | Deployment `040d949b` for commit `d8faea9` reached Live/Ready; the authenticated synthetic statement smoke reached `Needs review` with five pending lines after redeploy. Bucket privacy, 15 MiB/five-MIME restrictions, production storage configuration, and `AUTO_MIGRATE=false` were re-verified without exposing secrets. |
| 2026-09-12 | US-P07 Readiness and keepalive | Implemented bounded DB readiness check, HTTP 503 on degradation/timeout, request-log write suppression for health probes, asyncpg connection timeout hygiene, protected `/api/cron/supabase-keepalive` route with timing-safe `CRON_SECRET` verification and `ENABLE_KEEPALIVE_CRON` toggle, and Vercel Hobby once-daily schedule (`0 5 * * *` UTC). | All 281 backend tests and 27 frontend tests passed; live probes against production FastAPI Cloud and Vercel BFF verified 200 OK; no database migration needed. |
