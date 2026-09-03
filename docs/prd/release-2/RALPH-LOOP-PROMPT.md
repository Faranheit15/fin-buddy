# Ralph Loop Prompt — Fin Buddy Release 2

> **Document status:** Historical implementation prompt. Release 2 is complete;
> use the [progress tracker](PROGRESS.md) and [exit criteria](../RELEASE-2-TASKS.md#release-2-exit-criteria)
> before starting any future maintenance loop.

Copy the **Prompt body** below into a Ralph loop. State lives on disk in this folder; each iteration starts fresh and must re-read files.

## How to run

### Claude Code (ralph-loop plugin)

```bash
/ralph-loop "$(cat docs/prd/release-2/RALPH-LOOP-PROMPT.md)" --max-iterations 80 --completion-promise "RELEASE_2_COMPLETE"
```

If your tool does not expand the file, paste the **Prompt body** section only (from “You are implementing…” through the completion promise rules).

### Cursor / generic agent loop

Each iteration: open a fresh agent with the Prompt body as the sole user message. Stop when the agent outputs exactly:

```text
<promise>RELEASE_2_COMPLETE</promise>
```

Or after `--max-iterations` is reached. If stuck for many iterations on the same subtask, append a blocker to [`PROGRESS.md`](PROGRESS.md) and stop — do not invent false completion.

---

## Prompt body

You are implementing **Fin Buddy Release 2** in an autonomous Ralph loop.

### Absolute rules

1. **Disk is source of truth.** Re-read these every iteration before coding:
   - `docs/prd/release-2/README.md`
   - `docs/prd/release-2/PROGRESS.md`
   - The current story file under `docs/prd/release-2/US-*.md`
   - `docs/prd/RELEASE-2-TASKS.md`
   - `AGENTS.md`, `frontend/AGENTS.md`, `backend/AGENTS.md`, `docs/GOTCHAS.md`
2. **One subtask per iteration.** Pick the single next unchecked subtask in story order (US-01 → US-06). Within a story, finish Gather → Plan → Implement → Test → Validate in order. Do not skip ahead across stories when dependencies are unmet.
3. **Do not rewrite the stack.** Next.js + FastAPI + Supabase only. Never import across `frontend/` and `backend/`.
4. **Money is integer paise.** No float ledger math.
5. **Small, verified commits.** After a meaningful Implement/Test chunk that leaves the tree healthy, commit with a short imperative message. Do not push unless the human asked.
6. **Mark progress on disk.** Check off completed subtasks `[x]` in the story file. Update `PROGRESS.md` (current story/subtask, iteration log row). When a story’s Validate phase finishes, set Status = Done and tick related boxes in `RELEASE-2-TASKS.md`.
7. **Backpressure before claiming done.** For any Implement/Test subtask touching code:
   - Backend: `cd backend && uv run pytest` (targeted OK first, full if feasible), `uv run ruff check .`, `uv run mypy app` when models/services change.
   - Frontend: `cd frontend && bun run lint && bun run typecheck` when UI changes.
   Fix failures in this iteration when caused by your changes.
8. **Defaults when Gather is ambiguous** (do not block the loop waiting for humans):
   - Draft UX: post-by-default + Save draft secondary.
   - Settlements: keep table; add obligations separately (no double-count in friend dues).
   - EMI interest: typed posted schedule lines; reversible via ledger reverse.
   - Net worth: receivables as assets.
   - PWA: defer to R3 unless trivial; note in CONTEXT if deferred.
   Record the choice under **Story notes**.
9. **Frontend UI requires Impeccable.** For any subtask that creates or changes user-visible UI, load `.claude/skills/impeccable/SKILL.md` and follow it:
   - Once per session: `node .claude/skills/impeccable/scripts/context.mjs` (Operate mode for app surfaces; honor `PRODUCT.md` / `DESIGN.md`).
   - Plan UI with `shape` before coding new pages/flows/empty states/dashboard sections.
   - Before editing UI, load craft-floor; preserve The Ledger Shelf — no generic purple/gradient AI dashboard look.
   - Validate UI with `polish` + `harden`; use `onboard` for empty states, `audit` for a11y/responsive, `clarify` for copy/errors.
   - Skip only for pure API-client/type changes with no visual delta.
10. **Out of scope:** salary, investments, Account Aggregators, AI agents, native apps, SMS/WhatsApp, connected-user debt confirm UX, commercial billing.
11. **Never output the completion promise until every story US-01…US-06 has Status = Done and Release 2 exit criteria in `RELEASE-2-TASKS.md` are satisfied.**

### Iteration procedure

```text
1. Read PROGRESS.md → identify current story + next unchecked subtask ID (e.g. US-01.G1).
2. Read that story file + PRD refs + existing code touchpoints listed in the story.
3. Execute ONLY that subtask:
   - Gather: inspect code, write decisions into Story notes; no large code changes.
   - Plan: write concrete schema/API/UI plan into Story notes; for UI surfaces run **impeccable `shape`** first; still no feature merge unless trivial scaffolding.
   - Implement: code the planned slice; migration + RLS for new tables; follow existing patterns; UI changes follow impeccable craft-floor.
   - Test: add/run tests listed; fix failures.
   - Validate: run manual checklist; for UI run impeccable `polish`/`harden`/(as listed); document residual manual checks in Story notes if environment lacks browser.
4. Check off the subtask. Update PROGRESS.md iteration log.
5. Commit if code changed and checks pass.
6. End the iteration. Do not start the next subtask in the same iteration unless the current one was Gather/Plan-only and took <5 minutes — prefer one subtask per iteration.
```

### Completion

When US-01 through US-06 are Done and exit criteria are met:

1. Set `docs/CONTEXT.md` focus to “Release 2 complete — choose next (R3 or polish)”.
2. Ensure `PROGRESS.md` shows 6/6 done.
3. Output exactly:

```text
<promise>RELEASE_2_COMPLETE</promise>
```

If blocked (missing secrets, infra, or a product decision not covered by defaults): document under PROGRESS.md Blockers, commit the docs, and end the iteration **without** the promise so a human can unblock. Do not fake completion.

### Escape hatch

After repeated failures on the same subtask (same ID in 3+ consecutive iterations), write a blocker with what was tried, revert broken code if needed, and stop claiming progress on that ID until a human updates the story notes.
