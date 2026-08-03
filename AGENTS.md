# Repository Guidelines

## Project Structure & Module Organization

Fin Buddy is a two-app repository without monorepo tooling. `frontend/` contains the Next.js, TypeScript, Tailwind, and shadcn/ui web app; route files live under `frontend/src/app`, reusable UI under `frontend/src/components`, feature modules under `frontend/src/features`, and API clients/utilities under `frontend/src/lib`. `backend/` contains the FastAPI service; code is organized into `app/api`, `app/core`, `app/db`, `app/domain`, `app/models`, `app/schemas`, and `app/services`. Backend tests are in `backend/tests`. Product and architecture notes live in `docs/`, with root-level `README.md`, `PRODUCT.md`, and `DESIGN.md` for broader context.

## Build, Test, and Development Commands

Backend:

```bash
cd backend
uv sync --group dev
uv run uvicorn app.main:app --reload --port 8000
uv run pytest
uv run ruff check .
uv run mypy app
```

Frontend:

```bash
cd frontend
bun install
bun run dev
bun run lint
bun run typecheck
bun run build
```

Use `docker compose up -d --build` from the repository root to run both apps locally against Supabase.

## Coding Style & Naming Conventions

Python targets 3.12, uses Ruff with a 100-character line length, and enforces strict mypy. Keep modules snake_case, classes PascalCase, and tests named `test_*.py`. TypeScript should stay type-safe and component-focused: React components use PascalCase, hooks use `use*`, route directories follow Next.js conventions, and shared helpers stay in `frontend/src/lib`. Run Prettier with `bun run format` when formatting frontend files.

## Testing Guidelines

Backend tests use pytest with `pytest-asyncio`; add focused tests in `backend/tests` for API, domain, parser, and service behavior. Run `uv run pytest` before backend changes land. The frontend currently relies on linting, typechecking, and production build validation; run `bun run lint`, `bun run typecheck`, and `bun run build` for UI changes.

## Commit & Pull Request Guidelines

This repository has no established commit history yet. Use short, imperative commit subjects such as `Add statement parser tests` or `Fix dashboard totals`. Pull requests should include a brief summary, verification commands run, linked issues or product notes when applicable, and screenshots for visible frontend changes.

## Security & Configuration Tips

Never commit `.env` files or Supabase secrets. Start from `.env.example` or `backend/.env.example`, keep service-role keys backend-only, and update allowed Supabase redirect URLs and backend CORS origins when changing local or deployed hosts.
