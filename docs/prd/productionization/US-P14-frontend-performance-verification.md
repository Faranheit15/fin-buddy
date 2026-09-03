# US-P14 — Frontend performance and release verification

| Field | Value |
| --- | --- |
| **Status** | `todo` |
| **Sequence** | 14 |
| **Depends on** | US-P01…US-P13 |
| **One-loop objective** | Measure the complete product, remove avoidable frontend work, and make the release repeatable. |
| **Primary boundaries** | Next.js rendering/cache, BFF, client data fetching, bundle, browser tests, CI, release docs |

## User story

**As** a Fin Buddy owner
**I want** the whole application to be fast, testable, and repeatably releasable
**So that** free-tier infrastructure feels dependable without hiding stale financial data.

## Why this matters

The frontend builds successfully, but authenticated routes use several client
effects without a shared query cache, some metadata/detail requests are
sequential or repeated, and charts contribute substantial JavaScript. The
project has no frontend browser or accessibility suite. The public landing page
is also made dynamic by the root layout, while private app data must remain
uncached.

## Scope and non-goals

In scope: public/private rendering split, safe data-fetch improvements, bundle
and interaction measurement, browser/a11y coverage, dependency/secret/migration
gates, and final release documentation. Out of scope: new product features.

## Touchpoints

- [`frontend/src/app/layout.tsx`](../../../frontend/src/app/layout.tsx)
- [`frontend/src/app/api/backend/[...path]/route.ts`](../../../frontend/src/app/api/backend/[...path]/route.ts)
- [`frontend/src/features/auth/auth-provider.tsx`](../../../frontend/src/features/auth/auth-provider.tsx)
- [`frontend/src/app/app/`](../../../frontend/src/app/app)
- [`frontend/src/lib/api/`](../../../frontend/src/lib/api)
- [`frontend/package.json`](../../../frontend/package.json)
- [`.github/`](../../../.github)
- [`docker-compose.yml`](../../../docker-compose.yml)
- [`docs/DEPLOY.md`](../../DEPLOY.md)

## Acceptance criteria

1. Baselines exist for landing, login, dashboard, cards, transactions,
   statements, and the main mobile capture journey, including route JS,
   request count, LCP/INP/CLS where measurable, and API latency.
2. Public pages can be cached/static where safe; authenticated financial data
   remains private, uncached, tenant-scoped, and fresh after mutations.
3. Session/profile/metadata requests are shared or parallelized, stale requests
   are abortable, and below-the-fold charts are loaded without blocking the
   daily cockpit.
4. Large lists have explicit pagination and the BFF does not add accidental
   caching, redirects, header leaks, or unbounded retries.
5. Browser smoke and accessibility coverage exercises the most important
   user journeys without using real personal data.
6. Backend/frontend quality gates, migration checks, dependency/secret checks,
   and Compose configuration checks run from a documented command or CI job.
7. The release runbook contains current deployment evidence, rollback steps,
   health/readiness checks, data-target verification, and known free-tier limits.

## Tasks

### Gather

- [ ] **US-P14.G1 — Measure the current frontend.** Capture route-level JS
  transfer/chunks, request waterfalls, render timing, LCP/INP/CLS, console
  errors, and mobile/desktop screenshots for public and authenticated routes.
  Record cold/warm API timings separately from browser rendering.
- [ ] **US-P14.G2 — Trace client data ownership.** Inventory auth bootstrap,
  profile/org, cards/categories/contacts, dashboard, statement, debt, and
  notification requests. Mark duplicate/sequential requests, missing abort
  signals, stale update risks, and responses that must remain `no-store`.
- [ ] **US-P14.G3 — Inventory verification gaps.** Check browser/E2E/a11y
  tooling, CI workflows, lockfile/runtime pinning, dependency/secret/SBOM
  checks, migration gates, Compose config, and route/documentation drift.

### Plan

- [ ] **US-P14.P1 — Define performance budgets.** Set route JS, request count,
  web-vitals, API P95, cold-start, upload, and memory budgets from the measured
  product experience. Explain which budget is a guardrail versus a hard block.
- [ ] **US-P14.P2 — Design safe fetch strategy.** Choose a small shared query
  cache or server-prefetch approach for authenticated data, define cache keys by
  user/org, invalidation after mutation, abort behavior, and retry policy. Do
  not use shared CDN caching for private finance data.
- [ ] **US-P14.P3 — Design release checks.** Define local and CI commands,
  required browser journeys, accessibility scope, migration dry-run, secret
  scan, dependency/runtime pin checks, and how failures block a deployment.

### Implement

- [ ] **US-P14.I1 — Split public and private rendering.** Make the landing/auth
  surfaces cacheable/static where safe while keeping app/BFF/session routes
  dynamic and private. Verify CSP, cookies, headers, and redirects after the
  split.
- [ ] **US-P14.I2 — Remove fetch waterfalls.** Share session/profile metadata,
  parallelize independent requests, add abort signals/stale guards, avoid
  duplicate first-card/detail fetches, and update API types to match backend
  response fields.
- [ ] **US-P14.I3 — Reduce blocking JavaScript.** Lazy-load below-fold charts,
  preserve accessible summaries, remove avoidable dependencies/imports, and
  paginate large lists without changing financial totals.
- [ ] **US-P14.I4 — Add verification tooling.** Add the smallest maintainable
  browser smoke/a11y setup for login, card, friend spend/settlement, EMI,
  statement review/import, export, deletion, and key failure states. Use
  synthetic fixtures and isolated credentials.
- [ ] **US-P14.I5 — Add release automation.** Add documented or CI-enforced
  frontend/backend gates, migration check, dependency/secret/SBOM scan, frozen
  installs, runtime pin check, `docker compose config --quiet`, and deploy
  smoke instructions. Keep checks free-tier compatible.
- [ ] **US-P14.I6 — Reconcile docs.** Update the active plan/progress/runbook
  with final commands, deployment evidence, route inventory, known residuals,
  and the decision about the old remediation queue.

### Test

- [ ] **US-P14.T1 — Compare performance.** Repeat the baseline measurements at
  the same viewport, fixture size, network profile, and cold/warm condition.
  Record wins, regressions, and any changed tradeoff.
- [ ] **US-P14.T2 — Test cache/privacy boundaries.** Verify authenticated
  responses cannot be served across users/organizations, mutations invalidate
  the right data, and browser cookies/headers are not forwarded incorrectly.
- [ ] **US-P14.T3 — Run browser/a11y journeys.** Execute the synthetic core
  flows and assert final state, error recovery, console health, network
  failures, keyboard coverage, and mobile layout.
- [ ] **US-P14.T4 — Run the complete gates.** Run backend pytest/Ruff/mypy,
  frontend lint/typecheck/build/format policy, browser/a11y suite, migration
  checks, security scans, and Compose validation.

### Validate

- [ ] **US-P14.V1 — Verify the user journey.** Start from the public page and
  complete login, dashboard, capture, statement review, settlement/repayment,
  notification, export, and deletion checkpoints with synthetic data.
- [ ] **US-P14.V2 — Verify deployment.** Deploy the verified commit, run health,
  readiness, BFF, auth, storage, and route smoke checks, and confirm rollback
  instructions are executable.
- [ ] **US-P14.V3 — Verify budgets and quotas.** Compare measured use with the
  selected Vercel, FastAPI Cloud, Supabase, Storage, function, database, and
  logging limits. Record what happens when a limit is reached.
- [ ] **US-P14.V4 — Close the plan.** Mark this story done only after US-P01…
  US-P13 are done, update [`PROGRESS.md`](PROGRESS.md), record final evidence,
  and emit the completion promise only when every story is complete.

## Evidence to record

- Before/after performance table and test environment.
- Cache/privacy and BFF header checks.
- Browser/a11y coverage report.
- Full quality-gate and CI output.
- Deployment/rollback evidence and quota review.

## Safety notes

Do not optimize by caching private financial data or weakening tenant checks.
Do not make a browser suite depend on a real account, real bank statement, or
real email delivery. Do not declare the plan complete while an earlier story
has only documentation and no acceptance evidence.

## Story notes

_(Append dated implementation decisions and evidence here.)_
