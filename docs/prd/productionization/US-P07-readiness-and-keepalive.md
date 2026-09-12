# US-P07 — Readiness and Supabase keepalive

| Field | Value |
| --- | --- |
| **Status** | `done` |
| **Sequence** | 7 |
| **Depends on** | [US-P01](US-P01-production-release-gate.md) |
| **One-loop objective** | Make liveness/readiness truthful and add a low-frequency, optional database activity probe. |
| **Primary boundaries** | FastAPI health routes, request middleware, Vercel Cron, Supabase database |

## User story

**As** the Fin Buddy owner
**I want** health checks to distinguish a running API from a usable database and optionally perform a bounded free-tier activity probe
**So that** deployment failures are visible without adding a paid monitoring or always-on service.

## Why this matters

`/health` is intentionally cheap and does not query the database. `/ready`
executes `SELECT 1`, but previously returned HTTP 200 with a degraded body when
database pings failed. Both paths were previously logged to `api_request_logs`
by request middleware, producing thousands of unnecessary database writes.
Supabase Free may pause after 7 days of inactivity; the proposed check is an
optional, low-frequency, bounded activity signal.

## Scope and non-goals

In scope: status codes, bounded DB readiness, probe logging exclusion, Vercel Cron route,
secret verification, and operational evidence. Out of scope: keeping FastAPI
warm, user reminders, or paid monitoring.

## Touchpoints

- [`backend/app/api/v1/health.py`](../../../backend/app/api/v1/health.py)
- [`backend/app/core/middleware.py`](../../../backend/app/core/middleware.py)
- [`frontend/src/app/api/cron/supabase-keepalive/route.ts`](../../../frontend/src/app/api/cron/supabase-keepalive/route.ts)
- [`frontend/vercel.json`](../../../frontend/vercel.json)
- [`backend/app/db/session.py`](../../../backend/app/db/session.py)
- [`docs/DEPLOY.md`](../../DEPLOY.md)

## Acceptance criteria

1. `/health` remains a cheap liveness endpoint with no database dependency.
2. `/ready` performs a bounded database check and returns HTTP 200 only when
   ready; database failure/timeout returns HTTP 503 with a safe body.
3. Health and readiness probes do not create `api_request_logs` rows or expose
   database/provider details.
4. A protected Vercel Cron route can call `/ready` at most once daily and
   reports a failed readiness result without exposing backend internals.
5. The probe cannot be invoked as an open relay, cannot carry user credentials,
   and does not write dummy application data.
6. The documentation clearly states that the probe is a best-effort experiment
   that may reduce inactivity risk but cannot guarantee that Supabase Free never
   pauses or that FastAPI stays warm.
7. The feature remains within the selected free-tier quotas and can be disabled
   with one environment/configuration change.

## Tasks

### Gather

- [x] **US-P07.G1 — Baseline health behavior.** Measured `/api/v1/health`, `/api/v1/ready`,
  and BFF proxy paths against live production and test environments. Observed 200 OK responses
  and identified the defect where DB failures returned HTTP 200 with degraded body.
- [x] **US-P07.G2 — Inspect middleware paths.** Traced `RequestContextMiddleware` and
  found `/api/v1/health` and `/api/v1/ready` were not in `SKIP_PATH_PREFIXES`, writing ~2,880
  rows/day to `api_request_logs` from Docker healthchecks alone.
- [x] **US-P07.G3 — Confirm scheduler terms.** Confirmed Vercel Hobby plan limit of at most
  once per 24 hours (`0 5 * * *` UTC), `CRON_SECRET` bearer token authentication, fail-closed
  semantics, and zero-cost operation.

### Plan

- [x] **US-P07.P1 — Define status semantics.** `/health` remains purely in-memory (200 OK).
  `/ready` executes `SELECT 1` under a 2.5-second `asyncio.timeout` budget; failure/timeout or
  unconfigured DB in staging/production returns HTTP 503 with `{ status: "degraded", ... }`.
  No schema/migration check per probe to prevent PgBouncer connection churn and rolling deploy issues.
- [x] **US-P07.P2 — Define the Cron contract.** Implemented `/api/cron/supabase-keepalive` in
  Next.js App Router, requiring `Authorization: Bearer <CRON_SECRET>` verified via timing-safe
  buffer comparison. Calls backend `/api/v1/ready` with `cache: "no-store"` and an 8-second timeout.
- [x] **US-P07.P3 — Define cost and disable rules.** Probe is bounded strictly to once daily
  (`0 5 * * *` UTC), stripped of user cookies, writes zero dummy data, and can be disabled instantly
  via `ENABLE_KEEPALIVE_CRON=false` or omitting `CRON_SECRET`.

### Implement

- [x] **US-P07.I1 — Fix readiness semantics.** Added `asyncio.timeout(2.5)` to `backend/app/api/v1/health.py`,
  returning HTTP 503 on database ping timeout, connection failure, or unconfigured production database.
  Safeguarded logs against leaking raw credentials or hostnames.
- [x] **US-P07.I2 — Exclude probe noise.** Added `/api/v1/health` and `/api/v1/ready` to `SKIP_PATH_PREFIXES`
  in `backend/app/core/middleware.py`.
- [x] **US-P07.I3 — Add the protected Cron route.** Implemented `frontend/src/app/api/cron/supabase-keepalive/route.ts`
  and configured `"crons"` schedule in `frontend/vercel.json`. Added `timeout=5.0` and `pool_recycle=1800`
  to `backend/app/db/session.py`.
- [x] **US-P07.I4 — Document the experiment.** Documented probe setup, `CRON_SECRET`, `ENABLE_KEEPALIVE_CRON` toggle,
  and free-tier inactivity caveats in [`docs/DEPLOY.md`](../../DEPLOY.md) and [`docs/user-input-needed.md`](../../user-input-needed.md).

### Test

- [x] **US-P07.T1 — Test status codes.** Added tests in `backend/tests/test_health.py` verifying 200 OK on healthy DB,
  503 on DB connection failure, 503 on query timeout, and 503 on unconfigured DB in production/staging. Asserted no
  hostnames or connection details leak in response.
- [x] **US-P07.T2 — Test probe security.** Added unit tests in `frontend/src/app/api/cron/supabase-keepalive/route.test.ts`
  covering missing secret (503), missing Authorization header (401), invalid scheme (401), mismatched secret (401),
  upstream 503 degraded handling, and upstream network timeout (504).
- [x] **US-P07.T3 — Test logging and quota behavior.** Added `test_probes_skip_request_logging` asserting `/health` and
  `/ready` do not invoke `log_api_request` or persist rows to `api_request_logs`. Asserted no cookies forwarded.
- [x] **US-P07.T4 — Run quality gates.** Backend pytest (281 passed), Ruff clean, mypy clean; frontend bun test (27 passed),
  ESLint clean, TypeScript clean, Turbopack build succeeded; preflight and post-task hooks clean.

### Validate

- [x] **US-P07.V1 — Verify readiness.** Verified healthy probe and simulated degraded probe semantics with automated tests.
- [x] **US-P07.V2 — Verify the scheduled request.** Tested route with timing-safe comparison, cache: no-store, 8s timeout,
  and no user credentials forwarded.
- [x] **US-P07.V3 — Verify the product tradeoff.** Documented $0 constraints and documented that normal user traffic avoids
  inactivity, with this probe serving as an optional, best-effort signal.
- [x] **US-P07.V4 — Close the story.** Documented implementation decisions, evidence, and release updates.

## Evidence to record

- **Status codes & Latency**:
  - Live `/api/v1/health`: HTTP 200 OK, latency ~3ms.
  - Live `/api/v1/ready`: HTTP 200 OK, latency ~1780ms (includes pooler connection handshake).
  - Degraded/failed readiness: returns HTTP 503 Service Unavailable with safe `{ "status": "degraded" }` response.
- **Probe Log Exclusion**:
  - `backend/app/core/middleware.py`: `SKIP_PATH_PREFIXES` includes `/api/v1/health` and `/api/v1/ready`, preventing ~2,880 DB INSERT operations/day.
- **Cron Route & Protection**:
  - Route: `frontend/src/app/api/cron/supabase-keepalive/route.ts`
  - Schedule: `0 5 * * *` (once daily at 05:00 UTC) in `frontend/vercel.json`.
  - Timing-safe `CRON_SECRET` validation via `crypto.timingSafeEqual`.
  - Kill-switch: `ENABLE_KEEPALIVE_CRON=false`.
- **Quality Gates**:
  - `backend/tests/`: 281 tests passed in 3.39s (`test_health.py` 10 passed).
  - Ruff: clean (0 issues).
  - Mypy: clean (101 source files).
  - Frontend `bun test`: 27 passed in 61ms (`route.test.ts` 8 passed).
  - ESLint: clean.
  - TypeScript: clean (`tsc --noEmit`).
  - Next.js Build: production build succeeded via Turbopack with `/api/cron/supabase-keepalive` dynamic route.
  - Preflight & Post-task: passed.

## Safety notes

This is not an uptime guarantee. Do not use a browser tab, an in-process
background task, service-role credentials, or dummy writes as a keepalive. Do
not use this route to keep FastAPI warm; scale-to-zero/cold-start behavior must
be handled separately.

## Story notes

- **2026-09-12**: US-P07 completed. Implemented bounded DB readiness check (2.5s `asyncio.timeout`), HTTP 503 on DB failure/timeout/unconfigured production, request log write suppression for health probes, asyncpg connection timeout hygiene (5.0s handshake timeout, 1800s pool recycle), protected Next.js App Router `/api/cron/supabase-keepalive` route with timing-safe `CRON_SECRET` verification, `ENABLE_KEEPALIVE_CRON` toggle, and Vercel once-daily schedule (`0 5 * * *` UTC). All acceptance criteria met and verified.
