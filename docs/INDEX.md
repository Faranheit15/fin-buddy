# Documentation index

This is the complete registry of project documentation. For a guided entry
point, start with [`docs/README.md`](README.md).

## Product and release planning

| Document | Purpose |
| --- | --- |
| [`../README.md`](../README.md) | General overview, quickstart, Phase 0–5 roadmap, Docker Compose, and personal production deployment pointers. |
| [`../PRODUCT.md`](../PRODUCT.md) | Product requirements context, users, positioning, constraints, principles, and evidence on hand. |
| [`../DESIGN.md`](../DESIGN.md) | Design system source of truth: tokens, typography, layout, components, and visual guardrails. |
| [`prd/README.md`](prd/README.md) | Product-requirements folder index and release entry points. |
| [`prd/release-1/README.md`](prd/release-1/README.md) | Release 1 Phase 0–5 MVP baseline and handoff to Release 2. |
| [`prd/2026-07-27-fin-buddy-prd.md`](prd/2026-07-27-fin-buddy-prd.md) | Product requirements document (v2.0 — Release 1 baseline plus expanded personal finance). |
| [`prd/RELEASE-2-TASKS.md`](prd/RELEASE-2-TASKS.md) | Release 2 implementation backlog (R2A–R2H), cross-cutting checklist, and exit criteria. |
| [`prd/release-2/README.md`](prd/release-2/README.md) | Release 2 user-story index (US-01–US-06), dependencies, and workflow. |
| [`prd/release-2/PROGRESS.md`](prd/release-2/PROGRESS.md) | Release 2 story/subtask progress tracker and historical iteration log. |
| [`prd/release-2/RALPH-LOOP-PROMPT.md`](prd/release-2/RALPH-LOOP-PROMPT.md) | Ralph loop prompt retained for repeatable Release 2 implementation work. |
| [`prd/productionization/README.md`](prd/productionization/README.md) | Active productionization and product-polish user-story index. |
| [`prd/productionization/PROGRESS.md`](prd/productionization/PROGRESS.md) | Active story status and one-loop evidence tracker. |
| [`prd/productionization/RALPH-LOOP-PROMPT.md`](prd/productionization/RALPH-LOOP-PROMPT.md) | One-story-per-loop implementation prompt. |
| [`user-input-needed.md`](user-input-needed.md) | Human decisions, credential destinations, and agent-updated blockers; never secret values. |
| [`AGENT-TOOLING.md`](AGENT-TOOLING.md) | Codex, Claude Code, and Antigravity context, skills, hooks, and free-only guardrails. |

### Release 2 user stories

| Story | Scope |
| --- | --- |
| [`US-01`](prd/release-2/US-01-auditable-ledger.md) | Auditable ledger foundation. |
| [`US-02`](prd/release-2/US-02-multi-account-balances.md) | Multi-account balances. |
| [`US-03`](prd/release-2/US-03-categories-transfers-splits.md) | Categories, transfers, and splits. |
| [`US-04`](prd/release-2/US-04-debts-and-loans.md) | Debts and loans. |
| [`US-05`](prd/release-2/US-05-card-emis-and-gst.md) | Card EMIs and GST tracking. |
| [`US-06`](prd/release-2/US-06-insights-imports-reminders.md) | Insights, imports/exports, reminders, privacy, and deletion. |

### Productionization & Product Polish user stories

| Story | Scope |
| --- | --- |
| [`US-P00`](prd/productionization/US-P00-agent-interoperability-and-cost-guardrails.md) | Shared agent workflow and zero-cost guardrails. |
| [`US-P01`](prd/productionization/US-P01-production-release-gate.md) | Production release gate. |
| [`US-P02`](prd/productionization/US-P02-google-oauth.md) | Google OAuth that completes. |
| [`US-P03`](prd/productionization/US-P03-supabase-security-boundary.md) | Supabase security boundary. |
| [`US-P04`](prd/productionization/US-P04-tenant-authorization-lifecycle.md) | Tenant authorization and account lifecycle. |
| [`US-P05`](prd/productionization/US-P05-safe-financial-mutations.md) | Safe financial mutations. |
| [`US-P06`](prd/productionization/US-P06-durable-statement-ingestion.md) | Durable statement ingestion. |
| [`US-P07`](prd/productionization/US-P07-readiness-and-keepalive.md) | Readiness and Supabase keepalive. |
| [`US-P08`](prd/productionization/US-P08-database-api-performance.md) | Database and API performance. |
| [`US-P09`](prd/productionization/US-P09-jobs-logs-errors.md) | Jobs, logs, and error hygiene. |
| [`US-P10`](prd/productionization/US-P10-dues-billing-cockpit.md) | Dues and billing cockpit. |
| [`US-P11`](prd/productionization/US-P11-fast-capture-relationships.md) | Fast capture and relationship ledger. |
| [`US-P12`](prd/productionization/US-P12-statement-review-notifications.md) | Statement review and notification clarity. |
| [`US-P13`](prd/productionization/US-P13-mobile-accessibility-design.md) | Mobile, accessibility, and visual consistency. |
| [`US-P14`](prd/productionization/US-P14-frontend-performance-verification.md) | Frontend performance and release verification. |

## Operations and deployment

| Document | Purpose |
| --- | --- |
| [`DEPLOY.md`](DEPLOY.md) | Personal production deploy runbook for Vercel, FastAPI Cloud, and Supabase. |
| [`reviews/README.md`](reviews/README.md) | Review timeline and how to interpret release evidence. |
| [`reviews/2026-08-10-production-readiness-audit.md`](reviews/2026-08-10-production-readiness-audit.md) | Security, code-quality, architecture, UX, and production-readiness audit. |
| [`reviews/2026-08-11-release-readiness.md`](reviews/2026-08-11-release-readiness.md) | Final hardening outcome, free-tier architecture decision, validation evidence, and release-owner checklist. |
| [`reviews/production-remediation-loop.md`](reviews/production-remediation-loop.md) | Runnable one-subtask-at-a-time remediation queue for deferred hardening. |

## Architecture and UI integration

| Document | Purpose |
| --- | --- |
| [`architecture/README.md`](architecture/README.md) | Architecture-reference index. |
| [`architecture/aceternity.md`](architecture/aceternity.md) | Aceternity UI usage boundaries and shadcn-token integration. |

## Project context and contributor guardrails

| Document | Purpose |
| --- | --- |
| [`ROUTING.md`](ROUTING.md) | Where agents should look for specific implementation tasks. |
| [`GOTCHAS.md`](GOTCHAS.md) | Project-specific quirks, security constraints, and retired claims. |
| [`CONTEXT.md`](CONTEXT.md) | Current feature focus, completed release state, and deferred work. |
| [`../backend/README.md`](../backend/README.md) | FastAPI setup, endpoints, migrations, checks, and deployment notes. |
| [`../frontend/README.md`](../frontend/README.md) | Next.js setup, scripts, UI integration guidance, and Vercel deployment notes. |

## Document conventions

- The root README is the project quickstart; this folder is the documentation home.
- When progress is uncertain, verify the source tree and tests before trusting a historical note.
- Release trackers are the current source for implementation status.
- Dated reviews are evidence snapshots and should not be silently rewritten as current status.
- Manual residuals and open remediation items remain visible until they have evidence.
- Existing document paths are kept stable so links in code, prompts, and prior notes continue to resolve.
