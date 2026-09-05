---
name: fin-buddy-production-loop
description: Runs one Fin Buddy productionization or product-polish user-story loop with safe planning, implementation, testing, and verification. Use when changing Fin Buddy code, deployment configuration, database behavior, or the active story plan.
---

# Fin Buddy one-story loop

Use this skill for exactly one implementation-loop iteration. It is shared by
Codex, Claude Code, Google Antigravity GUI, and Google Antigravity CLI.

## Before editing

1. Read the root `AGENTS.md`, `docs/ROUTING.md`, `docs/CONTEXT.md`, and
   `docs/GOTCHAS.md`.
2. Read `docs/user-input-needed.md` and the complete active plan README,
   progress tracker, and selected story under `docs/prd/productionization/`.
3. Read `frontend/AGENTS.md` for frontend work and `backend/AGENTS.md` for
   backend work. Keep the frontend/backend boundary absolute.
4. Select the first `todo` or `in_progress` story in `PROGRESS.md`. Work on
   only that story.
5. If a missing user input blocks safe progress, record the exact row and
   dashboard path in `docs/user-input-needed.md`; do not invent a secret,
   project ID, role policy, or production target.

## Gather → Plan → Implement → Test → Validate

- **Gather:** capture a failing reproduction, baseline query, screenshot,
  response, or configuration snapshot without secrets.
- **Plan:** name the files, boundaries, data-safety rules, rollback, and
  evidence needed for every task.
- **Implement:** make the smallest coherent change. Use existing project
  patterns and migrations; never import across frontend/backend.
- **Test:** run the story-specific checks plus the applicable backend,
  frontend, Docker, browser, accessibility, and migration gates.
- **Validate:** re-read every acceptance criterion, confirm no secret or
  quota-risk change slipped in, update the story and `PROGRESS.md`, and stop.

## Non-negotiable safety rules

- Service-role, JWT, database, OAuth, scheduler, and AI/API keys remain in
  their provider secret stores or gitignored local files. Never print them.
- Keep monetary values as integer paise and preserve IST semantics.
- Supabase changes require a verified project target, versioned migration, and
  policy/grant evidence. Treat RLS as defense in depth, not a replacement for
  API authorization.
- The target is `$0 billed cost` under current free-tier quotas and terms. Do
  not upgrade a plan, attach billing, use paid AI, or add paid infrastructure.
- A Supabase keepalive is only a low-frequency, protected, best-effort activity
  probe. It must not write dummy data, run in a browser loop, or promise that
  Free projects never pause.
- UI work must load and follow the existing `impeccable` skill and the Ledger
  Shelf design source of truth.
- Run `tools/agent-hooks/preflight.sh` and `post-task.sh` through the native
  hook integration or manually before closing the loop.

## Closing the loop

Mark one story `done` only when all its acceptance criteria have evidence. If a
credential, external decision, or deployment access is missing, leave the
story `in_progress`, update `docs/user-input-needed.md`, and state the exact
next owner action. Do not start the next story in the same loop.
