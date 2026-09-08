# Productionization & Product Polish — Progress

> This is the current tracker for the active one-story-per-loop plan. Do not
> mark a story `done` without the acceptance evidence listed in its story file.

| Field | Value |
| --- | --- |
| **Plan** | Productionization & Product Polish |
| **Status** | Active — shared agent workflow complete; application stories queued |
| **Last reviewed** | 2026-09-08 |
| **Completed stories** | 6 / 15 |
| **Current story** | None — US-P05 complete; US-P06 queued |
| **Loop prompt** | [`RALPH-LOOP-PROMPT.md`](RALPH-LOOP-PROMPT.md) |

## Story status

| Story | Status | One-loop objective | Evidence |
| --- | --- | --- | --- |
| [US-P00](US-P00-agent-interoperability-and-cost-guardrails.md) | `done` | Give Codex, Claude Code, and Antigravity one safe loop, user-input handoff, and cost guardrail. | Native manifests, shared skills, local hook scripts, and docs validated on 2026-09-05. |
| [US-P01](US-P01-production-release-gate.md) | `done` | Make the live deployment explicitly production-safe and verify the release gate. | Deployed to FastAPI Cloud (commit a0b2bcf, deployment c016b96d); health & readiness HTTP 200 OK; docs/OpenAPI disabled; demo auth disabled; frontend BFF verified; Supabase Session Pooler DATABASE_URL verified. |
| [US-P02](US-P02-google-oauth.md) | `done` | Complete and test the Google OAuth redirect and session flow. | Live Google provider verified enabled; fixed callback contract enforced; PKCE S256 code exchange implemented; origin-bound single-use state management implemented; safe relative path validator enforced; backend tests (206 passed) and frontend tests (18 passed) verified; UI-09 real browser verification succeeded end-to-end on `https://fin-buddy-dev.vercel.app/login?next=/app/cards`. |
| [US-P03](US-P03-supabase-security-boundary.md) | `done` | Reconcile RLS, grants, security-definer helpers, and Auth security settings. | Alembic migration 20260907_0015 added; RLS enabled across all 23 application tables without FORCE; symmetric WITH CHECK and DELETE policies enforced via (SELECT auth.uid()); table, sequence, routine grants and default privileges revoked from anon, authenticated, PUBLIC; 16 migration/contract tests added (backend 222 passed, frontend 18 passed, lint/types/build clean); UI-06 queued for US-P04. |
| [US-P04](US-P04-tenant-authorization-lifecycle.md) | `done` | Close cross-organization references, role escalation, and deletion-session gaps. | Organization-aware validation across all references; UI-06 Tiered Collaborative Hybrid role enforcement; DeletedAccount tombstone lifecycle; EMI actor profile ID fix; additive reversible migration 20260907_0016; 248 backend & 18 frontend tests passed. |
| [US-P05](US-P05-safe-financial-mutations.md) | `done` | Make financial writes idempotent and concurrency-safe. | RFC 9440 Idempotency-Key engine with SHA-256 payload hashing and cached replay; row-level locking (`with_for_update`) on reversals, drafts, EMIs, obligations, statements, and balance corrections; additive reversible migration 20260908_0017 with partial unique index on reversals; 9 real PostgreSQL concurrency/race tests passed; 257 backend tests & 18 frontend tests passed. |
| [US-P06](US-P06-durable-statement-ingestion.md) | `todo` | Move uploads to durable signed Storage and bound ingestion resources. | — |
| [US-P07](US-P07-readiness-and-keepalive.md) | `todo` | Make readiness truthful and add an optional safe daily database probe. | — |
| [US-P08](US-P08-database-api-performance.md) | `todo` | Baseline and improve queries, indexes, pools, and API payloads. | — |
| [US-P09](US-P09-jobs-logs-errors.md) | `todo` | Make reminders, logs, and public errors safe and bounded. | — |
| [US-P10](US-P10-dues-billing-cockpit.md) | `todo` | Turn the dashboard into a single dues-and-actions cockpit. | — |
| [US-P11](US-P11-fast-capture-relationships.md) | `todo` | Improve capture, corrections, settlements, and debt clarity. | — |
| [US-P12](US-P12-statement-review-notifications.md) | `todo` | Make statement review and notifications truthful, recoverable workflows. | — |
| [US-P13](US-P13-mobile-accessibility-design.md) | `todo` | Complete the mobile, accessibility, motion, and design-token pass. | — |
| [US-P14](US-P14-frontend-performance-verification.md) | `todo` | Add frontend performance, browser, accessibility, and release verification. | — |

## Known starting evidence

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
| None | No human blockers currently blocking US-P05. |

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
