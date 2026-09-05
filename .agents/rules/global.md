# Fin Buddy Global Agent Rules

These rules apply to all tasks in this workspace.

1. **Root Guidelines**: Always respect the guidelines defined in `AGENTS.md` at the repository root.
2. **Task Routing**: Refer to `docs/ROUTING.md` to determine which modules to touch for a given task.
3. **Project Context**: Check `docs/CONTEXT.md` and `docs/GOTCHAS.md` to avoid repeating mistakes or violating boundaries.
4. **Nested Contexts**:
   - For tasks in `frontend/`, adhere to the rules in `frontend/AGENTS.md`.
   - For tasks in `backend/`, adhere to the rules in `backend/AGENTS.md`.
5. **Definitions of Done**: Never mark a task as finished until the relevant tests and checks (defined in the `AGENTS.md` files) have passed.
6. **Human inputs**: Read `docs/user-input-needed.md` before auth, deployment, migration, or product-policy work. Update statuses and paths without recording secret values.
7. **Free-only operation**: Keep Vercel Hobby, FastAPI Cloud Hobby, and Supabase Free assumptions explicit. Never upgrade a plan, attach billing, use paid AI, or add paid infrastructure without an explicit owner request.
8. **One-story loop**: Use `.agents/skills/fin-buddy-production-loop/SKILL.md`; select and finish only one active productionization story per iteration.
