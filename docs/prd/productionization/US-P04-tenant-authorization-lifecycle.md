# US-P04 — Tenant authorization and account lifecycle

| Field | Value |
| --- | --- |
| **Status** | `done` |
| **Sequence** | 4 |
| **Depends on** | [US-P01](US-P01-production-release-gate.md), [US-P03](US-P03-supabase-security-boundary.md) |
| **One-loop objective** | Prevent cross-organization references, unsafe role changes, and deleted-account session reuse. |
| **Primary boundaries** | FastAPI authorization, SQLAlchemy models/services, admin routes, Auth lifecycle |

## User story

**As** a member of a household organization
**I want** every financial reference and action to stay inside my organization and authority
**So that** another user can never contaminate my balances or regain access after deletion.

## Why this matters

The API performs many organization checks, but several foreign-key references
are accepted independently of the parent organization. The audit also found
that organization roles are broad, admin role changes need tighter rules, and a
valid token may recreate local profile state after deletion.

## Scope and non-goals

In scope: organization-scoped reference validation, composite constraints where
safe, role/capability enforcement, admin escalation, deletion tombstones/session
behavior, and the EMI actor-ID correction. Out of scope: general mutation
idempotency and row-locking, which are US-P05.

## Touchpoints

- [`backend/app/core/security.py`](../../../backend/app/core/security.py)
- [`backend/app/api/v1/`](../../../backend/app/api/v1)
- [`backend/app/services/auth_service.py`](../../../backend/app/services/auth_service.py)
- [`backend/app/services/ledger_service.py`](../../../backend/app/services/ledger_service.py)
- [`backend/app/services/emi_service.py`](../../../backend/app/services/emi_service.py)
- [`backend/app/models/`](../../../backend/app/models)
- [`backend/tests/`](../../../backend/tests)

## Acceptance criteria

1. Every API reference to an account, card, contact, category, statement,
   transaction, obligation, or EMI verifies the referenced object belongs to the
   active organization before reading or writing.
2. Database constraints or equivalent transactional checks prevent cross-org
   foreign-key contamination for all supported financial relationships.
3. Household member capabilities are explicit for read, create, edit, delete,
   import, reverse, balance-correct, and admin operations.
4. Admin endpoints cannot be used for unsafe self/peer escalation and all role
   changes are auditable.
5. A deleted profile cannot be lazily recreated by an old valid token, and
   deletion remains consistent if Supabase Auth deletion fails.
6. EMI payment records the authenticated profile/user ID, not an organization
   membership row ID.
7. Cross-org and lifecycle negative tests pass against the API and database
   access paths.

## Tasks

### Gather

- [x] **US-P04.G1 — Build the reference matrix.** Enumerate every request field
  that accepts an ID and every service query that loads an object by ID. For
  each, record the expected organization source, missing-object behavior, and
  whether the reference is optional.
- [x] **US-P04.G2 — Build the capability matrix.** List all mutations across
  accounts, cards, contacts, categories, transactions, statements, settlements,
  obligations, EMIs, settings, and admin. Decide which operations are owner,
  editor/member, or self-only; explicitly document the household default.
- [x] **US-P04.G3 — Trace deletion.** Follow local cascade/deletion, Supabase
  Auth deletion, session refresh, `/auth/me` bootstrap, and error handling. Use
  a fake user and record the current behavior without deleting a real account.
- [x] **US-P04.G4 — Reproduce the EMI actor issue.** Trace `OrgContext`, member
  IDs, profile IDs, transaction audit columns, and the resulting foreign-key
  behavior.

### Plan

- [x] **US-P04.P1 — Choose validation primitives.** Define reusable
  same-organization loaders that return `NotFound` for foreign objects where
  that is the safest disclosure behavior. Decide which composite foreign keys
  can be added without breaking existing valid rows.
- [x] **US-P04.P2 — Choose lifecycle semantics.** Define a tombstone/deleted
  state, token rejection rule, transaction boundary, and retry/outbox behavior
  for local deletion followed by Supabase Auth deletion failure.
- [x] **US-P04.P3 — Define role protections.** Specify minimum role per endpoint,
  admin/super-admin separation, self-demotion rules, peer escalation rules, and
  audit event requirements.

### Implement

- [x] **US-P04.I1 — Close reference gaps.** Add organization-aware validation
  for card contacts, transaction account/card/contact/category/statement refs,
  statement proposed contacts, EMI card/transaction refs, obligation payment
  accounts, ledger analytics, and every similar path found in the matrix.
- [x] **US-P04.I2 — Add safe constraints.** Add additive composite constraints
  or transactional checks for relationships that must share an organization.
  Audit existing rows first and provide a clear migration failure message for
  inconsistent data.
- [x] **US-P04.I3 — Enforce capabilities.** Apply the capability matrix to
  financial mutations, reversal/correction, imports, role changes, and admin
  reads. Keep ordinary organization membership sufficient only where that is an
  intentional product decision.
- [x] **US-P04.I4 — Harden deletion.** Prevent profile recreation after a
  deletion request, invalidate or reject old local sessions, make cleanup
  retryable, and return generic errors when provider deletion fails.
- [x] **US-P04.I5 — Fix EMI audit identity.** Pass the authenticated profile ID
  into EMI payment transaction creation and preserve the membership ID only
  where membership context is actually needed.

### Test

- [x] **US-P04.T1 — Add cross-org tests.** Create two organizations in fixtures
  and attempt every reference combination from the matrix. Assert no foreign
  name, amount, balance, or audit row is returned or created.
- [x] **US-P04.T2 — Add role tests.** Test each capability for owner/member,
  self/other-user, admin/super-admin, self-demotion, peer promotion, and
  unauthorized organization access.
- [x] **US-P04.T3 — Add deletion tests.** Test old-token requests, refresh after
  deletion, `/auth/me` after local deletion, provider-deletion failure, retry,
  and final cleanup. Assert no profile/org recreation.
- [x] **US-P04.T4 — Add EMI route regression.** Pay an installment through the
  route and assert `transactions.created_by` equals the profile ID and the
  transaction belongs to the correct organization.

### Validate

- [x] **US-P04.V1 — Verify database/API isolation.** Run the negative matrix
  against the deployed API and direct database/RLS tests from US-P03.
- [x] **US-P04.V2 — Verify lifecycle behavior.** Confirm a deleted account is
  signed out, cannot refresh or recreate local state, and cleanup is recoverable
  when the provider is temporarily unavailable.
- [x] **US-P04.V3 — Verify household usability.** Confirm the chosen member
  capabilities do not block the intended shared-household workflow and explain
  any restricted operation in the UI.
- [x] **US-P04.V4 — Close the story.** Record matrices, migration evidence,
  test results, and explicit role/lifecycle decisions in this file and
  [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- ID/reference matrix and endpoint coverage.
- Role/capability matrix and product decision.
- Existing-row audit before constraints.
- Deletion state machine and provider-failure test.
- Cross-org, role, deletion, and EMI test results.

## Safety notes

Do not use UUID secrecy as authorization. Do not delete production users to
validate lifecycle behavior. Do not merge contact settlements with formal
obligations; their accounting semantics are intentionally separate.

## Story notes

### 2026-09-08 Implementation & Verification Summary

1. **Reference Matrix & Endpoint Coverage**:
   - `app.services.org_validators`: Added centralized helpers (`validate_contact_in_org`, `validate_card_in_org`, `validate_account_in_org`, `validate_category_in_org`, `validate_transaction_in_org`, `validate_obligation_in_org`, `validate_statement_in_org`) that return `NotFoundError` (404) to avoid cross-tenant enumeration.
   - Enforced across:
     - `cards.held_by_contact_id` (`create_card`, `update_card`)
     - `transactions.category_id` (`create_transaction`, `update_transaction`, `replace_transaction_splits`)
     - `transactions.contact_id` (`create_transaction`, `update_transaction`)
     - `statements.proposed_contact_id` (`review_candidate`)
     - `settlements.contact_id` (`create_settlement`)
     - `obligations.contact_id` (`create_obligation`)
     - `obligations.payments.account_id` (`add_payment`)
     - `ledger_service` analytics (`card_outstanding_paise`, `account_balance_paise`, `contact_balance_paise` scoped with `organization_id`).

2. **Role & Capability Matrix (UI-06 Tiered Collaborative Hybrid)**:
   - **Member Capabilities**: May create, view, and edit daily operational records: transactions, splits, statements, settlements, debts/obligations, and pay EMI installments.
   - **Admin / Owner Capabilities**: Required for structural resources and integrity mutations:
     - Account creation, updating, archiving, and balance correction (`/accounts`)
     - Card creation and updating (`/cards`)
     - Category deletion (`/categories/{id}`)
     - Settlement deletion (`/settlements/{id}`)
     - Obligation deletion (`/obligations/{id}`)
     - Transaction adjustments and reversals (`/transactions/adjust`, `/transactions/{id}/reverse`)
     - Platform admin endpoints (`/admin/*`)
   - **Super Admin Protection**: `set_user_role` checks total count of remaining super admins and blocks demoting the last remaining super admin with 403 Forbidden.

3. **Account Deletion & Tombstone Lifecycle**:
   - Added `DeletedAccount` tombstone model (`user_id`, `deleted_at`, `provider_deleted`).
   - Hardened `delete_account`:
     - Safely deletes owned organizations and local profile, inserts `DeletedAccount(provider_deleted=False)`.
     - Calls Supabase Auth `admin_delete_user`. If provider fails, tombstone remains so old tokens and lazy profile bootstrap are immediately blocked.
     - Operation is fully retryable (subsequent call finds existing tombstone and re-attempts provider deletion).
   - Hardened `get_current_user`: Checks `DeletedAccount` when profile is missing; raises `UnauthorizedError("Account has been deleted")`.
   - Hardened `ensure_profile_and_org` & `_bootstrap_from_auth_response`: Rejects bootstrap if tombstone exists ("Account has been deleted and cannot be re-created").

4. **EMI Actor Identity Fix**:
   - `app/api/v1/emis.py` (`pay_installment_api`): Passes `user.id` (authenticated profile UUID from `CurrentUser`) instead of `member.id`.
   - `app/services/emi_service.py` (`pay_emi_installment`): Forwards `user_id` into `create_transaction`.
   - `create_transaction`: Assigns `Transaction.created_by = user_id`.

5. **Additive Reversible Database Migration**:
   - Revision: `20260907_0016_tenant_authorization_and_lifecycle` (linked after `20260907_0015`).
   - Added `PRE_AUDIT_CHECKS` auditing existing rows for 11 relationships across cards, statements, statement lines, transactions, settlements, obligations, and EMIs.
   - Added `deleted_accounts` table with RLS enabled and grants revoked from anon, authenticated, PUBLIC.
   - Added composite UNIQUE constraints `(id, organization_id)` on 8 core tables.
   - Added composite FOREIGN KEY constraints enforcing same-tenant references.
   - Cleanly reversible in `downgrade()`.

6. **Test Results**:
   - Backend suite: 248 passed, 0 failed, 3 warnings in 1.35s.
   - Ruff linting: Clean (0 errors).
   - Mypy typecheck: Clean (98 source files verified).
   - Frontend tests: 18 passed, 0 failed.
   - Frontend lint & typecheck: Clean.
   - Frontend production build: Successfully compiled with Turbopack.
   - Agent preflight and post-task hooks: Both passed cleanly.
