# Productionization & Product Polish — Progress

> This is the current tracker for the active one-story-per-loop plan. Do not
> mark a story `done` without the acceptance evidence listed in its story file.

| Field | Value |
| --- | --- |
| **Plan** | Productionization & Product Polish |
| **Status** | Active — shared agent workflow complete; application stories queued |
| **Last reviewed** | 2026-09-07 |
| **Completed stories** | 2 / 15 |
| **Current story** | US-P02 — Google OAuth redirect & session flow (in_progress) |
| **Loop prompt** | [`RALPH-LOOP-PROMPT.md`](RALPH-LOOP-PROMPT.md) |

## Story status

| Story | Status | One-loop objective | Evidence |
| --- | --- | --- | --- |
| [US-P00](US-P00-agent-interoperability-and-cost-guardrails.md) | `done` | Give Codex, Claude Code, and Antigravity one safe loop, user-input handoff, and cost guardrail. | Native manifests, shared skills, local hook scripts, and docs validated on 2026-09-05. |
| [US-P01](US-P01-production-release-gate.md) | `done` | Make the live deployment explicitly production-safe and verify the release gate. | Deployed to FastAPI Cloud (commit a0b2bcf, deployment c016b96d); health & readiness HTTP 200 OK; docs/OpenAPI disabled; demo auth disabled; frontend BFF verified; Supabase Session Pooler DATABASE_URL verified. |
| [US-P02](US-P02-google-oauth.md) | `in_progress` | Complete and test the Google OAuth redirect and session flow. | Live Google provider verified enabled with client ID `1017490367160-eja7fk6vt7m9fioh0lj9rhfoha46b2uv.apps.googleusercontent.com`; fixed callback contract enforced; PKCE S256 code exchange implemented; origin-bound single-use state management implemented; safe relative path validator enforced; backend tests (206 passed) and frontend tests (16 passed) verified; awaiting UI-09 disposable test account for real browser verification. |
| [US-P03](US-P03-supabase-security-boundary.md) | `todo` | Reconcile RLS, grants, security-definer helpers, and Auth security settings. | — |
| [US-P04](US-P04-tenant-authorization-lifecycle.md) | `todo` | Close cross-organization references, role escalation, and deletion-session gaps. | — |
| [US-P05](US-P05-safe-financial-mutations.md) | `todo` | Make financial writes idempotent and concurrency-safe. | — |
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
| Disposable test account | Provide or perform real browser login with a disposable test Google account (UI-09) to verify the live production flow. |
| Household roles | Decide whether every organization member may mutate finance records or whether capabilities need owner/member separation (UI-06). |

## Iteration log

| Date | Story | Result | Evidence / blocker |
| --- | --- | --- | --- |
| 2026-09-03 | Audit baseline | `fixed` | Six read-only specialist reviews completed; no files or cloud resources changed. This plan was created from the combined findings. |
| 2026-09-05 | US-P00 | `done` | Parallel repository/tooling/cost/input research was reconciled into shared context adapters, skills, native hooks, local safety scripts, `docs/user-input-needed.md`, and a conditional $0 contract. No application code or cloud resources changed. |
| 2026-09-05 | US-P01 | `in_progress` | Owner confirmed UI-01, 03, 04, 05, 07. Production matrix applied to cloud env. Fail-closed guards and unit tests implemented & passing. Diagnosed cloud build failure (resolved via Option A: GitHub push). Stale plain credentials deleted from cloud; awaiting owner setting secrets (UI-13) before push to `origin/develop`. |
| 2026-09-07 | US-P01 | `done` | Enforced JWKS ES256 verification and opaque Supabase keys; verified secret metadata in FastAPI Cloud; deployed via GitHub integration (commit a0b2bcf, deployment c016b96d); verified HTTP 200 health & readiness, docs/OpenAPI 404, demo-disabled, BFF proxying, and Supabase Session Pooler URI. Story US-P01 complete; US-P02 queued. |
| 2026-09-07 | US-P02 | `in_progress` | Verified UI-02 live (Google client ID active, Supabase returns HTTP 302 to accounts.google.com). Replaced query-string callback with fixed `/auth/callback` contract; implemented PKCE S256 code exchange; implemented single-use origin-bound state management; implemented safe relative app destination validator; added full backend and frontend unit tests (206 backend tests passed, 16 frontend unit tests passed). Story left in_progress awaiting UI-09 real browser verification. |
