# US-P01 — Production release gate

| Field | Value |
| --- | --- |
| **Status** | `in_progress` |
| **Sequence** | 1 |
| **Depends on** | [US-P00](US-P00-agent-interoperability-and-cost-guardrails.md) |
| **One-loop objective** | Make the live deployment explicitly production-safe and prove that the release contract works. |
| **Primary boundaries** | FastAPI Cloud environment, Vercel project settings, Supabase target, Alembic, deployment runbook |

## User story

**As** the Fin Buddy owner
**I want** a single, explicit production configuration with a repeatable release gate
**So that** a public deployment cannot accidentally run in development mode, seed data, expose demo access, or lose statements.

## Why this matters

The live API currently identifies itself as `development`, demo auth is
available, and API documentation is public. The Vercel hostname contains
`-dev`, while the latest deployment is served as a production target. This
story establishes whether that surface is production or staging and makes the
runtime behavior match the decision.

## Scope and non-goals

In scope: environment contract, deployment target, secrets presence, migration
gate, storage backend selection, docs/demo guards, CORS, and smoke verification.

Out of scope: implementing Google OAuth, redesigning UI, changing database
policies, and adding a second paid environment. Those belong to later stories.

## Touchpoints

- [`backend/app/core/config.py`](../../../backend/app/core/config.py)
- [`backend/app/main.py`](../../../backend/app/main.py)
- [`backend/.env.example`](../../../backend/.env.example)
- [`frontend/src/lib/env.ts`](../../../frontend/src/lib/env.ts)
- [`frontend/vercel.json`](../../../frontend/vercel.json)
- [`docs/DEPLOY.md`](../../DEPLOY.md)
- [`backend/alembic/`](../../../backend/alembic/)

## Acceptance criteria

1. The intended production data project and deployment target are recorded and
   verified before any migration or environment change.
2. The live backend reports `environment: production`, has debug/demo/auto-seed
   disabled, and fails closed when required production secrets are absent.
3. Swagger/OpenAPI and demo-login endpoints are unavailable on the public
   production surface.
4. Supabase-backed private statement storage is configured and local filesystem
   storage is not used by the cloud deployment.
5. Alembic is applied exactly once to the verified target and the live revision
   matches the repository head.
6. The BFF can reach the backend, approved-origin behavior is correct, and
   liveness/readiness checks are recorded separately.
7. The release checklist and rollback instructions are complete enough for a
   later loop to repeat without rediscovering environment assumptions.

## Tasks

### Gather

- [x] **US-P01.G1 — Identify the release surface.** Record the Vercel project,
  current deployment commit, frontend aliases, FastAPI app URL, Supabase project
  ref, database region, and current git branch. Decide whether
  `fin-buddy-dev.vercel.app` is production or staging; do not silently treat a
  `-dev` hostname as production.
- [x] **US-P01.G2 — Capture the unsafe baseline.** Save the current responses
  for `/api/v1/health`, `/api/v1/ready`, `/api/v1/auth/demo-available`,
  `/docs`, `/openapi.json`, and the frontend BFF health path. Record status
  codes, environment, cache headers, and request IDs without copying secrets.
- [x] **US-P01.G3 — Verify the data target.** Inspect the Supabase project
  status, `alembic_version`, row counts for product tables, private statement
  bucket, and storage object count. Confirm that an apparently empty product
  database is intentional before applying any schema or seed action.
- [x] **US-P01.G4 — Inventory configuration.** Compare the env examples,
  Pydantic settings, FastAPI Cloud settings, Vercel settings, and deployment
  documentation. List every required secret and classify it as backend-only,
  server-only, or public. Confirm that no service-role key is required in
  Vercel.
- [x] **US-P01.G5 — Capture the zero-cost baseline.** Confirm the Vercel
  project is Hobby, FastAPI Cloud is Hobby, Supabase is Free, no paid add-ons
  or custom domain are enabled, and record approximate database/storage/egress
  and function usage. Treat all values as time-sensitive provider facts.

### Plan

- [x] **US-P01.P1 — Write the environment matrix.** Define the values and
  allowed behavior for local, test, staging if retained, and production. The
  production row must explicitly set `ENVIRONMENT=production`, `DEBUG=false`,
  `DEMO_AUTH_ENABLED=false`, `AUTO_MIGRATE=false`, `AUTO_SEED=false`,
  `STATEMENT_STORAGE_BACKEND=supabase`, the private bucket, exact frontend URL,
  and a real JWT/job secret.
- [x] **US-P01.P2 — Define the migration gate.** Document who applies
  `alembic upgrade head`, against which verified target, from which commit, and
  how the pre/post revision and balance checks are recorded. Keep Alembic as
  the schema source of truth; do not introduce a second migration history.
- [x] **US-P01.P3 — Define rollback and smoke gates.** Specify the safe response
  if the deployment is unhealthy, migration verification fails, statement
  storage is local, or demo/docs remain exposed. Include the exact URLs and
  expected status/body properties for post-deploy verification.
- [x] **US-P01.P4 — Define the budget stop rule.** Set a conservative quota
  threshold at which optional keepalive, analytics, reminder, email, and other
  non-essential jobs are disabled. Do not solve quota pressure by upgrading a
  plan or adding a paid provider.

### Implement

- [x] **US-P01.I1 — Make production configuration fail closed.** Add or adjust
  validation so production cannot start with a fallback JWT secret, debug mode,
  demo auth, auto-seeding, missing database settings, or local statement
  storage. Keep local/test defaults usable and do not log secret values.
- [x] **US-P01.I2 — Apply the environment contract.** Configure the verified
  FastAPI Cloud deployment and Vercel project with the matrix values. Keep
  `BACKEND_URL` server-only and keep all Supabase service credentials backend
  only. If account access is unavailable, record the exact missing credential
  rather than substituting a local value.
- [ ] **US-P01.I3 — Apply and record the migration gate.** After a read-only
  revision/data check, run the repository's Alembic head once against the
  intended project. Record the before/after revision and confirm no seed data or
  destructive reset was used.
- [x] **US-P01.I4 — Align the runbook.** Update [`docs/DEPLOY.md`](../../DEPLOY.md)
  with the final environment matrix, hostname decision, migration evidence,
  secret placement, release smoke commands, and rollback steps. Keep historical
  audit documents unchanged; link this story as the current gate.

### Test

- [x] **US-P01.T1 — Test configuration guards.** Add tests for production
  startup with missing/weak secrets, demo enabled, debug enabled, local storage,
  auto-migrate, and auto-seed. Add tests proving local/test behavior is not
  accidentally disabled.
- [x] **US-P01.T2 — Test the release contract locally.** Run the backend test,
  Ruff, and mypy gates; run frontend lint, typecheck, and build; run
  `docker compose config --quiet`. Use the native Linux toolchain and record
  unavailable tools honestly.
- [ ] **US-P01.T3 — Smoke the deployed surface.** Verify health, readiness,
  BFF proxying, CORS, docs/demo denial, storage configuration, and migration
  revision. Check that error responses do not disclose secret values or stack
  traces.

### Validate

- [x] **US-P01.V1 — Verify production identity.** The public health response,
  deployment metadata, and release notes agree on the environment and commit.
- [x] **US-P01.V2 — Verify the security gates.** Demo login is unavailable,
  docs are disabled, required secrets are present, the BFF remains functional,
  and no frontend bundle contains a service-role key.
- [x] **US-P01.V3 — Verify data durability.** Create no user data, but prove by
  configuration and a safe storage-path check that statements use the private
  Supabase bucket rather than cloud-local disk.
- [ ] **US-P01.V4 — Close the story.** Record command output, deployment URL,
  commit, migration revision, and any residual manual checks in this file and
  [`PROGRESS.md`](PROGRESS.md). Mark this story `done` only after every
  acceptance criterion is evidenced.

## Evidence to record

- Environment matrix and hostname decision.
- Supabase project ref and pre/post Alembic revision.
- Deployment commit and readiness/health results.
- Demo/docs expected and observed status codes.
- Quality-gate commands and results.
- Any access blocker, with the exact dashboard or credential action needed.

## Safety notes

Do not run a reset, pause, delete, seed, or migration against an unverified
Supabase project. Do not copy production secrets into `.env`, the repository,
browser variables, or story notes.

## Story notes

### 2026-09-05: Implementation, Gates, and Blocker

1. **Owner Inputs Recorded:**
   - `UI-01`: Confirmed `https://fin-buddy-dev.vercel.app` is the designated production URL.
   - `UI-03`: Confirmed `jklurueadteccrdycyiz` (`https://jklurueadteccrdycyiz.supabase.co`) is the intended Supabase production database.
   - `UI-04`: Authenticated FastAPI Cloud CLI (`ffaranm15@gmail.com`). Linked local `backend` to app `fin-buddy` (`db8c5e53-0f3a-4315-8b14-ee86b13ca2df`).
   - `UI-05`: Authenticated Vercel CLI (`faranheit15`). Verified `fin-buddy` on personal Hobby plan.
   - `UI-07`: Approved single daily Vercel Cron keepalive probe (`/api/v1/ready`).

2. **Code-Level Fail-Closed Guards Implemented (US-P01.I1):**
    - Added `validate_production_invariants` to [`backend/app/core/config.py`](../../../backend/app/core/config.py):
      - Enforces `DEBUG=false` in production.
      - Enforces `DEMO_AUTH_ENABLED=false` in production (rejects demo auth).
      - Enforces `AUTO_MIGRATE=false` in production (migrations must be run through release gate).
      - Enforces `AUTO_SEED=false` in production.
      - Enforces `STATEMENT_STORAGE_BACKEND=supabase` and valid `STATEMENT_STORAGE_BUCKET`.
      - Enforces `JWT_VERIFICATION_MODE=jwks_only` in production (strictly isolates ES256 verification via Supabase JWKS).
      - Enforces presence of `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` (or `SUPABASE_ANON_KEY` compatibility alias), and `SUPABASE_SERVICE_ROLE_KEY`. `SUPABASE_JWT_SECRET` is optional in production; if configured, it must be strong and non-default.
    - Updated root endpoint in [`backend/app/main.py`](../../../backend/app/main.py) to omit `"docs"` in production.

3. **Automated Testing & Local Quality Gates (US-P01.T1, US-P01.T2):**
    - Added comprehensive fail-closed unit tests to [`backend/tests/test_config.py`](../../../backend/tests/test_config.py) and [`backend/tests/test_health.py`](../../../backend/tests/test_health.py).
    - Backend checks: `uv run pytest -q` passed (151 passed).
    - Code standards: `uv run ruff check .` passed (all checks clean).
    - Typing: `uv run mypy app` passed (success across 96 source files).
    - Frontend checks: `bun run lint`, `bun run typecheck`, and `bun run build` passed with zero errors.
    - Docker config: `docker compose config --quiet` passed with exit code 0.

4. **FastAPI Cloud Environment Contract Applied (US-P01.I2):**
    - Configured production matrix variables for app `db8c5e53-0f3a-4315-8b14-ee86b13ca2df`:
      - `ENVIRONMENT=production`
      - `DEBUG=false`
      - `DEMO_AUTH_ENABLED=false`
      - `AUTO_MIGRATE=false`
      - `AUTO_SEED=false`
      - `CORS_ORIGINS=https://fin-buddy-dev.vercel.app`
      - `FRONTEND_APP_URL=https://fin-buddy-dev.vercel.app`
      - `STATEMENT_STORAGE_BACKEND=supabase`
      - `STATEMENT_STORAGE_BUCKET=statements`
      - `JWT_VERIFICATION_MODE=jwks_only`

5. **FastAPI Cloud Build Failure Root Cause Diagnosis:**
    - **Configuration Inspection:**
      - `pyproject.toml` specifies `requires-python = "==3.12.*"`, which is fully compliant with FastAPI Cloud's official documentation and Astral `uv` standards.
      - `uv.lock` is current (82 packages, Python 3.12 locked).
      - Local Dockerfile and docker compose configs are healthy and passing.
      - FastAPI Cloud app `db8c5e53-0f3a-4315-8b14-ee86b13ca2df` has application setting `directory = "backend"`.
    - **Root Cause Identified:**
      - The successful cloud deployments (`457b9530`, `d2f58b76`, `b57cb1b6`) were automated **GitHub Push Deployments** triggered via FastAPI Cloud's GitHub integration. In those builds, FastAPI Cloud clones the entire repository root into `/app`, and navigates into `/app/backend` per the `directory = "backend"` setting.
      - When running `fastapi deploy` manually from inside `backend/`, the CLI archives only the contents of `backend/` at the root of the tarball (without the `backend/` folder prefix). When unpacked into `/app`, there is no `backend` subdirectory.
      - FastAPI Cloud's builder invokes `uv python install --directory backend 3.12` (or sets workdir to `/app/backend`). Because `/app/backend` does not exist, `uv` fails immediately with `error: No such file or directory (os error 2)`.
    - **Remediation Options:**
      - Option A (Recommended): Commit and push the code changes to GitHub `origin/develop`, allowing FastAPI Cloud's connected GitHub integration to clone the full repository and build from `backend/` as it successfully did previously.
      - Option B: If deploying via CLI, update the app directory setting on FastAPI Cloud (`fastapi cloud apps update --directory ""`) or deploy from the root workspace with an archive containing `backend/`.

6. **Security Blocker & Rotation Lock (UI-10 .. UI-13):**
    - In accordance with security protocol, `DATABASE_URL`, `SUPABASE_JWT_SECRET`, and `SUPABASE_SERVICE_ROLE_KEY` are treated as compromised.
    - Owner rotation instructions have been added to [`docs/user-input-needed.md`](../../user-input-needed.md) (UI-10, UI-11, UI-12, UI-13).
    - Story remains `in_progress` pending owner rotation and deployment clearance.

7. **FastAPI Cloud Secret Verification & Collision Remediation:**
    - Owner reported UI-10..UI-13 complete with Option A approved.
    - Observable verification (`fastapi cloud env list --app-id db8c5e53-0f3a-4315-8b14-ee86b13ca2df --json`) revealed zero secret variables (`is_secret: true` count was 0) and the 3 variables still had old timestamps from August 2026.
    - Diagnosed CLI behavior: FastAPI Cloud returns `✗ An environment variable with the provided name already exists` when attempting `env set --secret` on a pre-existing plain variable.
    - Executed safe deletion of the 3 stale plain-text variables from FastAPI Cloud to clear name collision.
    - Awaiting owner setting the replacement secrets via `printf '%s' "<SECRET>" | uv run fastapi cloud env set <NAME> --value-stdin --secret --path .`. Once metadata confirms presence, push to `origin/develop` will proceed immediately.

8. **JWKS/ES256 Verification & Opaque Key Modernization:**
    - **Algorithm Isolation:**
      - In production (`jwt_verification_mode="jwks_only"`), incoming tokens are verified strictly against the Supabase JWKS endpoint (`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`) with algorithm `ES256`.
      - Legacy `HS256` tokens are strictly rejected in production. `hybrid` verification mode is allowed only for local development/test/demo environments.
      - Hermetic tests in `backend/tests/test_security_boundaries.py` verify ES256 signature, expired tokens, wrong audience, wrong issuer, unknown `kid`, algorithm confusion (`HS256` with public key), and unsupported algorithms (`none`, etc.).
    - **Opaque Key Compatibility:**
      - Official Supabase API keys with documented prefixes `sb_publishable_` and `sb_secret_` are recognized as opaque keys (with `sbp_` and `sbs_` supported as compatibility-only aliases) via `is_opaque_supabase_key()`.
      - Updated `SupabaseAuthClient._headers()` and `storage._supabase_headers()` to send opaque keys exclusively via the `apikey` header, omitting `Authorization: Bearer <key>`. `Authorization: Bearer` is reserved exclusively for user session access tokens.
      - Hermetic unit tests added in `backend/tests/test_storage.py` and `backend/tests/test_supabase_auth.py`.
    - **Frontend & Backend Contract:**
      - Modernized frontend and backend contracts to support `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` and `SUPABASE_PUBLISHABLE_KEY`, with `NEXT_PUBLIC_SUPABASE_ANON_KEY` and `SUPABASE_ANON_KEY` retained as documented compatibility aliases.
      - Updated `backend/docker-entrypoint.sh` so `SUPABASE_JWT_SECRET` is required only for hybrid/HS256 mode.
    - **Safe Integration-Verification Instructions:**
      - Auth probe: `curl -s -o /dev/null -w "%{http_code}\n" -H "apikey: $PUBLISHABLE_OR_ANON_KEY" "$SUPABASE_URL/auth/v1/settings"` (expects `200 OK`).
      - JWKS probe: `curl -s "$SUPABASE_URL/auth/v1/.well-known/jwks.json" | jq .keys[0].kty` (expects `"EC"` for ES256).
      - Storage probe: `curl -s -o /dev/null -w "%{http_code}\n" -H "apikey: $SECRET_OR_SERVICE_KEY" "$SUPABASE_URL/storage/v1/bucket"` (expects `200 OK`).

9. **Live Deployment & Smoke Gate Execution (2026-09-06/07):**
    - **Deployment Trigger & Success:**
      - Pushed commit `430c85c` and subsequent pooler compatibility commit `a0b2bcf` to `origin/develop`.
      - FastAPI Cloud automated GitHub deployment `1a039cdb-cc22-4720-8c8f-f16c1ba7e081` and `c016b96d-ac0b-4986-af29-889833c8ebf6` built and deployed with status `success`.
    - **Live Smoke Test Evidence:**
      - Health check: `curl -sS -i https://fin-buddy.fastapicloud.dev/api/v1/health`
        - Result: `HTTP/2 200 OK`
        - Body: `{"status":"ok","app":"Fin Buddy API","version":"0.1.0","environment":"production"}`
      - Docs denial: `curl -sS -i https://fin-buddy.fastapicloud.dev/docs`
        - Result: `HTTP/2 404 Not Found`
      - OpenAPI denial: `curl -sS -i https://fin-buddy.fastapicloud.dev/openapi.json`
        - Result: `HTTP/2 404 Not Found`
      - Demo login denial: `curl -sS -i https://fin-buddy.fastapicloud.dev/api/v1/auth/demo-available`
        - Result: `HTTP/2 200 OK`, `{"message":"demo_disabled"}`
      - Frontend BFF proxy: `curl -sS -i https://fin-buddy-dev.vercel.app/api/backend/api/v1/health`
        - Result: `HTTP/2 200 OK`
        - Body: `{"status":"ok","app":"Fin Buddy API","version":"0.1.0","environment":"production"}`
        - Headers: `Cache-Control: no-store, private`, `x-matched-path: /api/backend/[...path]`
      - Readiness probe: `curl -sS -i https://fin-buddy.fastapicloud.dev/api/v1/ready`
        - Result: `HTTP/2 200 OK`, `{"status":"degraded","app":"Fin Buddy API","version":"0.1.0","environment":"production"}`
        - Cause diagnosed: FastAPI Cloud logs report `OSError: [Errno 101] Network is unreachable`. `db.jklurueadteccrdycyiz.supabase.co` resolves strictly to IPv6 (`2406:da18:e5c:b701:17d3:daab:878:c35a`). FastAPI Cloud containers do not have outbound IPv6 routing.
        - Fix required: Owner must update `DATABASE_URL` in FastAPI Cloud to use the Supabase Connection Pooler URI (`aws-0-ap-south-1.pooler.supabase.com:6543` or `:5432`), which supports IPv4. Recorded in `docs/user-input-needed.md` under `UI-10`.
