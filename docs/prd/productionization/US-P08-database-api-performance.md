# US-P08 — Database and API performance

| Field | Value |
| --- | --- |
| **Status** | `todo` |
| **Sequence** | 8 |
| **Depends on** | [US-P03](US-P03-supabase-security-boundary.md), [US-P05](US-P05-safe-financial-mutations.md) |
| **One-loop objective** | Reduce avoidable database work and connection pressure while preserving financial correctness. |
| **Primary boundaries** | SQLAlchemy sessions, Postgres indexes/RLS, dashboard analytics, pagination, API payloads |

## User story

**As** a Fin Buddy user on a free-tier deployment
**I want** dashboards and lists to remain responsive as my ledger grows
**So that** cost-saving infrastructure does not make the product feel slow or unreliable.

## Why this matters

Supabase advisors report nine unindexed foreign keys, repeated per-row
`auth.uid()` evaluation in RLS policies, and many unused indexes. The database
is currently small, so unused-index results are not enough evidence to delete
anything. The backend also creates async and sync engines with generous pool
defaults, while dashboard analytics and some pagination can perform more work
than necessary.

## Scope and non-goals

In scope: baseline measurement, safe indexes/RLS predicates, SQL pagination,
dashboard query reduction, pool/timeouts, and response-size discipline. Out of
scope: frontend rendering optimization, covered by US-P14.

## Touchpoints

- [`backend/app/db/session.py`](../../../backend/app/db/session.py)
- [`backend/app/core/config.py`](../../../backend/app/core/config.py)
- [`backend/app/services/ledger_service.py`](../../../backend/app/services/ledger_service.py)
- [`backend/app/services/dashboard_analytics.py`](../../../backend/app/services/dashboard_analytics.py)
- [`backend/app/api/v1/dashboard.py`](../../../backend/app/api/v1/dashboard.py)
- [`backend/app/api/v1/obligations.py`](../../../backend/app/api/v1/obligations.py)
- [`backend/alembic/versions/`](../../../backend/alembic/versions)

## Acceptance criteria

1. Baselines exist for dashboard, cards, transactions, obligations, statements,
   `/ready`, and BFF health, including latency, query count, payload size, and
   connection usage where measurable.
2. The nine missing foreign-key indexes are added only after checking existing
   indexes and migration impact; unused indexes are not removed based solely on
   current low traffic.
3. Applicable RLS predicates use the initialized-plan-safe auth-call pattern
   and retain correct isolation.
4. Obligations and other large lists paginate in SQL with explicit total/has
   more behavior rather than loading the entire organization into Python.
5. Dashboard analytics avoid avoidable sequential/repeated queries while
   preserving the existing money/date/tenant semantics.
6. Database pools, overflow, timeouts, and sync/async engine usage are sized for
   the actual FastAPI Cloud process model and tested under representative load.
7. No authenticated financial response is shared-cached or served stale across
   users/organizations.

## Tasks

### Gather

- [ ] **US-P08.G1 — Build realistic fixtures.** Generate a non-sensitive
  organization with representative cards, transactions, splits, statements,
  contacts, obligations, EMIs, and notifications at small/medium/large sizes.
  Keep all amounts synthetic and in integer paise.
- [ ] **US-P08.G2 — Measure current behavior.** Capture endpoint latency,
  query count, SQL timings, payload bytes, and connection counts for cold/warm
  requests. Include dashboard monthly trend and obligation list behavior.
- [ ] **US-P08.G3 — Inspect advisors and indexes.** Map each advisor finding to
  an existing migration/index/query. Check whether an apparently unused index
  supports a future or low-frequency integrity path before changing it.
- [ ] **US-P08.G4 — Inspect process limits.** Confirm workers, CPU/memory,
  pool defaults, transaction pooler settings, request timeouts, and synchronous
  work inside async endpoints.

### Plan

- [ ] **US-P08.P1 — Set budgets.** Define acceptable P50/P95 latency, query
  count, payload size, DB connections, parser/export duration, and memory for
  each endpoint. Use measured product needs rather than an arbitrary cloud
  limit.
- [ ] **US-P08.P2 — Design SQL changes.** Write the exact index definitions,
  RLS auth-call rewrites, pagination query/order contract, and dashboard query
  consolidation. Confirm each change with `EXPLAIN` before implementation.
- [ ] **US-P08.P3 — Design pool settings.** Start with conservative pool/overflow
  values such as one connection and zero overflow, add explicit timeouts, and
  validate whether sync engine use can be removed or isolated. Treat these as
  measured settings, not permanent guesses.

### Implement

- [ ] **US-P08.I1 — Add safe indexes.** Create additive Alembic indexes for the
  missing foreign keys that serve real queries. Use clear names and avoid
  blocking/unsafe production migration behavior where the provider requires a
  special strategy.
- [ ] **US-P08.I2 — Optimize RLS predicates.** Rewrite eligible policy auth
  calls using the initialized-plan pattern and preserve the exact tenant
  predicate. Re-run policy isolation tests from US-P03.
- [ ] **US-P08.I3 — Move pagination into SQL.** Add stable ordering, limit,
  offset/cursor, total or `has_more`, and filters for obligations and any list
  found to load unbounded rows. Update API types without breaking clients.
- [ ] **US-P08.I4 — Consolidate dashboard reads.** Reduce avoidable sequential
  monthly calls and repeated metadata queries. Keep the dashboard as a coherent
  response so the frontend does not recreate financial aggregation.
- [ ] **US-P08.I5 — Tune runtime resources.** Configure pool sizes, overflow,
  pool pre-ping/recycle, statement timeout, and bounded request timeout for the
  actual cloud process. Preserve transaction safety under US-P05.

### Test

- [ ] **US-P08.T1 — Compare query plans.** Record before/after `EXPLAIN` plans,
  rows scanned, index usage, and timings for each changed query at realistic
  fixture sizes.
- [ ] **US-P08.T2 — Test correctness under load.** Run concurrent reads/writes,
  pagination boundary cases, empty/large organizations, timezone boundaries,
  and RLS isolation. Assert balances and totals are unchanged.
- [ ] **US-P08.T3 — Test resource limits.** Exercise connection exhaustion,
  slow database, timeout, large export/list, and repeated dashboard loads. The
  API must fail with a bounded safe error rather than hang or leak details.
- [ ] **US-P08.T4 — Run quality gates.** Run backend tests/Ruff/mypy, migration
  checks, and the measured performance harness. Record environment and fixture
  sizes so results are reproducible.

### Validate

- [ ] **US-P08.V1 — Verify endpoint budgets.** Compare the baseline table with
  the new measurements and explain every regression or improvement.
- [ ] **US-P08.V2 — Verify free-tier safety.** Confirm peak connections fit the
  provider/runtime model and that authenticated responses remain `no-store`.
- [ ] **US-P08.V3 — Verify advisor state.** Re-run Supabase performance advisors
  and document any intentional unused indexes or unresolved findings.
- [ ] **US-P08.V4 — Close the story.** Record fixtures, query plans, pool values,
  metrics, and residual limits in this file and [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- Baseline and final P50/P95/queries/payload/connections table.
- `EXPLAIN` output summaries and migration revision.
- Pool/timeout settings and process model.
- Advisor result and intentional exceptions.
- Correctness results at each fixture size.

## Safety notes

Do not drop indexes just because the current database has almost no traffic. Do
not cache private financial responses at a shared CDN. Do not trade away tenant
filters or posted-only ledger semantics for a faster query.

## Story notes

_(Append dated implementation decisions and evidence here.)_
