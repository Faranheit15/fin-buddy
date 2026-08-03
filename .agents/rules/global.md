# Fin Buddy Global Agent Rules

These rules apply to all tasks in this workspace.

1. **Root Guidelines**: Always respect the guidelines defined in `AGENTS.md` at the repository root.
2. **Task Routing**: Refer to `docs/ROUTING.md` to determine which modules to touch for a given task.
3. **Project Context**: Check `docs/CONTEXT.md` and `docs/GOTCHAS.md` to avoid repeating mistakes or violating boundaries.
4. **Nested Contexts**: 
   - For tasks in `frontend/`, adhere to the rules in `frontend/AGENTS.md`.
   - For tasks in `backend/`, adhere to the rules in `backend/AGENTS.md`.
5. **Definitions of Done**: Never mark a task as finished until the relevant tests and checks (defined in the `AGENTS.md` files) have passed.
