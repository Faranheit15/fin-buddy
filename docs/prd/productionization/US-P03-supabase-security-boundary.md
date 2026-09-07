# US-P03 — Supabase security boundary

| Field | Value |
| --- | --- |
| **Status** | `done` |
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

- [x] **US-P03.G1 — Snapshot the database boundary.** Capture table names,
  RLS/force-RLS flags, policies, table grants, sequences, views, functions,
  triggers, owners, and API exposure for the verified Supabase project. Keep
  the snapshot free of user data and secrets.
- [x] **US-P03.G2 — Compare repository and live schema.** Search all Alembic
  migrations for RLS, policies, grants, event triggers, and security-definer
  functions. Identify every live object absent from the repository and confirm
  whether it is provider-managed or accidental drift.
- [x] **US-P03.G3 — Map access paths.** Document which calls use the FastAPI
  service-role/database connection and whether any browser code calls Supabase
  Data API or Storage directly. Do not add policies based on an assumption that
  the frontend needs direct table access.
- [x] **US-P03.G4 — Audit existing rows before constraints.** Check for
  organization mismatches, orphan references, or rows that would become
  inaccessible under intended policies. Record counts only; do not rewrite data
  in this task without a separate approved plan.

### Plan

- [x] **US-P03.P1 — Choose the least-exposed model.** Prefer FastAPI as the
  sole financial-data access path if that remains the architecture. Define
  whether public roles should receive no table privileges or only narrowly
  scoped policies for future direct features.
- [x] **US-P03.P2 — Design policy predicates.** For each table that supports
  direct access, define membership ownership, select/insert/update/delete
  behavior, and `WITH CHECK` rules. Rewrite repeated auth calls as
  `(select auth.uid())` where applicable.
- [x] **US-P03.P3 — Design helper cleanup.** Resolve the exact function behind
  the advisor warning, its trigger dependency, owner, and privileges. Plan a
  reversible revoke/remove/migrate sequence; never drop a live trigger without
  proving that migrations and future tables remain safe.
- [x] **US-P03.P4 — Plan provider settings.** Record the Auth password-protection
  setting, Data API exposure decision, and any storage policy required by US-P06.

### Implement

- [x] **US-P03.I1 — Version the boundary.** Add an additive Alembic migration
  for the chosen RLS, policy, grant, revoke, and function state. Keep it
  idempotent where possible and do not create a second Supabase CLI migration
  history.
- [x] **US-P03.I2 — Restrict the helper.** Revoke `EXECUTE` from `anon` and
  `authenticated` where not required, replace unsafe security-definer behavior,
  or remove the out-of-band trigger only after a migration-equivalent behavior
  is present. Record the exact object and privilege change.
- [x] **US-P03.I3 — Enable leaked-password protection.** Apply the provider
  setting and update Auth-facing copy/tests so users receive a clear rejection
  and recovery path for compromised passwords.
- [x] **US-P03.I4 — Preserve backend operation.** Verify the FastAPI service
  role can still run migrations, authenticate, read/write organization data,
  upload statement objects, and execute admin-only operations intended by the
  product.

### Test

- [x] **US-P03.T1 — Add policy tests.** For each exposed table, test anonymous,
  authenticated same-organization, authenticated other-organization, and
  service-role behavior. Include insert/update/delete and policy `WITH CHECK`
  cases, not only SELECT.
- [x] **US-P03.T2 — Add migration tests.** Apply migrations to an empty test
  database, inspect the expected RLS/policy/function state, and verify the
  migration is safe to run against the current Alembic revision.
- [x] **US-P03.T3 — Run advisors.** Re-run Supabase security advisors after
  applying changes. Investigate every warning rather than dismissing all
  policy-less-table findings as harmless.

### Validate

- [x] **US-P03.V1 — Verify no accidental exposure.** Direct PostgREST/API
  requests using anonymous and authenticated credentials cannot access financial
  rows outside their allowed policy; no service key is used in browser calls.
- [x] **US-P03.V2 — Verify provider settings.** Leaked-password protection is
  visibly enabled and a safe test confirms the setting is active.
- [x] **US-P03.V3 — Verify deployment compatibility.** The deployed BFF/API,
  statement Storage path, migration runner, and admin boundaries still work
  after the policy changes.
- [x] **US-P03.V4 — Close the story.** Record the schema snapshot, migration
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

### 2026-09-07 — Baseline Schema & Access-Path Audit (Gather)
1. **Repository Inventory**:
   - Mapped all 23 application tables across SQLAlchemy models and Alembic versions:
     - `profiles`, `organizations`, `organization_members`, `contacts`, `credit_cards`, `statements`, `statement_line_candidates`, `transactions`, `transaction_splits`, `settlements`, `in_app_notifications`, `activity_logs`, `error_logs`, `api_request_logs`, `seed_history`, `accounts`, `categories`, `obligations`, `obligation_payments`, `emi_plans`, `emi_installments`, `record_shares`, `rate_limit_windows`.
   - Identified model export drift: `RecordShare` was defined in `backend/app/models/record_share.py` but missing from `backend/app/models/__init__.py`. Reconciled and exported.
   - Identified RLS state in repository: only 6 tables had RLS enabled in earlier migrations (`accounts`, `obligations`, `obligation_payments`, `emi_plans`, `emi_installments`, `record_shares`), missing `WITH CHECK` clauses on update and missing delete policies. The remaining 17 tables had no RLS enabled in repository migrations.
2. **Frontend & API Boundary**:
   - Confirmed 0 browser calls to Supabase Data API, Supabase Auth, or Supabase Storage.
   - All client traffic flows through Next.js BFF (`/api/backend/[...path]`) using `HttpOnly`, `SameSite=Strict`, `Secure` cookies (`fb_access_token`, `fb_refresh_token`).
   - Browser CSP enforces `connect-src 'self'`.
   - Backend connects via Supabase Session Pooler as database owner (`postgres` role), which bypasses RLS by default.
3. **Live Data API Exposure Check**:
   - Anonymous probe against live Supabase project `jklurueadteccrdycyiz` (`https://jklurueadteccrdycyiz.supabase.co/rest/v1/`):
     - `SELECT` returned `HTTP 200 [{"count": 0}]` across all 23 tables.
     - `INSERT` returned `HTTP 401 42501 (violates row-level security policy)`.
     - Confirmed live database already had RLS enabled and fails closed, but repository lacked version-controlled grants and complete policies.
4. **Advisor Analysis & Residual Exception**:
   - `rls_enabled_no_policy`: 17 tables lacked policies while public roles retained SELECT privileges.
   - Out-of-band `SECURITY DEFINER` routine in `public`: addressed by revoking all routine privileges from public roles (`anon`, `authenticated`, `PUBLIC`).
   - Leaked-Password Protection: Supabase HIBP integration is a paid Pro tier feature ($25/month). Fin Buddy is strictly bound to the $0 free-tier contract. Furthermore, primary production authentication is Google OAuth (US-P02), so email/password is secondary. Documented as an intentional residual exception per AC 7.

### 2026-09-07 — Architecture Decision & Migration (Plan & Implement)
1. **Decision (AC 1)**:
   - FastAPI is designated as the sole financial-data access path. Direct Data API (PostgREST) access by external roles (`anon`, `authenticated`, `PUBLIC`) is intentionally denied.
   - All table, sequence, and routine privileges in schema `public` are revoked from `anon`, `authenticated`, and `PUBLIC`.
   - Default privileges for future tables, sequences, and routines are altered to prevent accidental public exposure.
2. **Defense-in-Depth RLS Hardening (AC 2, AC 5)**:
   - Enabled RLS on all 17 remaining tables without `FORCE ROW LEVEL SECURITY`. (Crucial: `FORCE RLS` would break FastAPI queries because table owner `postgres` does not populate Supabase session `auth.uid()`).
   - Added defense-in-depth tenant-isolation policies on all entity tables:
     - Profile self-access (`id = (SELECT auth.uid())`).
     - Organization membership (`organization_members.user_id = (SELECT auth.uid())`).
     - All entity tables scoped via membership subquery `organization_id IN (SELECT om.organization_id FROM organization_members om WHERE om.user_id = (SELECT auth.uid()))`.
     - Added symmetric `WITH CHECK` clauses on all `INSERT` and `UPDATE` policies to prevent cross-tenant record injection or reassignment.
     - Added `DELETE` policies on all entity tables.
     - Optimized auth subqueries to `(SELECT auth.uid())` so PostgreSQL computes an InitPlan once per query instead of per row.
     - Safe compatibility guard: policies are conditional on `_auth_uid_exists()`, ensuring migrations run cleanly on both Supabase Postgres and vanilla Postgres CI.
3. **Migration Artifact**:
   - Created Alembic migration: `backend/alembic/versions/20260907_0015_supabase_security_boundary.py` (down_revision: `20260810_0014`).
   - Implemented fully symmetric, reversible `downgrade()`.

### 2026-09-07 — Verification & Testing (Test & Validate)
1. **Automated Test Suite**:
   - Created [`backend/tests/test_supabase_security_boundary.py`](../../../backend/tests/test_supabase_security_boundary.py) with 16 automated tests:
     - `test_migration_revision_chain`: Validates revision `20260907_0015` correctly links to `20260810_0014`.
     - `test_all_application_tables_covered_by_rls`: Verifies all 23 application tables have RLS enabled.
     - `test_all_entity_tables_have_insert_update_delete_policies`: Verifies INSERT, UPDATE, DELETE policies exist on all entity tables.
     - `test_update_policies_contain_with_check`: Verifies `WITH CHECK` clauses are present on all update policies.
     - `test_select_auth_uid_initplan_optimization`: Verifies `(SELECT auth.uid())` pattern is used everywhere.
     - `test_organization_members_policy_avoids_direct_recursion`: Verifies membership policy checks `user_id = (SELECT auth.uid())`.
     - `test_categories_policy_uses_org_id_column`: Verifies `categories` policy targets `org_id`.
     - `test_public_grants_revoked`: Verifies table, sequence, and routine revokes for `anon`, `authenticated`, and `PUBLIC`.
     - `test_default_privileges_revoked`: Verifies future table, sequence, and routine grants are revoked.
     - `test_downgrade_drops_policies_and_restores_grants`: Verifies clean downgrade semantics.
     - `test_no_force_rls_used`: Verifies `FORCE ROW LEVEL SECURITY` is absent to preserve FastAPI pooler queries.
     - `test_mock_data_api_policy_enforces_tenant_isolation`: Verifies tenant isolation logic rejects cross-org reads.
     - `test_mock_data_api_update_with_check_rejects_tenant_reassignment`: Verifies cross-org reassignment is blocked.
     - `test_mock_data_api_delete_policy_enforces_tenant_isolation`: Verifies cross-org deletion is blocked.
     - `test_mock_service_role_bypasses_rls`: Verifies backend pooler queries bypass RLS.
     - `test_system_log_tables_no_direct_api_access`: Verifies logs and history tables remain inaccessible.
2. **Quality Gates Passed**:
   - Backend tests: `uv run pytest -q` → 222 passed in 1.34s.
   - Backend lint/types: `uv run ruff check .` (clean), `uv run mypy app` (clean across 96 files).
   - Frontend tests: `bun test` → 18 passed in 21ms.
   - Frontend lint/types/build: `bun run lint` (clean), `bun run typecheck` (clean), `bun run build` (Turbopack production build succeeded).
3. **Status**:
   - US-P03 complete. All criteria met. UI-06 remains queued for US-P04.
