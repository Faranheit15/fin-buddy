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

## Commit & Pull Request Guidelines
This repository has no established commit history yet. Use short, imperative commit subjects such as `Add statement parser tests` or `Fix dashboard totals`. Pull requests should include a brief summary, verification commands run, linked issues or product notes when applicable, and screenshots for visible frontend changes.

## Security & Configuration Tips
Never commit `.env` files or Supabase secrets. Start from `.env.example` or `backend/.env.example`, keep service-role keys backend-only, and update allowed Supabase redirect URLs and backend CORS origins when changing local or deployed hosts.

## Definition of Done (DoD) - Root
To verify the entire system works together locally:
```bash
docker compose up -d --build
```
Ensure both frontend and backend containers are healthy and communicating with Supabase.
