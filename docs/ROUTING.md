# Agent routing matrix

Use this matrix to locate the relevant files for your current task. Read the
root [`AGENTS.md`](../AGENTS.md) first, then use the closest service-specific
guidance when changing code.

| If you need to change… | Start with… |
| --- | --- |
| **Frontend UI/pages** | [`frontend/src/app`](../frontend/src/app) and [`frontend/AGENTS.md`](../frontend/AGENTS.md) |
| **Frontend components** | [`frontend/src/components`](../frontend/src/components) |
| **Frontend state/logic** | [`frontend/src/features`](../frontend/src/features) and [`frontend/src/lib`](../frontend/src/lib) |
| **Backend API endpoints** | [`backend/app/api`](../backend/app/api) and [`backend/AGENTS.md`](../backend/AGENTS.md) |
| **Database schema/models** | [`backend/app/models`](../backend/app/models) and [`backend/alembic`](../backend/alembic) |
| **Backend business logic** | [`backend/app/services`](../backend/app/services) and [`backend/app/domain`](../backend/app/domain) |
| **Environment configuration** | [`backend/.env.example`](../backend/.env.example) and [`.env.example`](../.env.example) |
| **Product requirements or release status** | [`prd/README.md`](prd/README.md), [`prd/productionization/PROGRESS.md`](prd/productionization/PROGRESS.md), and [`CONTEXT.md`](CONTEXT.md) |
| **Deployment or release evidence** | [`DEPLOY.md`](DEPLOY.md) and [`reviews/README.md`](reviews/README.md) |
| **Project-specific traps** | [`GOTCHAS.md`](GOTCHAS.md) |
| **Human decisions or credentials** | [`user-input-needed.md`](user-input-needed.md) — statuses and destinations only, never secret values |
| **Agent interoperability and hooks** | [`AGENT-TOOLING.md`](AGENT-TOOLING.md), root `GEMINI.md`, `.agents/skills/`, `.agents/hooks.json`, and `.claude/settings.json` |

## Boundary reminder

Fin Buddy has two sibling applications and no monorepo tooling. Keep imports
within `frontend/` or `backend/`; use the API layer for communication between
them.
