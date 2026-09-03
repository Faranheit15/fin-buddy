# US-P05 — Safe financial mutations

| Field | Value |
| --- | --- |
| **Status** | `todo` |
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

- [ ] **US-P05.G1 — Enumerate commands.** List every POST/PATCH/DELETE that
  creates, posts, reverses, corrects, pays, settles, imports, or deletes a
  financial record. Record side effects, current transaction boundary, and
  whether the client can safely retry it today.
- [ ] **US-P05.G2 — Reproduce races.** Build deterministic tests or a local
  harness for two EMI payments, two obligation payments, two statement imports,
  duplicate transaction submissions, and a request that loses its response
  after commit.
- [ ] **US-P05.G3 — Inspect schema support.** Check existing unique indexes,
  status columns, self-references, transaction isolation, and database pool
  behavior. Confirm which operations need a new migration.

### Plan

- [ ] **US-P05.P1 — Define the idempotency contract.** Choose header/body
  placement, key length/format, scope by user and organization, retention,
  response replay behavior, and conflict behavior when the same key has a
  different payload. Keep keys out of logs when they could identify data.
- [ ] **US-P05.P2 — Define lock order.** For each flow, identify the row that
  must be locked first, the invariant protected, the expected transaction
  isolation, and a bounded behavior for lock timeout/deadlock.
- [ ] **US-P05.P3 — Define uniqueness.** Specify database constraints for one
  reversal per source, one payment per installment/operation, one committed
  statement line per source identity, and any other duplicate-prone operation.

### Implement

- [ ] **US-P05.I1 — Add operation identity.** Implement the smallest shared
  persistence or constraint mechanism needed to record an idempotency key and
  replay the original result without storing sensitive payloads unnecessarily.
- [ ] **US-P05.I2 — Protect EMI and obligation payments.** Lock the pending
  installment/obligation state, validate the remaining amount inside the
  transaction, create ledger/payment rows atomically, and make a repeated
  payment return the existing result.
- [ ] **US-P05.I3 — Protect statement import.** Make candidate selection and
  committed marking conditional/locked, add a stable source identity, and
  ensure parsing/import status transitions cannot be overwritten by stale work.
- [ ] **US-P05.I4 — Protect other writes.** Apply the contract to transaction
  create/post/reverse/adjust, settlements, transfers, and account corrections
  where a retry can duplicate a ledger event. Keep posted-record audit rules.

### Test

- [ ] **US-P05.T1 — Test replay.** Send the same command twice with the same key
  and assert one side effect, the same response identity, and no extra audit
  row. Send the same key with a changed payload and assert a clear conflict.
- [ ] **US-P05.T2 — Test concurrency.** Run concurrent requests against a real
  PostgreSQL test database for EMI payment, obligation payment, and statement
  import. Assert balances, remaining amounts, and committed counts are correct.
- [ ] **US-P05.T3 — Test failure recovery.** Simulate provider/database failure
  before commit, after related-row insert, and after commit-before-response.
  Retry each case and assert no orphan or duplicate financial event.
- [ ] **US-P05.T4 — Run quality gates.** Run all affected backend tests, Ruff,
  mypy, migration tests, and a focused API integration suite.

### Validate

- [ ] **US-P05.V1 — Verify ledger invariants.** Compare before/after balances,
  statement counts, installment status, obligation remaining balance, and audit
  history for every concurrency scenario.
- [ ] **US-P05.V2 — Verify client behavior.** Confirm the BFF retries only when
  the operation key is preserved and shows a useful conflict/error when a key
  is reused incorrectly.
- [ ] **US-P05.V3 — Close the story.** Record the operation contract, migration
  revision, race harness, test output, and known unsupported commands in this
  file and [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- Financial-command/idempotency matrix.
- Lock order and invariant table.
- New constraints/migration revision.
- Concurrent test output and invariant comparisons.
- Retry-after-commit behavior.

## Safety notes

Never test concurrency by posting real user transactions. Do not make a
non-idempotent external email or provider call part of a database transaction
without a durable delivery design.

## Story notes

_(Append dated implementation decisions and evidence here.)_
