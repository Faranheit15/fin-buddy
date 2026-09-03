# Productionization & Product Polish — Progress

> This is the current tracker for the active one-story-per-loop plan. Do not
> mark a story `done` without the acceptance evidence listed in its story file.

| Field | Value |
| --- | --- |
| **Plan** | Productionization & Product Polish |
| **Status** | Not started — plan created |
| **Last reviewed** | 2026-09-03 |
| **Completed stories** | 0 / 14 |
| **Current story** | US-P01 — Production release gate |
| **Loop prompt** | [`RALPH-LOOP-PROMPT.md`](RALPH-LOOP-PROMPT.md) |

## Story status

| Story | Status | One-loop objective | Evidence |
| --- | --- | --- | --- |
| [US-P01](US-P01-production-release-gate.md) | `todo` | Make the live deployment explicitly production-safe and verify the release gate. | — |
| [US-P02](US-P02-google-oauth.md) | `todo` | Complete and test the Google OAuth redirect and session flow. | — |
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
- Backend checks pass: `uv run pytest -q`, `uv run ruff check .`, and
  `uv run mypy app`.
- Frontend checks pass: `bun run lint`, `bun run typecheck`, and `bun run build`.
- `bun run format:check` reports 69 files needing formatting.
- No frontend browser or accessibility test suite exists yet.
- FastAPI Cloud account-level environment and deployment state still needs
  verification because the local CLI is unauthenticated.

## Blockers requiring a human decision or credential

| Blocker | Required decision or input |
| --- | --- |
| `fin-buddy-dev.vercel.app` naming | Decide whether it is the production surface or a clearly labeled staging surface. |
| FastAPI Cloud account state | Authenticate the CLI or inspect the dashboard so the actual plan, env vars, and deployment are known. |
| Google OAuth | Create or select the Google Cloud Web OAuth client and enter its credentials in Supabase Auth. |
| Supabase data target | Confirm that the active project and its current row counts are the intended production database before schema changes. |
| Household roles | Decide whether every organization member may mutate finance records or whether capabilities need owner/member separation. |

## Iteration log

| Date | Story | Result | Evidence / blocker |
| --- | --- | --- | --- |
| 2026-09-03 | Audit baseline | `fixed` | Six read-only specialist reviews completed; no files or cloud resources changed. This plan was created from the combined findings. |
