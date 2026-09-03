# US-P07 — Readiness and Supabase keepalive

| Field | Value |
| --- | --- |
| **Status** | `todo` |
| **Sequence** | 7 |
| **Depends on** | [US-P01](US-P01-production-release-gate.md) |
| **One-loop objective** | Make liveness/readiness truthful and add a low-frequency, optional database activity probe. |
| **Primary boundaries** | FastAPI health routes, request middleware, Vercel Cron, Supabase database |

## User story

**As** the Fin Buddy owner
**I want** health checks to distinguish a running API from a usable database and optionally keep the free database active
**So that** deployment failures are visible without adding a paid monitoring or always-on service.

## Why this matters

`/health` is intentionally cheap and does not query the database. `/ready`
executes `SELECT 1`, but currently can return HTTP 200 with a degraded body.
Both paths are persisted by request middleware, so a periodic probe creates
unnecessary database log writes. Supabase Free may pause after low activity;
the proposed check is only a best-effort activity experiment.

## Scope and non-goals

In scope: status codes, bounded DB readiness, probe logging, Vercel Cron route,
secret verification, and operational evidence. Out of scope: keeping FastAPI
warm, user reminders, or paid monitoring.

## Touchpoints

- [`backend/app/api/v1/health.py`](../../../backend/app/api/v1/health.py)
- [`backend/app/core/middleware.py`](../../../backend/app/core/middleware.py)
- [`frontend/src/app/api/`](../../../frontend/src/app/api)
- [`frontend/vercel.json`](../../../frontend/vercel.json)
- [`backend/app/db/session.py`](../../../backend/app/db/session.py)
- [`docs/DEPLOY.md`](../../DEPLOY.md)

## Acceptance criteria

1. `/health` remains a cheap liveness endpoint with no database dependency.
2. `/ready` performs a bounded database check and returns HTTP 200 only when
   ready; database failure/timeout returns HTTP 503 with a safe body.
3. Health and readiness probes do not create `api_request_logs` rows or expose
   database/provider details.
4. A protected Vercel Cron route can call `/ready` once daily and reports a
   failed readiness result without exposing backend internals.
5. The probe cannot be invoked as an open relay, cannot carry user credentials,
   and does not write dummy application data.
6. The documentation clearly states that the probe reduces inactivity risk but
   cannot guarantee that Supabase Free never pauses or that FastAPI stays warm.
7. The feature remains within the selected free-tier quotas and can be disabled
   with one environment/configuration change.

## Tasks

### Gather

- [ ] **US-P07.G1 — Baseline health behavior.** Measure `/health`, `/ready`,
  BFF health, status codes, response bodies, latency, cache headers, and request
  log row counts in a safe environment. Record cold/warm observations
  separately.
- [ ] **US-P07.G2 — Inspect middleware paths.** Trace request ID creation,
  response logging, background tasks, exception handling, and any cache layer.
  Identify all probe paths that must be excluded without suppressing useful
  application errors.
- [ ] **US-P07.G3 — Confirm scheduler terms.** Verify the Vercel project plan,
  Cron schedule granularity, secret behavior, production-only execution, and
  quota impact. Record a fallback only if the selected scheduler is unavailable.

### Plan

- [ ] **US-P07.P1 — Define status semantics.** Specify liveness, readiness,
  degraded response, timeout budget, safe body, and monitoring interpretation.
  Decide whether readiness also checks migration revision or only connectivity.
- [ ] **US-P07.P2 — Define the Cron contract.** Use a route such as
  `/api/cron/supabase-keepalive`, verify `Authorization: Bearer CRON_SECRET`,
  call the backend `/api/v1/ready` with `no-store`, and return a concise
  success/failure status. Use a once-daily UTC schedule rather than every few
  seconds or an in-process loop.
- [ ] **US-P07.P3 — Define cost and disable rules.** Record normal user traffic
  behavior, probe frequency, function invocation budget, database log policy,
  and the exact environment flag/schedule change that disables the experiment.

### Implement

- [ ] **US-P07.I1 — Fix readiness semantics.** Add a bounded timeout and return
  HTTP 503 on DB failure while keeping error details internal. Preserve the
  cheap liveness route.
- [ ] **US-P07.I2 — Exclude probe noise.** Skip `/health`, `/ready`, and the
  internal Cron path from database request logging, or route them to a bounded
  platform log. Ensure errors and latency needed for operations remain visible.
- [ ] **US-P07.I3 — Add the protected Cron route.** Add the Vercel route and
  daily schedule. Use server-only `BACKEND_URL`, `CRON_SECRET`, fetch timeout,
  `cache: no-store`, and no user/session cookies. Do not call the reminder POST
  endpoint.
- [ ] **US-P07.I4 — Document the experiment.** Add setup, disable, expected
  output, quota caveat, and failure interpretation to [`docs/DEPLOY.md`](../../DEPLOY.md).

### Test

- [ ] **US-P07.T1 — Test status codes.** Mock healthy, unavailable, timed-out,
  and malformed database responses; assert `/ready` returns the right status
  and no sensitive detail.
- [ ] **US-P07.T2 — Test probe security.** Cover missing/invalid secret,
  method mismatch, arbitrary query/body input, redirect behavior, backend
  timeout, and upstream non-200 response.
- [ ] **US-P07.T3 — Test logging and quota behavior.** Assert probes do not
  insert request-log rows, do not forward auth cookies, and produce at most one
  bounded upstream call per invocation.
- [ ] **US-P07.T4 — Run quality gates.** Run backend tests/Ruff/mypy, frontend
  lint/typecheck/build, `docker compose config --quiet`, and a deployed safe
  probe smoke where scheduler credentials permit.

### Validate

- [ ] **US-P07.V1 — Verify readiness.** Bring the database check through a
  healthy and failed state and confirm load balancer/monitoring semantics match
  the documented status codes.
- [ ] **US-P07.V2 — Verify the scheduled request.** Confirm one Cron invocation
  reaches `/ready`, creates no application data, uses no user token, and
  records enough evidence to investigate a failure.
- [ ] **US-P07.V3 — Verify the product tradeoff.** Record whether normal user
  activity already avoids pausing, whether the probe changes that observation,
  and whether it should remain enabled.
- [ ] **US-P07.V4 — Close the story.** Record schedule, secret name, status
  behavior, logs, latency, and provider caveats in this file and
  [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- Before/after status codes and latency.
- Failure response and timeout behavior.
- Cron schedule and protected-route test output.
- Request-log row comparison.
- Decision to retain, disable, or revisit the keepalive.

## Safety notes

This is not an uptime guarantee. Do not use a browser tab, an in-process
background task, service-role credentials, or dummy writes as a keepalive. Do
not use this route to keep FastAPI warm; scale-to-zero/cold-start behavior must
be handled separately.

## Story notes

_(Append dated implementation decisions and evidence here.)_
