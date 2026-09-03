# US-P03 — Supabase security boundary

| Field | Value |
| --- | --- |
| **Status** | `todo` |
| **Sequence** | 3 |
| **Depends on** | [US-P01](US-P01-production-release-gate.md) |
| **One-loop objective** | Make Supabase RLS, grants, Auth security, and security-definer functions intentional, reproducible, and testable. |
| **Primary boundaries** | Supabase Postgres, Alembic migrations, Auth settings, Data API roles |

## User story

**As** a Fin Buddy owner
**I want** the database to fail closed even if an API path is introduced or misconfigured
**So that** financial data is protected by a documented second boundary rather than application checks alone.

## Why this matters

The active Supabase project has RLS enabled on application tables, but many have
no policies while `anon` and `authenticated` retain table grants. Advisors also
flag an out-of-band `SECURITY DEFINER` RLS helper executable by public roles and
disabled leaked-password protection. The current FastAPI service-role path may
be intentional, but the boundary is not reproducible from the repository.

## Scope and non-goals

In scope: schema/security inventory, RLS/policy/grant source of truth,
security-definer review, Auth password protection, direct Data API tests, and
safe migration. Out of scope: tenant-reference constraints and role capability
design, which are US-P04.

## Touchpoints

- [`backend/alembic/versions/`](../../../backend/alembic/versions)
- [`backend/app/db/`](../../../backend/app/db)
- [`backend/app/core/security.py`](../../../backend/app/core/security.py)
- [`docs/GOTCHAS.md`](../../GOTCHAS.md)
- Supabase Database Advisors, Auth settings, SQL editor, and API roles

## Acceptance criteria

1. Every public table has an explicit documented access decision: direct Data
   API allowed with a tested policy, or direct access intentionally denied.
2. RLS, policies, grants, and security-definer functions required by the app are
   represented in version-controlled Alembic migrations or explicitly marked
   as provider-managed with evidence.
3. The out-of-band RLS helper is either removed safely or restricted to the
   minimum role/functionality, and public execution is not left enabled by
   accident.
4. Anonymous and authenticated Data API tests cannot read or mutate another
   organization; the FastAPI service-role path continues to work.
5. Update policies include appropriate `WITH CHECK` protection, and any use of
   `FORCE ROW LEVEL SECURITY` is proven compatible with the actual database role.
6. Leaked-password protection is enabled and its behavior is recorded.
7. Supabase security advisors are clean or every remaining warning has a
   written, intentional exception and follow-up owner.

## Tasks

### Gather

- [ ] **US-P03.G1 — Snapshot the database boundary.** Capture table names,
  RLS/force-RLS flags, policies, table grants, sequences, views, functions,
  triggers, owners, and API exposure for the verified Supabase project. Keep
  the snapshot free of user data and secrets.
- [ ] **US-P03.G2 — Compare repository and live schema.** Search all Alembic
  migrations for RLS, policies, grants, event triggers, and security-definer
  functions. Identify every live object absent from the repository and confirm
  whether it is provider-managed or accidental drift.
- [ ] **US-P03.G3 — Map access paths.** Document which calls use the FastAPI
  service-role/database connection and whether any browser code calls Supabase
  Data API or Storage directly. Do not add policies based on an assumption that
  the frontend needs direct table access.
- [ ] **US-P03.G4 — Audit existing rows before constraints.** Check for
  organization mismatches, orphan references, or rows that would become
  inaccessible under intended policies. Record counts only; do not rewrite data
  in this task without a separate approved plan.

### Plan

- [ ] **US-P03.P1 — Choose the least-exposed model.** Prefer FastAPI as the
  sole financial-data access path if that remains the architecture. Define
  whether public roles should receive no table privileges or only narrowly
  scoped policies for future direct features.
- [ ] **US-P03.P2 — Design policy predicates.** For each table that supports
  direct access, define membership ownership, select/insert/update/delete
  behavior, and `WITH CHECK` rules. Rewrite repeated auth calls as
  `(select auth.uid())` where applicable.
- [ ] **US-P03.P3 — Design helper cleanup.** Resolve the exact function behind
  the advisor warning, its trigger dependency, owner, and privileges. Plan a
  reversible revoke/remove/migrate sequence; never drop a live trigger without
  proving that migrations and future tables remain safe.
- [ ] **US-P03.P4 — Plan provider settings.** Record the Auth password-protection
  setting, Data API exposure decision, and any storage policy required by US-P06.

### Implement

- [ ] **US-P03.I1 — Version the boundary.** Add an additive Alembic migration
  for the chosen RLS, policy, grant, revoke, and function state. Keep it
  idempotent where possible and do not create a second Supabase CLI migration
  history.
- [ ] **US-P03.I2 — Restrict the helper.** Revoke `EXECUTE` from `anon` and
  `authenticated` where not required, replace unsafe security-definer behavior,
  or remove the out-of-band trigger only after a migration-equivalent behavior
  is present. Record the exact object and privilege change.
- [ ] **US-P03.I3 — Enable leaked-password protection.** Apply the provider
  setting and update Auth-facing copy/tests so users receive a clear rejection
  and recovery path for compromised passwords.
- [ ] **US-P03.I4 — Preserve backend operation.** Verify the FastAPI service
  role can still run migrations, authenticate, read/write organization data,
  upload statement objects, and execute admin-only operations intended by the
  product.

### Test

- [ ] **US-P03.T1 — Add policy tests.** For each exposed table, test anonymous,
  authenticated same-organization, authenticated other-organization, and
  service-role behavior. Include insert/update/delete and policy `WITH CHECK`
  cases, not only SELECT.
- [ ] **US-P03.T2 — Add migration tests.** Apply migrations to an empty test
  database, inspect the expected RLS/policy/function state, and verify the
  migration is safe to run against the current Alembic revision.
- [ ] **US-P03.T3 — Run advisors.** Re-run Supabase security advisors after
  applying changes. Investigate every warning rather than dismissing all
  policy-less-table findings as harmless.

### Validate

- [ ] **US-P03.V1 — Verify no accidental exposure.** Direct PostgREST/API
  requests using anonymous and authenticated credentials cannot access financial
  rows outside their allowed policy; no service key is used in browser calls.
- [ ] **US-P03.V2 — Verify provider settings.** Leaked-password protection is
  visibly enabled and a safe test confirms the setting is active.
- [ ] **US-P03.V3 — Verify deployment compatibility.** The deployed BFF/API,
  statement Storage path, migration runner, and admin boundaries still work
  after the policy changes.
- [ ] **US-P03.V4 — Close the story.** Record the schema snapshot, migration
  revision, exact helper decision, advisor results, and residual exceptions in
  this file and [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- RLS/policy/grant/function inventory before and after.
- Access-path decision and direct Data API test matrix.
- Alembic revision and migration test output.
- Exact security-definer helper remediation.
- Auth password-protection confirmation and advisor results.

## Safety notes

Do not enable permissive policies just to silence an advisor. Do not enable
`FORCE ROW LEVEL SECURITY` until the actual database owner/service role behavior
has been tested. Take a safe schema/data snapshot before privileges or policies
change.

## Story notes

_(Append dated implementation decisions and evidence here.)_
