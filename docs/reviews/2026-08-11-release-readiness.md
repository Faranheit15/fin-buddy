# Release readiness update — 2026-08-11

## Decision

The codebase is ready to enter the deployment sequence on the existing free-tier architecture: Vercel for Next.js, FastAPI Cloud for the API, and Supabase for Auth, Storage, and Postgres. This work adds **no** paid cache, queue, database, monitoring, or hosting dependency.

Do not push or deploy until the release owner completes two environment actions: configure the server-only `BACKEND_URL` in Vercel and run the reviewed Alembic migration against the target Supabase database exactly once.

## Remediated findings

| ID | Outcome |
| --- | --- |
| SEC-01 | Browser tokens are no longer returned by a session endpoint. A same-origin Next.js BFF owns HttpOnly cookies, strips browser credential headers, attaches the backend bearer token server-side, and sanitizes auth responses. |
| SEC-02 | Statement uploads have content-length and streamed chunk limits before parsing. Oversize bodies receive a 413 response without an unbounded `UploadFile.read()`. |
| SEC-03 | Rate limiting uses existing Supabase Postgres with atomic PostgreSQL upserts and hashed keys. The bounded in-process limiter remains only for local development/tests. |
| SEC-04 | A nonce-based CSP, HSTS, frame denial, permissions policy, and no-store handling are applied at the Next proxy boundary. |
| SEC-05 | API, activity, and error logs are automatically purged after 90 days by default, using the existing database. |
| REL-01 | Native Linux Docker builds now succeed for both backend and frontend. |
| UX-01–03 | Authenticated dashboard failures are explicit and recoverable; mobile has a primary action; theme preference persists and remains keyboard reachable. |

## Release-owner checklist

1. In Supabase, create/confirm the private `statements` Storage bucket and production Auth Site URL/callback URL.
2. Apply the migration exactly once, before API replicas serve traffic:

   ```bash
   cd backend
   uv run alembic upgrade head
   ```

   This creates `rate_limit_windows`. Keep `AUTO_MIGRATE=false` in FastAPI Cloud afterward.
3. Configure FastAPI Cloud with the existing Supabase secrets, `STATEMENT_STORAGE_BACKEND=supabase`, a unique `JOB_RUNNER_SECRET`, and `CORS_ORIGINS=` (empty). Browsers no longer call FastAPI cross-origin.
4. Configure Vercel with root directory `frontend`, `NEXT_PUBLIC_APP_URL=https://<app-domain>`, and the **server-only** `BACKEND_URL=https://<fastapi-domain>`. Do not add Supabase service-role/JWT secrets to Vercel.
5. Deploy backend, confirm `GET /api/v1/health`, then deploy frontend.
6. Run the smoke list in [`docs/DEPLOY.md`](../DEPLOY.md): login, authenticated data entry, statement upload, restart/redeploy with a stored statement, and logout.

## Validation evidence

| Gate | Result |
| --- | --- |
| Backend Ruff | Passed |
| Backend MyPy | Passed: 95 source files |
| Backend tests | Passed: 121 tests (one upstream Starlette/httpx deprecation warning) |
| Alembic graph | Passed: `20260810_0014 (head)` |
| Frontend TypeScript | Passed |
| Frontend ESLint source check | Passed |
| Native Linux frontend production image | Passed |
| Native Linux backend production image | Passed |
| Compose configuration | Passed |
| Diff integrity | Passed: `git diff --check` |

## Deferred, non-blocking follow-up queue

- REL-02: automate the one-off migration approval/backup gate in the chosen CI provider.
- REL-03: enable repository-host dependency/secret scanning and scheduled update PRs.
- QLT-01: add browser, accessibility, and mobile-viewport coverage against a seeded test Supabase project.
- ARC-01: decide which agent/runtime assets are product-owned and enforce that policy in `.gitignore`.

The detailed repeatable queue remains in [production-remediation-loop.md](production-remediation-loop.md).
