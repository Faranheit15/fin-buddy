# Fin Buddy — Productionization & Product Polish

| Field | Value |
| --- | --- |
| **Plan** | Productionization & Product Polish |
| **Status** | Active planning |
| **Created** | 2026-09-03 |
| **Source** | Live audit of the repository, Vercel deployment, FastAPI endpoint, and Supabase project |
| **Progress** | [`PROGRESS.md`](PROGRESS.md) |
| **Loop contract** | [`RALPH-LOOP-PROMPT.md`](RALPH-LOOP-PROMPT.md) |

## Objective

Turn the Release 2 feature set into a trustworthy, pleasant daily finance
workspace while keeping the monthly infrastructure cost at $0 for personal or
low-volume use where the free-tier terms allow it.

The plan deliberately treats production safety and product quality as one
backlog. A polished UI is not ready to ship if a live deployment still exposes
demo access, loses uploaded statements, or permits cross-organization data
references.

## Product promise

Fin Buddy should make one daily question easy to answer:

> What needs attention today across my cards, billing cycles, EMIs, accounts,
> friend balances, and formal debts?

Its strongest product identity is a ledger-first workspace for credit-card
cycles, friend-attributed spending, settlements, EMIs, and informal debts. The
work should make those existing capabilities coherent before adding salary,
investments, Account Aggregators, AI, PWA, or commercial packaging.

## Story map

Sequence is the recommended dependency order, not a priority label. Each row is
intentionally scoped so one implementation-loop iteration can complete one
story without starting the next story.

| Sequence | Story | Outcome | Depends on | Status |
| ---: | --- | --- | --- | --- |
| 1 | [US-P01 — Production release gate](US-P01-production-release-gate.md) | The public deployment is explicitly production-safe and reproducible. | — | `todo` |
| 2 | [US-P02 — Google OAuth that completes](US-P02-google-oauth.md) | Users can sign in with Google through a secure, tested callback flow. | US-P01 | `todo` |
| 3 | [US-P03 — Supabase security boundary](US-P03-supabase-security-boundary.md) | Database policies, grants, and security-definer functions are intentional and versioned. | US-P01 | `todo` |
| 4 | [US-P04 — Tenant authorization and account lifecycle](US-P04-tenant-authorization-lifecycle.md) | Users cannot cross-link organizations or regain access after deletion. | US-P01, US-P03 | `todo` |
| 5 | [US-P05 — Safe financial mutations](US-P05-safe-financial-mutations.md) | Retries and concurrent requests cannot duplicate or corrupt ledger events. | US-P04 | `todo` |
| 6 | [US-P06 — Durable statement ingestion](US-P06-durable-statement-ingestion.md) | Statement files bypass the BFF size limit and remain durable on FastAPI Cloud. | US-P01, US-P03 | `todo` |
| 7 | [US-P07 — Readiness and Supabase keepalive](US-P07-readiness-and-keepalive.md) | Health probes are meaningful and an optional daily DB activity check is safe. | US-P01 | `todo` |
| 8 | [US-P08 — Database and API performance](US-P08-database-api-performance.md) | Core requests stay fast and within free-tier connection/resource limits. | US-P03, US-P05 | `todo` |
| 9 | [US-P09 — Jobs, logs, and error hygiene](US-P09-jobs-logs-errors.md) | Background reminders and operational telemetry are bounded, private, and retry-safe. | US-P05, US-P07 | `todo` |
| 10 | [US-P10 — Dues and billing cockpit](US-P10-dues-billing-cockpit.md) | The dashboard becomes the single action-oriented daily command center. | US-P04, US-P08 | `todo` |
| 11 | [US-P11 — Fast capture and relationship ledger](US-P11-fast-capture-relationships.md) | Recording spending, settlements, repayments, and corrections feels immediate and clear. | US-P04, US-P05, US-P10 | `todo` |
| 12 | [US-P12 — Statement review and notification clarity](US-P12-statement-review-notifications.md) | Imports are reviewable and notifications tell the truth about what needs action. | US-P05, US-P06, US-P10 | `todo` |
| 13 | [US-P13 — Mobile, accessibility, and visual consistency](US-P13-mobile-accessibility-design.md) | The Ledger Shelf experience works for keyboard, screen-reader, touch, dark-mode, and narrow-screen users. | US-P10, US-P11, US-P12 | `todo` |
| 14 | [US-P14 — Frontend performance and release verification](US-P14-frontend-performance-verification.md) | The complete user journey is measured, tested, and repeatably releasable. | US-P01…US-P13 | `todo` |

## Dependency shape

```text
US-P01 ──► US-P02
   ├─────► US-P03 ──► US-P04 ──► US-P05 ──► US-P08
   │          │                         └────► US-P09
   ├─────► US-P06 ───────────────────────────► US-P12
   └─────► US-P07 ───────────────────────────► US-P09

US-P08 ──► US-P10 ──► US-P11 ──► US-P13 ──► US-P14
                    └──► US-P12 ────────────────┘
```

## Legacy queue mapping

The older [`production-remediation-loop.md`](../../reviews/production-remediation-loop.md)
is retained as dated evidence. Its still-open IDs are represented by the
current stories as follows:

| Legacy ID | Current story coverage |
| --- | --- |
| `REL-02` | US-P01 migration/release gate |
| `REL-03` | US-P14 release automation and security checks |
| `QLT-01` | US-P13 accessibility plus US-P14 browser verification |
| `ARC-01` | US-P14 repository/runtime cleanup decision |

The new stories also absorb the live audit findings that were not present in
the older queue, including Google OAuth, Supabase policy drift, tenant
integrity, financial idempotency, direct statement uploads, and the dues
cockpit.

## Architecture invariants

- Keep the two-app boundary: `frontend/` and `backend/` communicate through
  the API; neither imports files from the other.
- Keep Supabase service-role credentials backend-only. Never place them in
  Vercel public variables or browser code.
- Keep all monetary calculations as integer paise and preserve INR/IST
  semantics. Never introduce float arithmetic into ledger or parser math.
- Keep statements in the private Supabase Storage bucket on FastAPI Cloud;
  local filesystem storage is not durable there.
- Keep posted ledger records auditable. Correct posted records with reversals or
  adjustments; do not reintroduce silent mutation.
- Preserve the distinction between contact settlements and formal obligations.
- Do not cache authenticated financial responses at a shared CDN layer.
- Treat Supabase RLS as defense in depth, but do not add permissive policies
  without testing the service-role API and direct Data API behavior.

## One-loop operating model

1. Read the root `AGENTS.md`, this index, the selected story, `GOTCHAS.md`,
   `CONTEXT.md`, and the relevant code or deployment runbook.
2. Work on exactly one story. Do not begin another story because it is nearby
   or because one task is blocked.
3. Complete the story phases in order: **Gather → Plan → Implement → Test →
   Validate**. A task description explains both the action and the evidence
   needed to mark it complete.
4. Record a baseline or failing reproduction before changing behavior. For
   cloud work, record the target project, deployment, or environment before
   making a change.
5. If credentials or an external decision are missing, leave the story
   `in_progress` with the exact blocker. Never invent secrets, redirect URLs,
   project IDs, or production data.
6. Run the applicable quality gates, update the story checkboxes and
   [`PROGRESS.md`](PROGRESS.md), and commit only the verified story. Do not push
   unless the user asks.

## Plan-level completion

The plan is complete only when all stories are `done` and the final validation
shows:

- production configuration is fail-closed;
- Google sign-in and session refresh complete in a real browser;
- cross-organization reads and writes fail at both API and database boundaries;
- statement upload, review, import, export, and deletion work end to end;
- dashboard, card-cycle, friend-ledger, and debt workflows are understandable
  on desktop and mobile;
- backend, frontend, browser, accessibility, migration, and security gates are
  reproducible;
- latency, connection counts, storage, and log growth have recorded baselines;
- the $0 architecture is documented as quota- and terms-dependent rather than
  promised as an uptime guarantee.
