# Production remediation loop

This is the repository-native Ralph-loop queue for the findings in the [2026-08-10 production readiness audit](2026-08-10-production-readiness-audit.md). It follows the existing Release 2 loop convention while keeping audit remediation separately tracked.

## State

Update this table at the end of every iteration. Do not change a task to `done` without its listed acceptance evidence.

| Order | ID     | Priority | Status | One-iteration objective                                      |
| ----: | ------ | -------- | ------ | ------------------------------------------------------------ |
|     1 | SEC-01 | P1       | `done` | Design and implement the token-free BFF session boundary.    |
|     2 | SEC-02 | P1       | `done` | Bound and stream statement uploads before parsing.           |
|     3 | REL-01 | P1       | `done` | Make a clean Linux/CI production build reproducible.         |
|     4 | SEC-03 | P2       | `done` | Replace process-local rate limiting with shared enforcement. |
|     5 | SEC-04 | P2       | `done` | Introduce, observe, and enforce a nonce-based CSP.           |
|     6 | SEC-05 | P2       | `done` | Apply logged-data retention and access controls.             |
|     7 | REL-02 | P2       | `todo` | Add an approved, controlled migration gate.                  |
|     8 | REL-03 | P2       | `todo` | Add dependency, secret, and SBOM security automation.        |
|     9 | QLT-01 | P2       | `todo` | Add browser/component/a11y coverage for core flows.          |
|    10 | UX-01  | P2       | `done` | Make demo and failure states explicit and recoverable.       |
|    11 | UX-02  | P2       | `done` | Restore a mobile primary action and accessible targets.      |
|    12 | UX-03  | P3       | `done` | Decide, implement, and test theme preference behaviour.      |
|    13 | ARC-01 | P3       | `todo` | Remove or document tracked runtime-agent assets.             |

## How to run

Use the same fresh-agent loop supported by the project’s existing Ralph prompt. The command below is an example when the `ralph-loop` plugin is installed:

```bash
/ralph-loop "$(cat docs/reviews/production-remediation-loop.md)" --max-iterations 40 --completion-promise "PRODUCTION_REMEDIATION_COMPLETE"
```

For another agent runner, send the **Prompt body** below as the only task for each new iteration. Stop only when it returns the completion promise exactly, or when a documented blocker needs a human decision.

## Prompt body

You are remediating Fin Buddy’s production-readiness findings in a fresh, one-subtask-per-iteration loop.

1. Treat disk as source of truth. Read `AGENTS.md`, `frontend/AGENTS.md`, `backend/AGENTS.md`, `docs/GOTCHAS.md`, `docs/CONTEXT.md`, `docs/reviews/2026-08-10-production-readiness-audit.md`, and this file before changing code.
2. Select the first row whose Status is `todo` or `in_progress`. Work on **only that ID** this iteration. Keep P1 items ahead of P2/P3 items.
3. Read the full finding and its required fix/acceptance evidence in the audit. Set the task to `in_progress` before implementation. Add a concise dated note below this prompt stating the intended approach and touched boundary.
4. Write a failing test, reproduction, or observable baseline before changing behaviour. Implement the smallest secure vertical slice. Do not rewrite the stack: retain Next.js + FastAPI + Supabase, and never import across frontend/backend.
5. For visible UI, follow the repository’s Impeccable workflow before editing. For auth, upload, tenancy, secrets, redirects, logs, or rate limits, add a regression test that proves the unsafe path is closed.
6. Run the relevant gates. At minimum, code changes must pass the applicable checks:

   ```text
   backend: uv run pytest -q; uv run ruff check .; uv run mypy app
   frontend: bun run lint; bun run typecheck; bun run build
   integration: docker compose config --quiet (and a targeted integration test when relevant)
   ```

   Use the native Linux/container toolchain for frontend build verification. A Windows Node process from a WSL UNC path is not valid REL-01 evidence.

7. Re-read the task’s acceptance evidence. If it is fully met, set Status to `done`, record the commands/results in the iteration log, and commit the verified change with a short imperative subject. If not, leave it `in_progress` with the exact blocker or next measurable slice.
8. End the iteration. Do not begin the next task in the same iteration. Never output the completion promise while any table row is not `done`.

### Iteration log

Append one row per completed or blocked iteration.

| Date       | ID             | Result | Evidence / blocker                                                                                                                                          |
| ---------- | -------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-08-10 | Audit baseline | fixed  | P0 job auth, auth redirects, proxy trust, bounded limiter, logging redaction, headers, Compose/CI hardening, Next proxy migration, and formatting complete. |
| 2026-08-11 | SEC-01–05, REL-01, UX-01–03 | fixed | BFF token boundary, bounded uploads, Supabase Postgres shared rate limits and retention, nonce CSP, native Docker production builds, explicit error recovery, mobile primary action, and persisted theme preference validated. |

### Completion

When every row has Status `done`, re-run the full quality gates, review `git diff --check`, update the audit with the final evidence, and output exactly:

```text
<promise>PRODUCTION_REMEDIATION_COMPLETE</promise>
```
