# Release 2 — User Stories

| Field | Value |
|--------|--------|
| **Release** | Fin Buddy Release 2 |
| **PRD** | [`../2026-07-27-fin-buddy-prd.md`](../2026-07-27-fin-buddy-prd.md) v2.0 |
| **Workstreams** | [`../RELEASE-2-TASKS.md`](../RELEASE-2-TASKS.md) |
| **Progress** | [`PROGRESS.md`](PROGRESS.md) |
| **Ralph prompt** | [`RALPH-LOOP-PROMPT.md`](RALPH-LOOP-PROMPT.md) |

## How to use

1. Implement stories **in order** (dependencies below).
2. Within a story, complete phases in order: **Gather → Plan → Implement → Test → Validate**.
3. Mark subtask checkboxes `[x]` in the story file when done.
4. Update [`PROGRESS.md`](PROGRESS.md) after each completed subtask or story.
5. Autonomous agents: use [`RALPH-LOOP-PROMPT.md`](RALPH-LOOP-PROMPT.md).

## Story map

| ID | Story | Maps to | Depends on |
|----|--------|---------|------------|
| [US-01](US-01-auditable-ledger.md) | Auditable ledger foundation | R2A | — |
| [US-02](US-02-multi-account-balances.md) | Multi-account balances | R2B | US-01 |
| [US-03](US-03-categories-transfers-splits.md) | Categories, transfers & splits | R2C | US-01, US-02 |
| [US-04](US-04-debts-and-loans.md) | Debts & loans | R2D | US-02 |
| [US-05](US-05-card-emis-and-gst.md) | Card EMIs & GST tracking | R2E | US-01, US-02 |
| [US-06](US-06-insights-imports-reminders.md) | Insights, imports/exports & reminders | R2F + R2G + R2H | US-02…US-05 |

```text
US-01 ──► US-02 ──► US-03 ──► US-06
              │         ▲
              ├──► US-04 ─┘
              └──► US-05 ─┘
```

## Architecture anchors (do not violate)

- Two apps only: `frontend/` (Next.js) and `backend/` (FastAPI). No cross-imports.
- Money: integer **paise** (`bigint`). Never float math in domain/services.
- Org-scoped data + membership checks + Supabase RLS on new tables.
- Layers: `models` → `services` / `domain` → `api/v1` → frontend `lib/api` + `app/app/*`.
- Additive Alembic migrations; backfill existing MVP rows safely.
- Imports always require human review before posting.

## Frontend UI — Impeccable (required)

Any Plan / Implement / Validate work that creates or changes **user-visible UI** must use the **impeccable** skill (`.claude/skills/impeccable/SKILL.md`):

1. Run `node .claude/skills/impeccable/scripts/context.mjs` once per session (respect `PRODUCT.md` / `DESIGN.md`; Operate mode for app surfaces).
2. **Plan:** `shape` the surface before coding new pages, flows, empty states, or major dashboard sections.
3. **Implement:** follow `reference/craft-floor.md` before editing UI; preserve The Ledger Shelf / existing shell; no generic AI-dashboard look.
4. **Validate:** run `polish` and `harden` on the touched surface; use `onboard` for empty states; `audit` for a11y/responsive; `clarify` for copy/errors when needed.

Skip Impeccable for API-client-only or pure type changes with no visual delta.

## Verification commands

**Backend** (`backend/`):

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

**Frontend** (`frontend/`):

```bash
bun run lint
bun run typecheck
bun run build
```
