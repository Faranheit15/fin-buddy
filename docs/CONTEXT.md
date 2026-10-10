# Active project context

> **Feature focus:** Productionization and product polish — story plan active
>
> **Last recorded:** 2026-10-06 · **Last reviewed:** 2026-10-06

## Current release state

Phases 0–5 MVP are shipped. PRD v2.0 and R2A–R2H tasks are complete. Work was
broken into six user stories under [`prd/release-2/`](prd/release-2/) (US-01…US-06)
and all are now Done. The next work is organized as independently completable
user stories in the
[Productionization & Product Polish plan](prd/productionization/README.md).
The plan covers the current deployment gate, security and reliability work,
the $0 operating posture, and focused improvements to the daily finance
workflow and UI. The shared agent workflow and human-input handoff are now in
place so Codex, Claude Code, and Google Antigravity can continue the same
one-story loop without putting credentials in the repository.

As of 2026-10-10, 8 of 15 productionization stories are done (US-P00–US-P06,
US-P08); US-P07 is reopened in_progress for a keepalive cold-start timeout fix.
FastAPI Cloud scale-to-zero cold starts take 8–16s, causing the previous 8s
keepalive timeout to abort and return 504. The next unstarted story is US-P09
(jobs, logs, and error hygiene). Live progress and evidence are in
[`prd/productionization/PROGRESS.md`](prd/productionization/PROGRESS.md).

## Deferred to Release 3+

PWA is deferred to R3. Salary, investments, Account Aggregators, AI, and
commercial packaging remain Release 3+ work. The full deferred list is in the
[Release 2 out-of-scope section](prd/RELEASE-2-TASKS.md#explicitly-out-of-scope-release-3).

## How to use this page

Keep this page short and update it when the active feature focus changes. Use
the release trackers for detailed progress and dated reviews for deployment or
production-readiness evidence.
