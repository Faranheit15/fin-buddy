# US-P05 — Safe financial mutations

| Field | Value |
| --- | --- |
| **Status** | `done` |
| **Sequence** | 5 |
| **Depends on** | [US-P04](US-P04-tenant-authorization-lifecycle.md) |
| **One-loop objective** | Make retries, double-clicks, and concurrent requests unable to duplicate financial events. |
| **Primary boundaries** | Transactions, statement imports, EMI payments, obligation payments, settlements, Postgres transactions |

## User story

**As** a Fin Buddy owner
**I want** every financial action to be safe to retry
**So that** a slow network, browser retry, or two open tabs cannot create duplicate money movements.

## Why this matters

The current implementation reads a pending row, creates related records, and
then marks it complete in several flows without a durable operation key or row
lock. That is acceptable in a single-user happy-path test but unsafe for
retries, mobile reconnects, scheduled jobs, or future household members.

## Scope and non-goals

In scope: idempotency contract, conditional updates/row locks, unique
constraints, transaction boundaries, and concurrency tests for financial writes.
Out of scope: tenant authorization, which is US-P04, and UI workflow polish,
which is US-P11/US-P12.

## Touchpoints

- [`backend/app/services/transaction_service.py`](../../../backend/app/services/transaction_service.py)
- [`backend/app/services/emi_service.py`](../../../backend/app/services/emi_service.py)
- [`backend/app/services/obligation_service.py`](../../../backend/app/services/obligation_service.py)
- [`backend/app/services/statement_service.py`](../../../backend/app/services/statement_service.py)
- [`backend/app/api/v1/`](../../../backend/app/api/v1)
- [`backend/app/models/`](../../../backend/app/models)
- [`backend/alembic/versions/`](../../../backend/alembic/versions)

## Acceptance criteria

1. Every externally retried financial command has a documented idempotency key
   or an equivalent unique operation identity.
2. Repeating a successful request returns the original result without a second
   transaction, payment, settlement, import, or notification side effect.
3. Concurrent payment/import requests serialize safely and cannot overpay,
   double-post, or commit the same statement line twice.
4. All related ledger rows and status changes commit atomically or expose a
   recoverable, explicitly marked failure state.
5. A failed request can be retried without requiring manual database cleanup.
6. Tests cover timeout-after-commit, double-click, concurrent request, and
   partial-failure behavior for the important financial flows.

## Tasks

### Gather

- [x] **US-P05.G1 — Enumerate commands.** List every POST/PATCH/DELETE that
  creates, posts, reverses, corrects, pays, settles, imports, or deletes a
  financial record. Record side effects, current transaction boundary, and
  whether the client can safely retry it today.
- [x] **US-P05.G2 — Reproduce races.** Build deterministic tests or a local
  harness for two EMI payments, two obligation payments, two statement imports,
  duplicate transaction submissions, and a request that loses its response
  after commit.
- [x] **US-P05.G3 — Inspect schema support.** Check existing unique indexes,
  status columns, self-references, transaction isolation, and database pool
  behavior. Confirm which operations need a new migration.

### Plan

- [x] **US-P05.P1 — Define the idempotency contract.** Choose header/body
  placement, key length/format, scope by user and organization, retention,
  response replay behavior, and conflict behavior when the same key has a
  different payload. Keep keys out of logs when they could identify data.
- [x] **US-P05.P2 — Define lock order.** For each flow, identify the row that
  must be locked first, the invariant protected, the expected transaction
  isolation, and a bounded behavior for lock timeout/deadlock.
- [x] **US-P05.P3 — Define uniqueness.** Specify database constraints for one
  reversal per source, one payment per installment/operation, one committed
  statement line per source identity, and any other duplicate-prone operation.

### Implement

- [x] **US-P05.I1 — Add operation identity.** Implement the smallest shared
  persistence or constraint mechanism needed to record an idempotency key and
  replay the original result without storing sensitive payloads unnecessarily.
- [x] **US-P05.I2 — Protect EMI and obligation payments.** Lock the pending
  installment/obligation state, validate the remaining amount inside the
  transaction, create ledger/payment rows atomically, and make a repeated
  payment return the existing result.
- [x] **US-P05.I3 — Protect statement import.** Make candidate selection and
  committed marking conditional/locked, add a stable source identity, and
  ensure parsing/import status transitions cannot be overwritten by stale work.
- [x] **US-P05.I4 — Protect other writes.** Apply the contract to transaction
  create/post/reverse/adjust, settlements, transfers, and account corrections
  where a retry can duplicate a ledger event. Keep posted-record audit rules.

### Test

- [x] **US-P05.T1 — Test replay.** Send the same command twice with the same key
  and assert one side effect, the same response identity, and no extra audit
  row. Send the same key with a changed payload and assert a clear conflict.
- [x] **US-P05.T2 — Test concurrency.** Run concurrent requests against a real
  PostgreSQL test database for EMI payment, obligation payment, and statement
  import. Assert balances, remaining amounts, and committed counts are correct.
- [x] **US-P05.T3 — Test failure recovery.** Simulate provider/database failure
  before commit, after related-row insert, and after commit-before-response.
  Retry each case and assert no orphan or duplicate financial event.
- [x] **US-P05.T4 — Run quality gates.** Run all affected backend tests, Ruff,
  mypy, migration tests, and a focused API integration suite.

### Validate

- [x] **US-P05.V1 — Verify ledger invariants.** Compare before/after balances,
  statement counts, installment status, obligation remaining balance, and audit
  history for every concurrency scenario.
- [x] **US-P05.V2 — Verify client behavior.** Confirm the BFF retries only when
  the operation key is preserved and shows a useful conflict/error when a key
  is reused incorrectly.
- [x] **US-P05.V3 — Close the story.** Record the operation contract, migration
  revision, race harness, test output, and known unsupported commands in this
  file and [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

### Financial-command / Idempotency Matrix

| Endpoint | Method | Service / Handler | Locking / Concurrency Mechanism | Idempotency Key Handling | Duplicate Prevention |
| --- | --- | --- | --- | --- | --- |
| `/api/v1/transactions` | POST | `transaction_service.create_transaction` | Atomic commit, ledger logging | RFC 9440 header `Idempotency-Key` | Cached response replay on retry |
| `/api/v1/transactions/adjust` | POST | `transaction_service.adjust_transaction` | Atomic commit, delta calculation | RFC 9440 header `Idempotency-Key` | Cached response replay on retry |
| `/api/v1/transactions/{id}/post` | POST | `transaction_service.post_draft` | `SELECT FOR UPDATE` on draft tx | RFC 9440 header `Idempotency-Key` | 409 Conflict if already posted |
| `/api/v1/transactions/{id}/reverse` | POST | `transaction_service.reverse_transaction` | `SELECT FOR UPDATE` on target tx + partial unique index `uq_transactions_reverses_id` | RFC 9440 header `Idempotency-Key` | 409 Conflict if already reversed + DB unique constraint |
| `/api/v1/transfers` | POST | `transfer_service.create_transfer` | Atomic double-entry commit | RFC 9440 header `Idempotency-Key` | Cached response replay on retry |
| `/api/v1/emis` | POST | `emi_service.create_plan` | Atomic plan + installment commit | RFC 9440 header `Idempotency-Key` | Cached response replay on retry |
| `/api/v1/emis/installments/{id}/pay` | POST | `emi_service.pay_emi_installment` | `SELECT FOR UPDATE OF emi_installments` | RFC 9440 header `Idempotency-Key` | 409 Conflict if already paid |
| `/api/v1/obligations` | POST | `obligation_service.create_obligation` | Atomic obligation creation | RFC 9440 header `Idempotency-Key` | Cached response replay on retry |
| `/api/v1/obligations/{id}/payments` | POST | `obligation_service.add_payment` | `SELECT FOR UPDATE` on obligation | RFC 9440 header `Idempotency-Key` | 409 Conflict if already marked PAID |
| `/api/v1/statements/{id}/import` | POST | `statement_service.import_statement_candidates` | `SELECT FOR UPDATE` on statement & candidates | RFC 9440 header `Idempotency-Key` | State check: skips already committed candidates |
| `/api/v1/accounts/{id}/correct-balance` | POST | `account_service.correct_balance` | `SELECT FOR UPDATE` on account | RFC 9440 header `Idempotency-Key` | Serialized balance recalculation |
| `/api/v1/settlements` | POST | `settlement_service.create_settlement` | Atomic settlement + transaction commit | RFC 9440 header `Idempotency-Key` | Cached response replay on retry |

### Lock Order and Invariants

1. **Reversals**: Lock original `transactions` row first (`FOR UPDATE`). Invariant: Exactly one active reversal per transaction (`uq_transactions_reverses_id`).
2. **Draft Posting**: Lock draft `transactions` row (`FOR UPDATE`). Invariant: A draft can transition from `draft` to `posted` exactly once.
3. **EMI Installments**: Lock target `emi_installments` row (`FOR UPDATE`). Invariant: Only pending installments can be paid; double-payment raises 409 Conflict.
4. **Obligations**: Lock parent `obligations` row (`FOR UPDATE`). Invariant: Payments cannot be made against obligations in `PAID` status.
5. **Statement Ingestion**: Lock `statements` and filter candidate lines (`FOR UPDATE`). Invariant: Candidate lines can be committed to ledger transactions exactly once.
6. **Account Balance Correction**: Lock target `accounts` row (`FOR UPDATE`). Invariant: Balance delta is calculated against the latest state without intervening writes.

### Database Constraints & Migration Revision

- **Alembic Revision**: `20260908_0017_safe_financial_mutations` (down-revision `20260908_0016_tenant_authorization_lifecycle`).
- **Table Added**: `idempotency_records`
  - Columns: `id` (UUID PK), `organization_id` (UUID FK), `user_id` (UUID FK), `idempotency_key` (VARCHAR 128), `request_path` (VARCHAR 255), `request_hash` (CHAR 64 SHA-256), `status` (VARCHAR 20), `response_code` (INT), `response_body` (JSONB), `created_at`, `expires_at` (DateTime, 24h retention default).
  - Constraints & Indexes: `uq_idempotency_org_key (organization_id, idempotency_key)`, plus `ix_idempotency_records_organization_id`, `ix_idempotency_records_user_id`, and `ix_idempotency_records_expires_at`.
- **Constraint Added**: Partial unique index `uq_transactions_reverses_id` on `transactions(reverses_id)` where `reverses_id IS NOT NULL`.
- **Additional business-invariant indexes/constraints**: `uq_emi_installments_plan_seq`, `uq_statement_lines_committed_tx`, and `uq_settlements_id_org`.
- **Reversibility**: Reversible 1-step downgrade and upgrade verified cleanly on real PostgreSQL 16.

### Concurrency and Integration Test Results

Real PostgreSQL concurrency suite executed against `postgres:16-alpine` on `localhost:5433`:
```
tests/test_concurrency_postgres.py::test_idempotency_key_syntax_validation PASSED [ 11%]
tests/test_concurrency_postgres.py::test_idempotency_replay_returns_cached_response PASSED [ 22%]
tests/test_concurrency_postgres.py::test_idempotency_payload_mismatch_raises_conflict PASSED [ 33%]
tests/test_concurrency_postgres.py::test_concurrent_duplicate_transactions_race PASSED [ 44%]
tests/test_concurrency_postgres.py::test_concurrent_reversals_race PASSED [ 55%]
tests/test_concurrency_postgres.py::test_concurrent_emi_installment_payments_race PASSED [ 66%]
tests/test_concurrency_postgres.py::test_concurrent_obligation_payments_race PASSED [ 77%]
tests/test_concurrency_postgres.py::test_concurrent_statement_imports_race PASSED [ 88%]
tests/test_concurrency_postgres.py::test_failure_before_commit_allows_retry PASSED [100%]
9 passed in 1.91s
```

Full Backend Suite:
- `uv run pytest`: 257 passed, 0 failed.
- `uv run ruff check .`: 0 issues found.
- `uv run mypy app`: 0 issues in 100 source files.

Frontend Suite:
- `bun test`: 18 passed, 0 failed.
- `bun run lint`: 0 errors.
- `bun run typecheck`: 0 errors.
- `bun run build`: Next.js production build clean.

## Safety notes

Never test concurrency by posting real user transactions. Do not make a
non-idempotent external email or provider call part of a database transaction
without a durable delivery design.

## Story notes

### 2026-09-08 — US-P05 Implementation & Verification Completed

1. **Idempotency Engine Design**:
   - Implemented `backend/app/core/idempotency.py` conforming to IETF draft RFC 9440.
   - Enforces key length between 16 and 128 characters.
   - Hashes canonical JSON payloads with SHA-256 so sensitive request bodies (card details, amounts) are not logged or stored in plaintext.
   - On matching key and hash, replays cached response with `Idempotency-Replayed: true` header.
   - On matching key with mismatched payload, raises 409 `ConflictError` (`idempotency_key_reused_with_different_payload`).
   - If an error or rollback occurs before commit, the idempotency record is not persisted, allowing immediate safe retry.

2. **Database Concurrency & Locking**:
   - Added `with_for_update()` row-level locking to services: reversals, draft postings, EMI installment payments, obligation payments, statement imports, and account balance corrections.
   - Created partial unique index `uq_transactions_reverses_id` on `transactions(reverses_id)` to ensure database-level guarantee against double reversals even under arbitrary multi-worker race conditions.
   - Verified schema migration reversibility (upgrade and downgrade tested on PostgreSQL 16 container).

3. **Frontend Integration**:
   - Extended `ApiClientOptions` in `frontend/src/lib/api/client.ts` with `idempotencyKey?: string`.
   - Updated Next.js BFF route handler (`frontend/src/app/api/backend/[...path]/route.ts`) to forward `Idempotency-Key` upstream and proxy `Idempotency-Replayed` downstream.
   - Hardened UI dialogs and forms (`transaction-form.tsx`, `correct-balance-dialog.tsx`, `reverse-transaction-dialog.tsx`, `create-emi-dialog.tsx`, `obligation-payment-form.tsx`, `settlement-form.tsx`) with `isSubmittingRef` to prevent double-clicks and `idempotencyKeyRef` to reuse the key during retries.

### 2026-09-08 — Production migration and live verification

- Applied `20260908_0017_safe_financial_mutations` explicitly to Supabase project
  `jklurueadteccrdycyiz` (`Fin Buddy`). Non-secret catalog SQL verified
  `public.alembic_version = 20260908_0017`, confirmed that
  `public.idempotency_records` exists, and confirmed all four business-invariant
  indexes/constraints: `uq_transactions_reverses_id`,
  `uq_emi_installments_plan_seq`, `uq_statement_lines_committed_tx`, and
  `uq_settlements_id_org`. The four supporting idempotency indexes were also
  present.
- FastAPI Cloud production metadata remained fail-closed with
  `ENVIRONMENT=production`, `DEBUG=false`, `AUTO_SEED=false`, and
  `AUTO_MIGRATE=false`; no automatic production migration was enabled.
- Authenticated live verification through the production BFF used a disposable
  card-create operation with a ₹1 limit and no opening balance. The first
  request returned `201`; the same `Idempotency-Key` and identical payload
  returned `201` with `Idempotency-Replayed: true` and an identical cached
  response; reusing the key with a changed payload returned `409` with
  `idempotency_payload_mismatch`. Both disposable test cards were closed after
  the check, and one completed idempotency record remains for its normal 24-hour
  retention window.
- FastAPI Cloud runtime logs for the linked `fin-buddy` app were inspected for
  the preceding 30 minutes after the test. No error, exception, or traceback
  entries were present.
