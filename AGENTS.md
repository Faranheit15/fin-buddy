# Fin Buddy - Global Architecture and Agent Guidelines

## System Design and Boundaries
Fin Buddy is a two-app repository without monorepo tooling:
- **`frontend/`**: Next.js, TypeScript, Tailwind, and shadcn/ui web app.
- **`backend/`**: FastAPI service (Python 3.12).

The boundary is absolute: do not import files across the frontend/backend divide. Use the API layer for communication.

## Routing and Delegation
This file contains global rules. For specific tasks, ALWAYS read the nested contexts:

- Working on frontend? Read `frontend/AGENTS.md`
- Working on backend? Read `backend/AGENTS.md`
- Not sure where to start? Read `docs/ROUTING.md`
- Wondering about a project quirk? Read `docs/GOTCHAS.md`
- Wondering what feature we are currently working on? Read `docs/CONTEXT.md`
- Needing a human decision or credential? Read `docs/user-input-needed.md`
- Using a repeatable productionization loop? Read `.agents/skills/fin-buddy-production-loop/SKILL.md`

## Shared agent tooling

`AGENTS.md` is the canonical project contract for ChatGPT Codex, Claude Code,
and Google Antigravity GUI/CLI. `CLAUDE.md` and `GEMINI.md` are thin adapters;
do not create a competing architecture manual in a vendor-specific file.
Shared skills live in `.agents/skills/`, Claude's native bridge lives in
`.claude/skills/`, and native hook manifests are kept under `.claude/` and
`.agents/`. See [`docs/AGENT-TOOLING.md`](docs/AGENT-TOOLING.md) for the
compatibility map and local validation commands.

## Commit & Pull Request Guidelines
Use short, imperative commit subjects such as `Add statement parser tests` or `Fix dashboard totals`. Pull requests should include a brief summary, verification commands run, linked issues or product notes when applicable, and screenshots for visible frontend changes.

## Security & Configuration Tips
Never commit `.env` files or Supabase secrets. Start from `.env.example` or `backend/.env.example`, keep service-role keys backend-only, and update allowed Supabase redirect URLs and backend CORS origins when changing local or deployed hosts.

Never ask the owner to paste a secret into chat or a tracked file. Record
missing credentials, dashboard destinations, and non-secret identifiers in
[`docs/user-input-needed.md`](docs/user-input-needed.md). The project targets
$0 billed cost only within the current free-tier quotas and terms: do not
upgrade plans, attach billing, call paid AI APIs, or add paid infrastructure
without an explicit user request. A scheduled Supabase activity probe is
best-effort and is not an uptime or no-pause guarantee.

## Definition of Done (DoD) - Root
To verify the entire system works together locally:
```bash
docker compose up -d --build
```
Ensure both frontend and backend containers are healthy and communicating with Supabase.
