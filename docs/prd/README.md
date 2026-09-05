# Product requirements

This folder contains the product requirements and release planning record for
Fin Buddy. The main PRD is a single requirements source spanning the shipped
Release 1 baseline and the Release 2 expansion; the release-specific trackers
make implementation status easier to scan.

## Release entry points

| Release | Status | Start with | Supporting record |
| --- | --- | --- | --- |
| **Release 1 — MVP** | Shipped | [Release 1 baseline index](release-1/README.md) | [Root Phase 0–5 roadmap](../../README.md#phase-roadmap-release-1-baseline) · [PRD v2.0 baseline](2026-07-27-fin-buddy-prd.md#15-acceptance-criteria) |
| **Release 2** | Implementation complete | [User-story index](release-2/README.md) | [Workstreams and exit criteria](RELEASE-2-TASKS.md) · [Progress](release-2/PROGRESS.md) |
| **Productionization & Product Polish** | Active plan | [User-story index](productionization/README.md) | [Progress](productionization/PROGRESS.md) · [Loop prompt](productionization/RALPH-LOOP-PROMPT.md) |
| **Release 3+** | Planned / deferred | [Active context](../CONTEXT.md) | [Release 2 out-of-scope list](RELEASE-2-TASKS.md#explicitly-out-of-scope-release-3) |

## Canonical documents

- [`release-1/README.md`](release-1/README.md) — Phase 0–5 MVP baseline and handoff to Release 2.
- [`2026-07-27-fin-buddy-prd.md`](2026-07-27-fin-buddy-prd.md) — product purpose, users, capabilities, flows, data model, business rules, quality bar, roadmap, and acceptance criteria.
- [`RELEASE-2-TASKS.md`](RELEASE-2-TASKS.md) — R2A–R2H workstreams, dependencies, cross-cutting checklist, exit criteria, and out-of-scope work.
- [`release-2/README.md`](release-2/README.md) — US-01–US-06 story map and story workflow.
- [`release-2/PROGRESS.md`](release-2/PROGRESS.md) — current story status and implementation history.
- [`release-2/RALPH-LOOP-PROMPT.md`](release-2/RALPH-LOOP-PROMPT.md) — autonomous implementation-loop prompt retained for project history and repeatable work.
- [`productionization/README.md`](productionization/README.md) — active user-story plan for production readiness and product polish.
- [`productionization/PROGRESS.md`](productionization/PROGRESS.md) — current status and one-loop evidence for the active plan.
- [`productionization/RALPH-LOOP-PROMPT.md`](productionization/RALPH-LOOP-PROMPT.md) — one-story-per-loop execution contract.
- [`../user-input-needed.md`](../user-input-needed.md) — secure human decisions and credential destinations.
- [`../AGENT-TOOLING.md`](../AGENT-TOOLING.md) — shared Codex, Claude Code, and Antigravity setup.

## Reading order

For product orientation, read the root [`PRODUCT.md`](../../PRODUCT.md), then
the [main PRD](2026-07-27-fin-buddy-prd.md). For active implementation work,
read the [Productionization & Product Polish index](productionization/README.md),
then [progress](productionization/PROGRESS.md) and the selected story. Release
2 remains available as the completed historical feature plan.
