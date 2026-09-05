# US-P01 — Production release gate

| Field | Value |
| --- | --- |
| **Status** | `todo` |
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

- [ ] **US-P01.G1 — Identify the release surface.** Record the Vercel project,
  current deployment commit, frontend aliases, FastAPI app URL, Supabase project
  ref, database region, and current git branch. Decide whether
  `fin-buddy-dev.vercel.app` is production or staging; do not silently treat a
  `-dev` hostname as production.
- [ ] **US-P01.G2 — Capture the unsafe baseline.** Save the current responses
  for `/api/v1/health`, `/api/v1/ready`, `/api/v1/auth/demo-available`,
  `/docs`, `/openapi.json`, and the frontend BFF health path. Record status
  codes, environment, cache headers, and request IDs without copying secrets.
- [ ] **US-P01.G3 — Verify the data target.** Inspect the Supabase project
  status, `alembic_version`, row counts for product tables, private statement
  bucket, and storage object count. Confirm that an apparently empty product
  database is intentional before applying any schema or seed action.
- [ ] **US-P01.G4 — Inventory configuration.** Compare the env examples,
  Pydantic settings, FastAPI Cloud settings, Vercel settings, and deployment
  documentation. List every required secret and classify it as backend-only,
  server-only, or public. Confirm that no service-role key is required in
  Vercel.
- [ ] **US-P01.G5 — Capture the zero-cost baseline.** Confirm the Vercel
  project is Hobby, FastAPI Cloud is Hobby, Supabase is Free, no paid add-ons
  or custom domain are enabled, and record approximate database/storage/egress
  and function usage. Treat all values as time-sensitive provider facts.

### Plan

- [ ] **US-P01.P1 — Write the environment matrix.** Define the values and
  allowed behavior for local, test, staging if retained, and production. The
  production row must explicitly set `ENVIRONMENT=production`, `DEBUG=false`,
  `DEMO_AUTH_ENABLED=false`, `AUTO_MIGRATE=false`, `AUTO_SEED=false`,
  `STATEMENT_STORAGE_BACKEND=supabase`, the private bucket, exact frontend URL,
  and a real JWT/job secret.
- [ ] **US-P01.P2 — Define the migration gate.** Document who applies
  `alembic upgrade head`, against which verified target, from which commit, and
  how the pre/post revision and balance checks are recorded. Keep Alembic as
  the schema source of truth; do not introduce a second migration history.
- [ ] **US-P01.P3 — Define rollback and smoke gates.** Specify the safe response
  if the deployment is unhealthy, migration verification fails, statement
  storage is local, or demo/docs remain exposed. Include the exact URLs and
  expected status/body properties for post-deploy verification.
- [ ] **US-P01.P4 — Define the budget stop rule.** Set a conservative quota
  threshold at which optional keepalive, analytics, reminder, email, and other
  non-essential jobs are disabled. Do not solve quota pressure by upgrading a
  plan or adding a paid provider.

### Implement

- [ ] **US-P01.I1 — Make production configuration fail closed.** Add or adjust
  validation so production cannot start with a fallback JWT secret, debug mode,
  demo auth, auto-seeding, missing database settings, or local statement
  storage. Keep local/test defaults usable and do not log secret values.
- [ ] **US-P01.I2 — Apply the environment contract.** Configure the verified
  FastAPI Cloud deployment and Vercel project with the matrix values. Keep
  `BACKEND_URL` server-only and keep all Supabase service credentials backend
  only. If account access is unavailable, record the exact missing credential
  rather than substituting a local value.
- [ ] **US-P01.I3 — Apply and record the migration gate.** After a read-only
  revision/data check, run the repository's Alembic head once against the
  intended project. Record the before/after revision and confirm no seed data or
  destructive reset was used.
- [ ] **US-P01.I4 — Align the runbook.** Update [`docs/DEPLOY.md`](../../DEPLOY.md)
  with the final environment matrix, hostname decision, migration evidence,
  secret placement, release smoke commands, and rollback steps. Keep historical
  audit documents unchanged; link this story as the current gate.

### Test

- [ ] **US-P01.T1 — Test configuration guards.** Add tests for production
  startup with missing/weak secrets, demo enabled, debug enabled, local storage,
  auto-migrate, and auto-seed. Add tests proving local/test behavior is not
  accidentally disabled.
- [ ] **US-P01.T2 — Test the release contract locally.** Run the backend test,
  Ruff, and mypy gates; run frontend lint, typecheck, and build; run
  `docker compose config --quiet`. Use the native Linux toolchain and record
  unavailable tools honestly.
- [ ] **US-P01.T3 — Smoke the deployed surface.** Verify health, readiness,
  BFF proxying, CORS, docs/demo denial, storage configuration, and migration
  revision. Check that error responses do not disclose secret values or stack
  traces.

### Validate

- [ ] **US-P01.V1 — Verify production identity.** The public health response,
  deployment metadata, and release notes agree on the environment and commit.
- [ ] **US-P01.V2 — Verify the security gates.** Demo login is unavailable,
  docs are disabled, required secrets are present, the BFF remains functional,
  and no frontend bundle contains a service-role key.
- [ ] **US-P01.V3 — Verify data durability.** Create no user data, but prove by
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

_(Append dated implementation decisions and evidence here.)_
