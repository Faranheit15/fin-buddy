# Productionization & Product Polish — One-story loop

Use this prompt for a fresh implementation-loop iteration. The loop owns one
user story at a time; it must not silently become a multi-story sprint.

```text
You are implementing Fin Buddy productionization and product polish.

1. Treat the source tree and tests as the primary source of truth. Read the
   root AGENTS.md, docs/CONTEXT.md, docs/GOTCHAS.md, docs/ROUTING.md, this
   plan's README.md and PROGRESS.md, docs/user-input-needed.md, and the
   selected story before changing anything. Read frontend/AGENTS.md for
   frontend work and backend/AGENTS.md for backend work. Load the
   `.agents/skills/fin-buddy-production-loop` skill when the client supports
   project skills.

2. Select the first story in PROGRESS.md whose status is todo or in_progress.
   Work on only that story in this iteration. Do not start another story after
   the selected story reaches done.

3. Read the complete selected story. Set it to in_progress in the story file
   and PROGRESS.md before implementation. Write a short dated note describing
   the baseline, intended approach, and touched boundary.

4. Complete Gather, Plan, Implement, Test, and Validate in order. For every
   task, produce the evidence requested by that task. Start with a failing
   test, reproduction, query snapshot, screenshot, or other observable baseline
   before changing behavior.

5. Keep the architecture intact: Next.js frontend, FastAPI backend, and
   Supabase Auth/Postgres/Storage. Never import across frontend/backend. Never
   expose a service-role key. Keep money in integer paise and keep contact
   settlements separate from formal obligations.

6. External changes require extra care. Resolve the exact project, deployment,
   bucket, function, or database target first. Never invent a secret or use a
   production user record as a fixture. If a required credential or product
   decision is missing, leave the story in_progress and record the exact
   blocker instead of making an unsafe assumption.

7. Any visible UI work must use the impeccable skill: shape the surface before
   coding, follow the Ledger Shelf design source of truth, then run the
   applicable polish, harden, clarify, onboard, or audit checks. Preserve
   existing dense operate-mode behavior while improving touch and keyboard use.

8. Run the relevant verification gates. At minimum:

   backend:  cd backend && uv run pytest -q && uv run ruff check . && uv run mypy app
   frontend: cd frontend && bun run lint && bun run typecheck && bun run build
   config:   docker compose config --quiet

   Run browser, accessibility, migration, or SQL integration checks whenever
   the selected story requires them. Do not claim Docker evidence if Docker is
   unavailable.

   Keep the cost contract strict: no paid AI/API calls, paid plans, custom
   domains, paid integrations, or always-on resources. A Supabase activity
   probe is optional, once daily at most, bounded, secret-protected, and
   best-effort; it cannot guarantee that a Free project never pauses.

9. Re-read the selected story's acceptance criteria. If every criterion is
   met, mark only that story done, append the commands and results to its
   evidence section and PROGRESS.md, and commit with a short imperative subject.
   If any criterion is unmet, leave the story in_progress and document the
   exact next measurable task or blocker. Never mark a story done because the
   code merely builds.

10. End the iteration. Do not output the plan-complete promise while any story
    is not done.
```

## Completion promise

When all fifteen stories are `done`, run the full gates again, review
`git diff --check`, verify the live release checklist, update `PROGRESS.md`,
and output:

```text
<promise>FIN_BUDDY_PRODUCTIONIZATION_COMPLETE</promise>
```
