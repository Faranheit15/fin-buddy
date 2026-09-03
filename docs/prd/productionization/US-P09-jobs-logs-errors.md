# US-P09 — Jobs, logs, and error hygiene

| Field | Value |
| --- | --- |
| **Status** | `todo` |
| **Sequence** | 9 |
| **Depends on** | [US-P05](US-P05-safe-financial-mutations.md), [US-P07](US-P07-readiness-and-keepalive.md) |
| **One-loop objective** | Make reminders, operational logs, and public errors bounded, private, and retry-safe. |
| **Primary boundaries** | Reminder job, notifications, middleware logging, exception mapping, provider errors |

## User story

**As** a Fin Buddy owner
**I want** reminders and diagnostics to be reliable without exposing my financial data
**So that** background work helps me and does not create duplicate mail, noisy database growth, or security leaks.

## Why this matters

The reminder job scans several resources with N+1 queries and has no durable
run lock or delivery marker. Request logs are written through fire-and-forget
database tasks, while provider bodies and stack traces can leak through public
errors. Operational tables can grow on the same free database used for user
data.

## Scope and non-goals

In scope: reminder scheduling contract, idempotent delivery, query/chunk
limits, structured logging, retention/access, request IDs, and safe error
mapping. Out of scope: the daily keepalive route itself, covered by US-P07,
and the detailed notifications UI, covered by US-P12.

## Touchpoints

- [`backend/app/api/v1/jobs.py`](../../../backend/app/api/v1/jobs.py)
- [`backend/app/services/email_service.py`](../../../backend/app/services/email_service.py)
- [`backend/app/services/notification_service.py`](../../../backend/app/services/notification_service.py)
- [`backend/app/core/middleware.py`](../../../backend/app/core/middleware.py)
- [`backend/app/core/exceptions.py`](../../../backend/app/core/exceptions.py)
- [`backend/app/infrastructure/supabase_auth.py`](../../../backend/app/infrastructure/supabase_auth.py)
- [`backend/app/models/`](../../../backend/app/models)

## Acceptance criteria

1. A reminder job is authenticated, bounded, serialized or idempotent, and safe
   to retry without duplicate delivery.
2. Reminder queries are set-based or chunked, and the job reports counts and
   failures without loading the entire organization universe into memory.
3. Email is optional and correctly configured; in-app notifications remain the
   primary path when no valid provider/sender is configured.
4. Public errors are generic and actionable; provider bodies, stack traces,
   secrets, tokens, and sensitive financial metadata remain internal.
5. Request IDs are server-owned, logs have access controls and retention, and
   fire-and-forget database writes cannot silently lose required audit data.
6. Log growth and job work remain bounded on the free database/runtime.
7. Tests cover duplicate jobs, provider failure, malformed input, retention,
   log redaction, and request-ID behavior.

## Tasks

### Gather

- [ ] **US-P09.G1 — Trace reminder execution.** Map scheduler → protected job
  endpoint → profile/org/card/EMI queries → notification/email send → log. Record
  current N+1 behavior, failure handling, sender address, and duplicate risk.
- [ ] **US-P09.G2 — Inventory sensitive logging.** Search request, error,
  auth, parser, provider, and admin logs for tokens, raw bodies, stack traces,
  paths, IPs, user agents, organization IDs, and financial values. Classify what
  is needed for support versus what should be redacted.
- [ ] **US-P09.G3 — Measure retention.** Count operational rows, estimate
  daily growth including probes, inspect existing purge behavior, and define a
  safe retention window for the free database.

### Plan

- [ ] **US-P09.P1 — Define delivery identity.** Choose a unique key based on
  organization, user, reminder type, source object, threshold/date, and provider
  so retries and overlapping runs cannot send the same reminder twice.
- [ ] **US-P09.P2 — Define job execution.** Specify lock/lease, batch size,
  timeout, continuation behavior, maximum work per request, result counters,
  and how a failed batch is retried.
- [ ] **US-P09.P3 — Define logging policy.** Separate platform logs from
  user-facing audit logs, specify redaction and access roles, choose retention,
  and define which paths are intentionally not persisted in Postgres.
- [ ] **US-P09.P4 — Define error taxonomy.** Map validation, auth, provider,
  database, parser, rate-limit, and unexpected failures to stable public codes
  and internal diagnostics.

### Implement

- [ ] **US-P09.I1 — Harden reminder execution.** Add batch/chunk processing,
  a durable lock or idempotent run key, sent-marker/delivery key, timeout, and
  safe retry behavior. Keep `X-Job-Secret` backend-only and do not accept it in
  query strings.
- [ ] **US-P09.I2 — Reduce reminder queries.** Replace N+1 scans with bounded
  joins/queries where practical, avoid recomputing the same ledger totals for
  every recipient, and record per-batch failures without aborting all safe work.
- [ ] **US-P09.I3 — Make email truthful.** Require a valid configured sender and
  provider before sending, expose provider failures generically, and align
  settings copy with actual card/EMI reminder coverage. Keep in-app reminders
  useful without email.
- [ ] **US-P09.I4 — Harden logs.** Generate request IDs server-side, redact
  provider/auth data, replace required fire-and-forget audit writes with a
  reliable bounded path, and keep probe/health noise out of operational tables.
- [ ] **US-P09.I5 — Enforce retention.** Add or verify bounded purge for request,
  error, and activity logs, with privileged access only and no deletion of
  financial ledger history.

### Test

- [ ] **US-P09.T1 — Test job replay.** Run overlapping/retried jobs with a fake
  provider and assert one delivery per delivery identity, stable counters, and
  recoverable failed batches.
- [ ] **US-P09.T2 — Test resource bounds.** Exercise large recipient sets,
  provider slowness, database failure, invalid secret, and timeout. Assert the
  job stops within its budget and can resume safely.
- [ ] **US-P09.T3 — Test redaction.** Assert public responses never contain raw
  provider bodies, JWTs, API keys, file paths, stack traces, or sensitive
  financial values. Assert request IDs cannot be spoofed into logs.
- [ ] **US-P09.T4 — Test retention/access.** Verify purge age boundaries,
  protected admin access, and preservation of ledger/activity evidence required
  by the product.
- [ ] **US-P09.T5 — Run quality gates.** Run backend tests, Ruff, mypy, migration
  checks, and a safe job invocation with a fake email provider.

### Validate

- [ ] **US-P09.V1 — Verify a real scheduled run.** With email disabled or a
  controlled test recipient, run the protected job and record batches, duration,
  failures, database writes, and duplicate behavior.
- [ ] **US-P09.V2 — Verify public errors.** Exercise invalid auth, provider,
  parser, and database paths through the BFF and confirm copy is helpful but
  non-sensitive.
- [ ] **US-P09.V3 — Verify storage growth.** Confirm log retention and probe
  exclusions keep operational data within the agreed free-tier budget.
- [ ] **US-P09.V4 — Close the story.** Record delivery identity, lock/batch
  design, redaction examples, retention evidence, and residual provider limits
  in this file and [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- Job/query/batch baseline and final behavior.
- Delivery-key and retry test results.
- Public error/redaction test output.
- Retention policy and access-role evidence.
- Provider/sender configuration decision.

## Safety notes

Never run a reminder test against real recipients without an explicit test
configuration. Never store tokens, secrets, or raw financial exports in logs.
Do not solve operational reliability by writing fake financial activity.

## Story notes

_(Append dated implementation decisions and evidence here.)_
