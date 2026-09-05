# Fin Buddy documentation

This is the documentation home for Fin Buddy. It gives a newcomer a fast path
through the product, the release history, the architecture, and the operational
runbooks without changing the location of any existing document.

> **Current status — 2026-09-03**
>
> Release 1 (the Phase 0–5 MVP) is shipped. Release 2 implementation is
> complete across R2A–R2H and US-01–US-06. The release-readiness review says the
> project can enter deployment on the existing free-tier architecture after the
> release owner completes the required Supabase, FastAPI Cloud, and Vercel
> environment actions. Productionization and product-polish work is now the
> active plan. Salary, investments, Account Aggregators, AI, PWA, and
> commercial packaging remain deferred Release 3+ expansion work.

## Start here

| If you want to… | Read… |
| --- | --- |
| Understand the product and run it locally | [`README.md`](../README.md) |
| Browse this documentation set | [`INDEX.md`](INDEX.md) |
| Read the product requirements | [`prd/README.md`](prd/README.md) |
| See the Release 1 baseline | [`prd/release-1/README.md`](prd/release-1/README.md) |
| See Release 2 scope and completion | [`prd/release-2/README.md`](prd/release-2/README.md) |
| Inspect Release 2 progress and evidence | [`prd/release-2/PROGRESS.md`](prd/release-2/PROGRESS.md) |
| Start the active implementation loop | [`prd/productionization/README.md`](prd/productionization/README.md) and [`prd/productionization/RALPH-LOOP-PROMPT.md`](prd/productionization/RALPH-LOOP-PROMPT.md) |
| Inspect active story progress | [`prd/productionization/PROGRESS.md`](prd/productionization/PROGRESS.md) |
| Provide a missing decision or credential safely | [`user-input-needed.md`](user-input-needed.md) |
| Understand Codex, Claude Code, and Antigravity setup | [`AGENT-TOOLING.md`](AGENT-TOOLING.md) |
| Deploy the current system | [`DEPLOY.md`](DEPLOY.md) |
| Understand the design language | [`DESIGN.md`](../DESIGN.md) and [`architecture/`](architecture/README.md) |

## Release map

| Release | Status | What it contains | Primary evidence |
| --- | --- | --- | --- |
| **Release 1 — MVP** | Shipped | Phases 0–5: foundations, Supabase auth and organizations, cards and billing cycles, contacts and transactions, statement review/import, notifications, settings, and deployment documentation. | [Release 1 index](prd/release-1/README.md) · [Root roadmap](../README.md#phase-roadmap-release-1-baseline) · [PRD v2.0 baseline](prd/2026-07-27-fin-buddy-prd.md#15-acceptance-criteria) |
| **Release 2** | Implementation complete | Auditable ledger, multi-account balances, categories/transfers/splits, debts and loans, card EMIs/GST, imports/exports, net worth and upcoming items, reminders, privacy, deletion, and share-schema readiness. | [Release 2 index](prd/release-2/README.md) · [Exit criteria](prd/RELEASE-2-TASKS.md#release-2-exit-criteria) · [Readiness review](reviews/2026-08-11-release-readiness.md) |
| **Productionization & Product Polish** | Active plan | Shared agent workflow, production-safe deployment, auth, tenant isolation, free-tier reliability, upload correctness, performance, daily dues workflows, mobile accessibility, and release verification. | [Story index](prd/productionization/README.md) · [Progress](prd/productionization/PROGRESS.md) |
| **Release 3+** | Planned / deferred | PWA work, connected-user debt confirmation, salary/PF/NPS, investments/XIRR, Account Aggregators/Open Banking, AI agents, native apps, SMS/WhatsApp, and commercial packaging. | [`CONTEXT.md`](CONTEXT.md) · [Release 2 out-of-scope list](prd/RELEASE-2-TASKS.md#explicitly-out-of-scope-release-3) |

## Documentation map

### Product and release planning

- [`prd/README.md`](prd/README.md) — product requirements and release entry points.
- [`prd/release-1/README.md`](prd/release-1/README.md) — Release 1 Phase 0–5 baseline and handoff to Release 2.
- [`prd/2026-07-27-fin-buddy-prd.md`](prd/2026-07-27-fin-buddy-prd.md) — the main product requirements document, including the Release 1 baseline and Release 2 requirements.
- [`prd/RELEASE-2-TASKS.md`](prd/RELEASE-2-TASKS.md) — Release 2 workstreams, exit criteria, and out-of-scope items.
- [`prd/release-2/README.md`](prd/release-2/README.md) — Release 2 story map and implementation workflow.
- [`prd/release-2/PROGRESS.md`](prd/release-2/PROGRESS.md) — story status and historical iteration log.
- [`prd/productionization/README.md`](prd/productionization/README.md) — active productionization and product-polish story map.
- [`prd/productionization/PROGRESS.md`](prd/productionization/PROGRESS.md) — active story status and evidence log.

### Architecture and design

- [`DESIGN.md`](../DESIGN.md) — product design system and visual source of truth.
- [`PRODUCT.md`](../PRODUCT.md) — product, audience, positioning, constraints, and principles.
- [`architecture/README.md`](architecture/README.md) — architecture references and UI integration guidance.
- [`architecture/aceternity.md`](architecture/aceternity.md) — how Aceternity UI fits the existing design system.

### Operations and release evidence

- [`DEPLOY.md`](DEPLOY.md) — Vercel, FastAPI Cloud, Supabase, smoke checks, and local quality gates.
- [`reviews/README.md`](reviews/README.md) — dated production-readiness reviews and the remediation queue.
- [`reviews/2026-08-11-release-readiness.md`](reviews/2026-08-11-release-readiness.md) — latest release-owner checklist and validation evidence.

### Working context and guardrails

- [`CONTEXT.md`](CONTEXT.md) — the active feature focus and deferred work.
- [`ROUTING.md`](ROUTING.md) — where to look when changing a part of the system.
- [`GOTCHAS.md`](GOTCHAS.md) — repository-specific traps, security rules, and retired approaches.
- [`user-input-needed.md`](user-input-needed.md) — owner decisions and secure input destinations.
- [`AGENT-TOOLING.md`](AGENT-TOOLING.md) — cross-agent skills, rules, hooks, and free-only guardrails.

## Source-of-truth order

When documentation and implementation appear to disagree, use this order:

1. The current source tree and its tests.
2. The active Productionization & Product Polish plan and progress tracker.
3. The Release 2 workstream and progress trackers.
4. Dated release-readiness or production-review evidence.
5. Story notes and iteration logs, which preserve historical decisions and context.

## How to use this documentation

1. Start with this page for orientation.
2. Use [`INDEX.md`](INDEX.md) when you need the complete registry of documents.
3. Treat release trackers as the current implementation status and dated reviews as historical evidence.
4. Treat unchecked manual checks and the active productionization queue as follow-up work, even when the corresponding release implementation is marked complete.
5. Keep existing paths stable when adding or revising documentation so links in the codebase and agent prompts continue to work.

The root [`README.md`](../README.md), [`PRODUCT.md`](../PRODUCT.md), and
[`DESIGN.md`](../DESIGN.md) remain at the repository root because they are the
project-level quickstart and design inputs. They are linked here intentionally;
no document is duplicated or removed.
