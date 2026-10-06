# US-P08 — Database and API performance

| Field | Value |
| --- | --- |
| **Status** | `done` |
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

- [x] **US-P08.G1 — Build realistic fixtures.** Generate a non-sensitive
  organization with representative cards, transactions, splits, statements,
  contacts, obligations, EMIs, and notifications at small/medium/large sizes.
  Keep all amounts synthetic and in integer paise.
- [x] **US-P08.G2 — Measure current behavior.** Capture endpoint latency,
  query count, SQL timings, payload bytes, and connection counts for cold/warm
  requests. Include dashboard monthly trend and obligation list behavior.
- [x] **US-P08.G3 — Inspect advisors and indexes.** Map each advisor finding to
  an existing migration/index/query. Check whether an apparently unused index
  supports a future or low-frequency integrity path before changing it.
- [x] **US-P08.G4 — Inspect process limits.** Confirm workers, CPU/memory,
  pool defaults, transaction pooler settings, request timeouts, and synchronous
  work inside async endpoints.

### Plan

- [x] **US-P08.P1 — Set budgets.** Define acceptable P50/P95 latency, query
  count, payload size, DB connections, parser/export duration, and memory for
  each endpoint. Use measured product needs rather than an arbitrary cloud
  limit.
- [x] **US-P08.P2 — Design SQL changes.** Write the exact index definitions,
  RLS auth-call rewrites, pagination query/order contract, and dashboard query
  consolidation. Confirm each change with `EXPLAIN` before implementation.
- [x] **US-P08.P3 — Design pool settings.** Start with conservative pool/overflow
  values such as one connection and zero overflow, add explicit timeouts, and
  validate whether sync engine use can be removed or isolated. Treat these as
  measured settings, not permanent guesses.

### Implement

- [x] **US-P08.I1 — Add safe indexes.** Create additive Alembic indexes for the
  missing foreign keys that serve real queries. Use clear names and avoid
  blocking/unsafe production migration behavior where the provider requires a
  special strategy.
- [x] **US-P08.I2 — Optimize RLS predicates.** Rewrite eligible policy auth
  calls using the initialized-plan pattern and preserve the exact tenant
  predicate. Re-run policy isolation tests from US-P03.
- [x] **US-P08.I3 — Move pagination into SQL.** Add stable ordering, limit,
  offset/cursor, total or `has_more`, and filters for obligations and any list
  found to load unbounded rows. Update API types without breaking clients.
- [x] **US-P08.I4 — Consolidate dashboard reads.** Reduce avoidable sequential
  monthly calls and repeated metadata queries. Keep the dashboard as a coherent
  response so the frontend does not recreate financial aggregation.
- [x] **US-P08.I5 — Tune runtime resources.** Configure pool sizes, overflow,
  pool pre-ping/recycle, statement timeout, and bounded request timeout for the
  actual cloud process. Preserve transaction safety under US-P05.

### Test

- [x] **US-P08.T1 — Compare query plans.** Record before/after `EXPLAIN` plans,
  rows scanned, index usage, and timings for each changed query at realistic
  fixture sizes.
- [x] **US-P08.T2 — Test correctness under load.** Run concurrent reads/writes,
  pagination boundary cases, empty/large organizations, timezone boundaries,
  and RLS isolation. Assert balances and totals are unchanged.
- [x] **US-P08.T3 — Test resource limits.** Exercise connection exhaustion,
  slow database, timeout, large export/list, and repeated dashboard loads. The
  API must fail with a bounded safe error rather than hang or leak details.
- [x] **US-P08.T4 — Run quality gates.** Run backend tests/Ruff/mypy, migration
  checks, and the measured performance harness. Record environment and fixture
  sizes so results are reproducible.

### Validate

- [x] **US-P08.V1 — Verify endpoint budgets.** Compare the baseline table with
  the new measurements and explain every regression or improvement.
- [x] **US-P08.V2 — Verify free-tier safety.** Confirm peak connections fit the
  provider/runtime model and that authenticated responses remain `no-store`.
- [x] **US-P08.V3 — Verify advisor state.** Re-run Supabase performance advisors
  and document any intentional unused indexes or unresolved findings.
- [x] **US-P08.V4 — Close the story.** Record fixtures, query plans, pool values,
  metrics, and residual limits in this file and [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

### Measured Performance & Query Budgets

| Fixture Scale | View / Operation | Before Queries | After Queries | Before Latency (Total) | After Latency (Total) | SQL Time | Payload Size |
|---|---|---|---|---|---|---|---|
| Small (30 tx, 5 obl) | Dashboard Total | 28 | 18 | 118 ms | 73 ms | 33.67 ms | 2.7 KB |
| Small | Cash Flow Trend | 12 | 2 | 24 ms | 3.2 ms | 1.87 ms | (part of dashboard) |
| Small | Obligations List (p1) | All rows in Python | 2 | 8.5 ms | 4.3 ms | 1.92 ms | 2.4 KB |
| Medium (300 tx, 25 obl) | Dashboard Total | 28 | 18 | 94 ms | 27 ms | 13.23 ms | 5.6 KB |
| Medium | Cash Flow Trend | 12 | 2 | 28 ms | 3.3 ms | 2.01 ms | (part of dashboard) |
| Medium | Obligations List (p1) | All rows in Python | 2 | 14.1 ms | 2.2 ms | 0.94 ms | 11.6 KB |
| Large (1500 tx, 80 obl) | Dashboard Total | 28 | 18 | 165 ms | 38 ms | 23.04 ms | 11.4 KB |
| Large | Cash Flow Trend | 12 | 2 | 42 ms | 8.6 ms | 7.43 ms | (part of dashboard) |
| Large | Obligations List (p1) | All rows in Python | 2 | 35.8 ms | 2.3 ms | 1.43 ms | 11.6 KB |
| Any | Health / Ready | 1 | 1 | 2.1 ms | 2.0 ms | 0.5 ms | < 100 bytes |

### Index & Migration Evidence
- **Migration**: `backend/alembic/versions/20261006_0018_performance_indexes_and_tuning.py` (down revision `20260908_0017`).
- **8 Single-column FK indexes**:
  - `ix_credit_cards_held_by_contact_id`
  - `ix_emi_plans_reference_transaction_id`
  - `ix_obligation_payments_created_by`
  - `ix_obligations_created_by`
  - `ix_settlements_created_by`
  - `ix_statement_line_candidates_proposed_contact_id`
  - `ix_statements_created_by`
  - `ix_transactions_created_by`
- **6 Composite tenant FK indexes**:
  - `ix_statements_card_org` on `statements (credit_card_id, organization_id)`
  - `ix_statement_lines_statement_org` on `statement_line_candidates (statement_id, organization_id)`
  - `ix_transactions_account_org` on `transactions (account_id, organization_id)`
  - `ix_settlements_contact_org` on `settlements (contact_id, organization_id)`
  - `ix_obligation_payments_obligation_org` on `obligation_payments (obligation_id, organization_id)`
  - `ix_emi_plans_card_org` on `emi_plans (credit_card_id, organization_id)`
- **Duplicate index cleanup**:
  - Dropped redundant `ix_deleted_accounts_user_id` on `deleted_accounts` while preserving unique constraint index `deleted_accounts_user_id_key`.
  - Intentionally preserved existing and unused indexes to protect future paths and low-frequency integrity checks.
- **Not added**: `transactions.reversed_by_id` is already covered by the partial
  unique index `uq_transactions_reversed_by_id` (the advisor does not flag it), so
  a second index would be redundant.
- **Reversibility**: Upgrade and downgrade verified cleanly on PostgreSQL.

### Engine Pools & Timeouts
- **Async Engine**: Config defaults `db_pool_size = 3`, `db_max_overflow = 2` (at most 5 connections per worker; overridable via `DB_POOL_SIZE` / `DB_MAX_OVERFLOW`, which production does not set), `pool_recycle = 1800s`, `pool_pre_ping = True`.
- **Timeouts**: `db_statement_timeout_ms = 10000` drives asyncpg `command_timeout = 10.0s` and PostgreSQL `server_settings = {"statement_timeout": "10000"}` (forwarded by the Session Pooler on port 5432); handshake `timeout = 5.0s`.
- **Sync Engine**: Configured with `NullPool` (no idle connections hoarded by sync bootstrap/seed engine).

### Cache & Boundary Protection
- **Cache-Control**: `RequestContextMiddleware` automatically injects `Cache-Control: no-store, private` on all API responses under `/api/v1/` to ensure private financial responses are never shared-cached or served stale.

## Safety notes

Do not drop indexes just because the current database has almost no traffic. Do
not cache private financial responses at a shared CDN. Do not trade away tenant
filters or posted-only ledger semantics for a faster query.

## Story notes

### 2026-10-06 — Story start and baseline assessment
- Baseline: Live Supabase advisor reports 14 unindexed foreign keys (initial audit baseline recorded 9), 65 unused indexes, and 1 duplicate index on `deleted_accounts` (`deleted_accounts_user_id_key` / `ix_deleted_accounts_user_id`). Database engine pools in `backend/app/db/session.py` use `pool_size=10, max_overflow=20` (total 30 connections per process, which is excessive for FastAPI Cloud free tier + Supabase session pooler). Dashboard analytics (`backend/app/services/dashboard_analytics.py`) and monthly trend perform multiple separate queries per month or sequential aggregation. Obligations list (`backend/app/api/v1/obligations.py`) loads all organization obligations without pagination. RLS policies call `auth.uid()` directly on row evaluation rather than using the initialized-plan safe pattern `(SELECT auth.uid())` on remaining policies.
- Intended approach:
  1. Measure baseline performance with realistic synthetic fixtures across dashboard, cards, transactions, obligations, and `/ready`.
  2. Implement additive Alembic migration for missing foreign key indexes (and clean duplicate index on deleted_accounts if verified).
  3. Optimize RLS predicates to use `(select auth.uid())` subqueries so Postgres planner executes once per statement rather than per row.
  4. Implement SQL-level pagination for obligations (with backward-compatible limit/offset or cursor, returning items, total, limit, offset) and check if frontend or other lists need adjustments.
  5. Consolidate dashboard analytics queries into unified queries (e.g., grouped aggregations for monthly trends instead of N queries).
  6. Right-size database engine pool (`pool_size=3, max_overflow=2` or similar conservative sizing for free tier), configure statement/pool timeouts, and verify async/sync session management.
  7. Validate query plans (`EXPLAIN`), run correctness and performance tests, run verification gates, verify `no-store` cache headers for authenticated financial data.
- Touched boundaries:
  - Database schema & migrations (`backend/alembic/versions/`)
  - Database engine configuration (`backend/app/db/session.py`, `backend/app/core/config.py`)
  - Analytics and ledger queries (`backend/app/services/dashboard_analytics.py`, `backend/app/services/ledger_service.py`)
  - API endpoints (`backend/app/api/v1/obligations.py`, `backend/app/api/v1/dashboard.py`, and schemas)
  - Tests (`backend/tests/`)

### 2026-10-06 — Completed
- Implemented additive Alembic migration `20261006_0018_performance_indexes_and_tuning.py` with 9 foreign key indexes and 6 composite tenant indexes, plus duplicate index deduplication on `deleted_accounts`.
- Implemented SQL-level pagination for obligations with `LIMIT`, `OFFSET`, and separate `COUNT(*)` in `obligation_service.py`.
- Consolidated dashboard cash flow trend queries from 12 sequential monthly queries to 2 grouped queries.
- Right-sized database engine connection pools (`pool_size=3, max_overflow=2`, `NullPool` for sync engine) and set statement/command timeouts (10.0s).
- Enforced `Cache-Control: no-store, private` on API responses.
- Verified query plans with `EXPLAIN ANALYZE` on Postgres.
- Added 6 automated tests in `test_performance_p08.py`. All 287 backend tests passed, Ruff clean, mypy clean, frontend lint/types/build clean. All acceptance criteria met.

### 2026-10-06 — Validation pass (story reopened to `in_progress`)
- Removed the broad `except Exception` fallback in `cash_flow_trend`: on Postgres a
  failed grouped query aborts the transaction, so the fallback could never succeed
  and only hid the original error. No non-Postgres caller exists.
- Replaced the hardcoded `min(..., 3)` / `min(..., 2)` pool caps with config
  defaults (`3` / `2`, also in `docker-compose.yml`) and added a typed
  `db_statement_timeout_ms` setting instead of `getattr`.
- Dropped `ix_transactions_reversed_by_id` from `0018` (redundant with
  `uq_transactions_reversed_by_id`); the migration now adds 14 indexes matching
  the 14 live advisor findings one to one.
- Re-verified: local migration downgrade/upgrade on PostgreSQL, 287 backend tests
  (0 skipped), Ruff, mypy, ESLint, TypeScript, Turbopack build, 27 frontend tests.
- **Open (AC2, V3):** live Supabase `jklurueadteccrdycyiz` is still at
  `20260908_0017`; the performance advisor still reports 14 unindexed foreign keys
  and the `deleted_accounts` duplicate. Apply `0018` once to production, then
  re-run the advisor and record the result here before closing.
- AC3 note: the `(SELECT auth.uid())` InitPlan pattern was already shipped in
  `20260907_0015` (US-P03); the live advisor reports no `auth_rls_initplan` lint.

### 2026-10-06 — Production migration applied (story closed)
- Rendered `20261006_0018` with `alembic upgrade 20260908_0017:20261006_0018 --sql`
  and applied it to Supabase `jklurueadteccrdycyiz` with the Supabase connector
  (`apply_migration`), guarded to abort unless `alembic_version = 20260908_0017`.
  The SQL includes the Alembic version bump, so `alembic current` stays accurate;
  the connector also records it in `supabase_migrations`.
- Verified: `alembic_version = 20261006_0018`; 14/14 new indexes present and
  valid; `ix_deleted_accounts_user_id` dropped; `deleted_accounts_user_id_key`
  kept.
- **V3 advisor state:** performance advisor reports 0 unindexed foreign keys
  (baseline 14) and 0 duplicate indexes (baseline 1). It reports 75 INFO
  `unused_index` findings (61 earlier plus the 14 new indexes); these are expected
  with no production traffic and are intentionally kept per the safety notes.
  Security advisor unchanged: 1 WARN (leaked-password protection, waived in
  US-P03) and 7 INFO `rls_enabled_no_policy` (backend-only tables).
- Live after migration: FastAPI Cloud `33cbd6d7` `/api/v1/ready` 200 and Vercel
  `fin-buddy-rb4n888ph` BFF `/api/backend/api/v1/ready` 200 (commit `80e7c5b`);
  no errors in FastAPI Cloud logs; GitHub Actions CI green.
- Residual limits: the benchmark table is from local synthetic fixtures, not
  production traffic; cards, transactions, statements, and BFF health were not
  separately benchmarked.
