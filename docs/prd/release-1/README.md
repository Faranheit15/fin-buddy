# Release 1 — MVP baseline

Release 1 is the shipped Phase 0–5 foundation for Fin Buddy. This page is a
navigation layer over the existing project README and PRD; it does not replace
or duplicate either source.

> **Status:** Shipped · **Scope:** Phases 0–5 · **Successor:** Release 2

## What shipped

| Phase | Capability | Status |
| --- | --- | --- |
| 0 | PRD, frontend/backend scaffolds, and repository foundations | Done |
| 1 | Supabase authentication, organization bootstrap, and authenticated app shell | Done |
| 2 | Credit cards, billing-cycle math, and dashboard KPIs | Done |
| 3 | Contacts, transactions, settlements, and friend-lending balances | Done |
| 4 | Statement PDF upload, review, and import | Done |
| 5 | Polish, empty states, notifications, settings, and deployment documentation | Done |

## Read the source records

- [Root README](../../../README.md) — quickstart, architecture, Phase 0–5 roadmap, Docker Compose, and deployment pointers.
- [Product requirements](../2026-07-27-fin-buddy-prd.md) — [v1 baseline](../2026-07-27-fin-buddy-prd.md#16-what-shipped-in-v1-baseline), [v1 acceptance criteria](../2026-07-27-fin-buddy-prd.md#151-v1-personal-daily-driver-shipped).
- [Backend README](../../../backend/README.md) — FastAPI setup, migrations, API surface, and checks.
- [Frontend README](../../../frontend/README.md) — Next.js setup, scripts, and Vercel deployment notes.
- [Deployment runbook](../../DEPLOY.md) — personal production deployment sequence.

## Handoff to Release 2

Release 2 extends this foundation rather than replacing it. The current
implementation map is in the [Release 2 index](../release-2/README.md), with
the [workstream exit criteria](../RELEASE-2-TASKS.md#release-2-exit-criteria)
and [progress tracker](../release-2/PROGRESS.md) as the status references.
