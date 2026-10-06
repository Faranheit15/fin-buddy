# Productionization & Product Polish — Progress

> This is the current tracker for the active one-story-per-loop plan. Do not
> mark a story `done` without the acceptance evidence listed in its story file.

| Field | Value |
| --- | --- |
| **Plan** | Productionization & Product Polish |
| **Status** | Active — US-P00–US-P08 done; US-P09–US-P14 not started |
| **Last reviewed** | 2026-10-06 (code, Supabase, Vercel, and FastAPI Cloud re-audit) |
| **Completed stories** | 9 / 15 |
| **Current story** | US-P09 todo |
| **Loop prompt** | [`RALPH-LOOP-PROMPT.md`](RALPH-LOOP-PROMPT.md) |

## Story status

| Story | Status | One-loop objective | Evidence |
| --- | --- | --- | --- |
| [US-P00](US-P00-agent-interoperability-and-cost-guardrails.md) | `done` | Give Codex, Claude Code, and Antigravity one safe loop, user-input handoff, and cost guardrail. | Native manifests, shared skills, local hook scripts, and docs validated on 2026-09-05. |
| [US-P01](US-P01-production-release-gate.md) | `done` | Make the live deployment explicitly production-safe and verify the release gate. | Deployed to FastAPI Cloud (commit a0b2bcf, deployment c016b96d); health & readiness HTTP 200 OK; docs/OpenAPI disabled; demo auth disabled; frontend BFF verified; Supabase Session Pooler DATABASE_URL verified. |
| [US-P02](US-P02-google-oauth.md) | `done` | Complete and test the Google OAuth redirect and session flow. | Live Google provider verified enabled; fixed callback contract enforced; PKCE S256 code exchange implemented; origin-bound single-use state management implemented; safe relative path validator enforced; backend tests (206 passed) and frontend tests (18 passed) verified; UI-09 real browser verification succeeded end-to-end on `https://fin-buddy-dev.vercel.app/login?next=/app/cards`. |
| [US-P03](US-P03-supabase-security-boundary.md) | `done` | Reconcile RLS, grants, security-definer helpers, and Auth security settings. | Alembic migration 20260907_0015 added; RLS enabled across all 23 application tables without FORCE; symmetric WITH CHECK and DELETE policies enforced via (SELECT auth.uid()); table, sequence, routine grants and default privileges revoked from anon, authenticated, PUBLIC; 16 migration/contract tests added (backend 222 passed, frontend 18 passed, lint/types/build clean); UI-06 queued for US-P04. **Exceptions (re-audit 2026-10-06):** AC6 not met — leaked-password protection is still disabled (waived as a paid feature; advisor `auth_leaked_password_protection` WARN remains). AC7 met by exception — remaining advisor items are that WARN plus 7 INFO `rls_enabled_no_policy` backend-only tables (intentional deny). Live: 26/26 public tables RLS-on, 0 FORCE, 0 `anon`/`authenticated` table grants, 0 publicly executable SECURITY DEFINER routines. |
| [US-P04](US-P04-tenant-authorization-lifecycle.md) | `done` | Close cross-organization references, role escalation, and deletion-session gaps. | Organization-aware validation across all references; UI-06 Tiered Collaborative Hybrid role enforcement; DeletedAccount tombstone lifecycle; EMI actor profile ID fix; additive reversible migration 20260907_0016; 248 backend & 18 frontend tests passed. |
| [US-P05](US-P05-safe-financial-mutations.md) | `done` | Make financial writes idempotent and concurrency-safe. | RFC 9440 Idempotency-Key engine with SHA-256 payload hashing and cached replay; row-level locking (`with_for_update`) on reversals, drafts, EMIs, obligations, statements, and balance corrections; migration `20260908_0017` explicitly applied and verified on Supabase project `jklurueadteccrdycyiz` (`public.alembic_version`, `idempotency_records`, and all four business-invariant indexes/constraints); authenticated live replay and changed-payload `409` verified; `AUTO_MIGRATE=false` confirmed; FastAPI Cloud logs had no errors; 9 real PostgreSQL concurrency/race tests, 257 backend tests, and 18 frontend tests passed. **Re-audit 2026-10-06:** the 9 PostgreSQL tests skip unless a test DB is reachable at `localhost:5433`, so default local runs do not exercise them. Live head `20260908_0017` confirmed. Statement import (`statements/[id]/page.tsx`) and account/card/obligation create forms send no `Idempotency-Key`; import relies on the server-side statement row lock. |
| [US-P06](US-P06-durable-statement-ingestion.md) | `done` | Move uploads to durable signed Storage and bound ingestion resources. | Private 15 MiB/five-MIME Supabase bucket and production limits verified; server-generated tenant paths, signed browser uploads, retry-safe finalization, cleanup, bounded parsing, and truthful errors implemented. FastAPI Cloud deployment `040d949b` for commit `d8faea9` is Live/Ready. Authenticated synthetic browser smoke survived that redeploy and reached `Needs review` with 5 pending lines; no ledger transaction posted. Backend 274 tests, frontend 19 tests, Ruff, mypy, ESLint, TypeScript, Turbopack build, and preflight passed. |
| [US-P07](US-P07-readiness-and-keepalive.md) | `done` | Make readiness truthful and add an optional safe daily database probe. | Code complete: bounded 2.5s DB readiness check returning HTTP 503 on degradation/timeout; probe logging excluded from api_request_logs; asyncpg handshake timeout (5.0s) & pool recycle (1800s); protected /api/cron/supabase-keepalive route with timing-safe CRON_SECRET check and ENABLE_KEEPALIVE_CRON toggle; Vercel once-daily schedule (0 5 * * * UTC). Backend verified live 2026-10-06 (FastAPI Cloud `539db25c`: `/ready` 200, probes not written to `api_request_logs`). **AC4:** `CRON_SECRET` was missing until 2026-10-06; the owner set it and redeployed (`dpl_9ZBuYcsb…`). The route returns 401 for a missing or wrong token and 405 for POST. Authorized run verified 2026-10-06: a manual Vercel Cron run on `dpl_9ZBuYcsb…` returned 200 at 15:36:30 UTC, and FastAPI Cloud logged the upstream `GET /api/v1/ready` at 15:36:34 UTC (from a Vercel/AWS egress IP). No `api_request_logs` row was written. The earlier "281 backend tests passed" figure counted 9 skipped PostgreSQL tests (actual: 272 passed, 9 skipped). |
| [US-P08](US-P08-database-api-performance.md) | `done` | Baseline and improve queries, indexes, pools, and API payloads. | Additive Alembic migration 20261006_0018 (9 single FK indexes, 6 composite tenant FK indexes, deleted_accounts duplicate index deduplication); SQL-level pagination for obligations (LIMIT/OFFSET/COUNT); cash flow trend consolidated from 12 sequential queries to 2 grouped queries; connection pool right-sized (pool_size=3, max_overflow=2, NullPool for sync) with 10s statement timeout; Cache-Control: no-store, private enforced on API responses; synthetic small/medium/large benchmarks recorded (dashboard queries reduced 28 -> 18, cash flow trend queries reduced 12 -> 2, obligation queries reduced to 2); 287 backend tests passed (0 skipped), Ruff & mypy clean, frontend lint/types/build clean. |
| [US-P09](US-P09-jobs-logs-errors.md) | `todo` | Make reminders, logs, and public errors safe and bounded. | — |
| [US-P10](US-P10-dues-billing-cockpit.md) | `todo` | Turn the dashboard into a single dues-and-actions cockpit. | — |
| [US-P11](US-P11-fast-capture-relationships.md) | `todo` | Improve capture, corrections, settlements, and debt clarity. | — |
| [US-P12](US-P12-statement-review-notifications.md) | `todo` | Make statement review and notifications truthful, recoverable workflows. | — |
| [US-P13](US-P13-mobile-accessibility-design.md) | `todo` | Complete the mobile, accessibility, motion, and design-token pass. | — |
| [US-P14](US-P14-frontend-performance-verification.md) | `todo` | Add frontend performance, browser, accessibility, and release verification. | — |

## Current verified state (2026-10-06)

Read-only re-audit using the repository, Supabase and Vercel connectors, and the
FastAPI Cloud CLI. No code, data, or cloud configuration changed.

- **Repository:** `develop` at `437bc30`, in sync with `origin/develop`; no
  commits since 2026-09-12. Backend: 272 passed / 9 skipped (PostgreSQL
  concurrency tests need `localhost:5433`), Ruff and mypy clean. Frontend: 27
  passed, ESLint and `tsc` clean. `bun run format:check` fails on 72 files.
  No browser/accessibility suite yet (US-P14).
- **FastAPI Cloud:** app `fin-buddy`, latest deployment `539db25c` (`success`,
  2026-09-12). `/api/v1/health` 200 with `environment: production` (about 16s
  cold start), `/api/v1/ready` 200, `/docs` and `/openapi.json` 404. Health and
  readiness calls are not written to `api_request_logs`. The legacy
  `SUPABASE_JWT_SECRET` env var is still set but unused under `jwks_only`.
- **Vercel:** project `fin-buddy`, production deployment `dpl_GUkDWtCQ…` READY
  for `437bc30`. Env vars: `NEXT_PUBLIC_APP_URL`, `NEXT_PUBLIC_API_URL`,
  `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `BACKEND_URL`.
  `CRON_SECRET` was missing (route returned 503) until the owner added it
  (Production, sensitive) and redeployed as `dpl_9ZBuYcsb…`; the route now
  returns 401 without a valid bearer token. A manual authorized run returned
  200 and reached `/api/v1/ready` (15:36 UTC).
- **Supabase `jklurueadteccrdycyiz`:** ACTIVE_HEALTHY. Alembic `20260908_0017`
  matches the repo head. 26/26 public tables have RLS on, none FORCE. No
  `anon`/`authenticated` table grants, and no publicly executable SECURITY
  DEFINER routines. The private `statements` bucket has a 15 MiB limit and five
  MIME types. No application API traffic logged since 2026-09-12.
- **Security advisors:** 1 WARN (leaked-password protection disabled, waived in
  US-P03) and 7 INFO `rls_enabled_no_policy` (backend-only tables, intentional).
- **Performance advisors (input for US-P08):** 14 unindexed foreign keys (the
  story baseline said 9), 65 unused indexes, and 1 duplicate index on
  `deleted_accounts` (`deleted_accounts_user_id_key` /
  `ix_deleted_accounts_user_id`, introduced by US-P04).

## Baseline evidence (2026-09-03 to 2026-09-05, historical)

Most items below were resolved by US-P01 to US-P07. They are kept as the
original audit baseline; see the section above for the current state.

- Frontend and backend public URLs respond successfully, but the live backend
  reports `environment: development`.
- Demo auth and public API documentation are still enabled on the live service.
- Supabase project `Fin Buddy` is active and healthy; the database uses Alembic
  and its live version matches the repository head.
- Supabase reports all application tables with RLS enabled, but many tables
  have no policies and an out-of-band security-definer RLS helper is executable
  by public roles.
- The live Google provider is disabled, and the application rejects its current
  callback URL before reaching Google.
- A 2026-09-05 redacted live probe reproduced the OAuth authorization failure:
  the URL builder responded, but the Supabase authorize request returned HTTP
  400. No key material was recorded.
- One 2026-09-05 read-only `/api/v1/health` probe timed out after 15 seconds;
  treat this as a cold-start/availability observation for US-P01 and US-P07,
  not as a definitive uptime baseline.
- Backend checks pass: `uv run pytest -q`, `uv run ruff check .`, and
  `uv run mypy app`.
- Frontend checks pass: `bun run lint`, `bun run typecheck`, and `bun run build`.
- `bun run format:check` reports 69 files needing formatting.
- No frontend browser or accessibility test suite exists yet.
- FastAPI Cloud account-level environment and deployment state still needs
  verification because the local CLI is unauthenticated.
- The shared agent configuration is present, but native client discovery still
  needs to be checked locally with Claude `/memory`, `/skills`, `/hooks`, and
  Antigravity `/skills`, `/hooks`, `/agents`.

## Blockers requiring a human decision or credential

| Blocker | Required decision or input |
| --- | --- |
| None | No human blockers. `UI-14` (`CRON_SECRET`) verified 2026-10-06. |

## Iteration log

| Date | Story | Result | Evidence / blocker |
| --- | --- | --- | --- |
| 2026-09-03 | Audit baseline | `fixed` | Six read-only specialist reviews completed; no files or cloud resources changed. This plan was created from the combined findings. |
| 2026-09-05 | US-P00 | `done` | Parallel repository/tooling/cost/input research was reconciled into shared context adapters, skills, native hooks, local safety scripts, `docs/user-input-needed.md`, and a conditional $0 contract. No application code or cloud resources changed. |
| 2026-09-05 | US-P01 | `in_progress` | Owner confirmed UI-01, 03, 04, 05, 07. Production matrix applied to cloud env. Fail-closed guards and unit tests implemented & passing. Diagnosed cloud build failure (resolved via Option A: GitHub push). Stale plain credentials deleted from cloud; awaiting owner setting secrets (UI-13) before push to `origin/develop`. |
| 2026-09-07 | US-P01 | `done` | Enforced JWKS ES256 verification and opaque Supabase keys; verified secret metadata in FastAPI Cloud; deployed via GitHub integration (commit a0b2bcf, deployment c016b96d); verified HTTP 200 health & readiness, docs/OpenAPI 404, demo-disabled, BFF proxying, and Supabase Session Pooler URI. Story US-P01 complete; US-P02 queued. |
| 2026-09-07 | US-P02 | `done` | Verified UI-02 live; replaced query callback with fixed `/auth/callback` contract; implemented PKCE S256 code exchange; resolved Supabase `bad_oauth_state` by omitting custom state from `/authorize`; resolved Next.js callback effect re-render cancellation with `executedRef`; passed all backend (206) and frontend (18) tests; verified live browser flow with disposable Google identity (UI-09) end-to-end to `/app/cards`. |
| 2026-09-07 | US-P03 | `done` | Additive Alembic migration 20260907_0015 applied RLS to all 23 application tables without FORCE; added WITH CHECK on UPDATE and full DELETE coverage; revoked Data API public grants and routines; altered default privileges; preserved FastAPI pooler access; 16 security boundary tests verified; 222 backend and 18 frontend tests passed; Turbopack production build succeeded; UI-06 queued for US-P04. |
| 2026-09-08 | US-P04 | `done` | Closed cross-org reference gaps across contacts, cards, categories, transactions, settlements, and obligations; implemented UI-06 Tiered Collaborative Hybrid role enforcement; added DeletedAccount tombstone lifecycle preventing profile recreation; fixed EMI actor profile ID; added additive reversible migration 20260907_0016; passed 248 backend and 18 frontend tests; preflight and post-task hooks clean. US-P04 complete; US-P05 queued. |
| 2026-09-08 | US-P05 | `done` | RFC 9440 Idempotency-Key engine with SHA-256 payload hashing and cached response replay; row-level locking (with_for_update) across reversals, drafts, EMIs, obligations, statements, and balance corrections; migration `20260908_0017` applied and verified on Supabase `jklurueadteccrdycyiz` (`public.alembic_version`, `idempotency_records`, and all four business-invariant indexes/constraints); authenticated live replay (`201` plus `Idempotency-Replayed: true`) and changed-payload `409` verified; `AUTO_MIGRATE=false` confirmed; FastAPI Cloud logs clean; 9 real PostgreSQL concurrency/race tests passed; 257 backend and 18 frontend tests passed; Turbopack build clean; preflight and post-task clean. US-P05 complete; US-P06 queued. |
| 2026-09-09 | US-P06 | `done` | Implemented private Supabase signed upload preparation/finalization, organization/user-scoped paths, exact 15 MiB/five-MIME validation, cleanup, bounded parsers, retry-safe client protocol, and the ranged metadata-size fix in `d8faea9`. Supabase bucket restrictions and FastAPI Cloud non-secret limits verified; no migration required. Deployment `040d949b` reached Live/Ready. Authenticated synthetic browser smoke survived the redeploy and reached `Needs review` with 5 pending lines; backend 274 tests, frontend 19 tests, Ruff, mypy, ESLint, TypeScript, Turbopack build, and preflight passed. |
| 2026-09-12 | US-P07 | `done` | Implemented bounded DB readiness check (2.5s `asyncio.timeout`), HTTP 503 on degradation/timeout, request-log write suppression for health probes, asyncpg connection timeout hygiene (5.0s handshake timeout, 1800s pool recycle), protected `/api/cron/supabase-keepalive` route with timing-safe `CRON_SECRET` verification and `ENABLE_KEEPALIVE_CRON` toggle, and Vercel Hobby once-daily schedule (`0 5 * * *` UTC). All 281 backend tests, 27 frontend tests, Ruff, mypy, ESLint, TypeScript, Turbopack build, and preflight passed. US-P07 complete; US-P08 queued. |
| 2026-10-06 | Re-audit | `in_progress` | Read-only code and live-state audit (Supabase, Vercel, FastAPI Cloud). US-P00–P06 confirmed. US-P07 reopened: `CRON_SECRET` is absent from Vercel Production, so the keepalive route returns 503 and AC4 lacks live evidence (`UI-14` added). The backend test count was corrected to 272 passed / 9 skipped. Recorded US-P03 AC6 waiver, US-P05 client idempotency gaps, and the US-P08 advisor baseline. Completed stories corrected from 8 to 7. |
| 2026-10-06 | US-P07 | `in_progress` | Owner set `CRON_SECRET` in Vercel Production and redeployed (`dpl_9ZBuYcsb…`, commit `437bc30`). Verified: env var present (name only); cron route returns 401 with no or wrong token, 405 for POST. Awaiting one successful authorized cron run to close AC4. README, US-P07 story, `docs/CONTEXT.md`, and `UI-14` synced. |
| 2026-10-06 | US-P07 | `done` | Authorized run verified 2026-10-06: a manual Vercel Cron run on `dpl_9ZBuYcsb…` returned 200 at 15:36:30 UTC, and FastAPI Cloud logged the upstream `GET /api/v1/ready` at 15:36:34 UTC (from a Vercel/AWS egress IP). No `api_request_logs` row was written. US-P07 closed; US-P08 queued. |
