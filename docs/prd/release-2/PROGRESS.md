# Release 2 — Progress

| Field | Value |
|--------|--------|
| **Updated** | 2026-08-05 |
| **Current story** | US-02 |
| **Current subtask** | US-02.P1 |
| **Overall** | 1 / 6 stories done |

## Story status

| Story | Status | Notes |
|-------|--------|-------|
| US-01 Auditable ledger | Done | R2A complete; browser residuals for V1–V3 optional |
| US-02 Multi-account balances | In progress | Gather done → next P1 accounts schema |
| US-03 Categories / transfers / splits | Todo | Blocked on US-01, US-02 |
| US-04 Debts & loans | Todo | Blocked on US-02 |
| US-05 Card EMIs & GST | Todo | Blocked on US-01, US-02 |
| US-06 Insights / imports / reminders | Todo | Blocked on US-02…US-05 for full scope |

## Iteration log

| When | Story | Subtask | Result |
|------|-------|---------|--------|
| 2026-08-05 | US-01 | US-01.G1 | Inventoried balance consumers; documented which queries must filter `posted` in story notes. Next: G2. |
| 2026-08-05 | US-01 | US-01.G2 | Chose post-by-default + Save draft secondary; documented API/UI implications. Next: G3. |
| 2026-08-05 | US-01 | US-01.G3 | Confirmed additive migration: posting_status backfill posted, nullable reverse FKs, extend transaction_type. Next: P1. |
| 2026-08-05 | US-01 | US-01.P1 | Specced Alembic `20260805_0003`: posting_status enum, type extensions, columns/FKs/indexes. Next: P2. |
| 2026-08-05 | US-01 | US-01.P2 | Specced transaction_service + HTTP: create/post/reverse/adjust; posted immutable; delta_sign for adjustments. Next: P3. |
| 2026-08-05 | US-01 | US-01.P3 | Impeccable shape brief for ledger: status badges, draft/post CTAs, Reverse dialog; adjust UI deferred to US-02. Next: P4. |
| 2026-08-05 | US-01 | US-01.P4 | Wrote unit+API test matrix mapped to T1–T5; FakeSession/helpers approach. Next: I1. |
| 2026-08-05 | US-01 | US-01.I1 | Added PostingStatus, adjustment/reversal types, Transaction columns, Alembic 20260805_0003 + delta_sign; GOTCHAS enum note. Next: I2. |
| 2026-08-05 | US-01 | US-01.I2 | Posted-only ledger filters + adjustment/reversal contributions; domain helpers + tests. Next: I3. |
| 2026-08-05 | US-01 | US-01.I3 | transaction_service + API post/reverse/adjust; posted immutable; activity enum migration; service tests. Next: I4. |
| 2026-08-05 | US-01 | US-01.I4 | Ledger UI: status badges/filter, Save draft, Post draft, Reverse dialog; API client types. Next: I5. |
| 2026-08-05 | US-01 | US-01.I5 | Import confirm always posts; helper + regression tests. Next: T1. |
| 2026-08-05 | US-01 | US-01.T1 | Draft exclusion matrix covered (card/contact mix, draft-only, post-then-include). Next: T2. |
| 2026-08-05 | US-01 | US-01.T2 | Reversal net-zero tests (purchase/refund/contact); double-reverse after success; cannot reverse reversal/draft. Next: T3. |
| 2026-08-05 | US-01 | US-01.T3 | Adjustment ±delta + contact contrib; zero rejected; service +/–/contact outstanding checks. Next: T4. |
| 2026-08-05 | US-01 | US-01.T4 | Posted 409 immutability; draft delete; create posted/draft; reject reverse type; cross-org card/tx NotFound. Next: T5. |
| 2026-08-05 | US-01 | US-01.T5 | DoD: pytest 79, ruff green (fixed I001), frontend lint+typecheck OK; mypy pre-existing statement_service noted in GOTCHAS. Next: V1. |
| 2026-08-05 | US-01 | US-01.V1 | Draft→post balance path re-verified via 6 unit tests; browser residuals documented (no live stack). Next: V2. |
| 2026-08-05 | US-01 | US-01.V2 | Reverse purchase path re-verified via 8 unit tests; UI Reverse dialog residuals documented. Next: V3. |
| 2026-08-05 | US-01 | US-01.V3 | Import confirm posted-only + idempotent re-verified (3 tests); UI residuals documented. Next: V4. |
| 2026-08-05 | US-01 | US-01.V4 | Impeccable polish/harden on ledger UI (a11y labels, errors, reverse dialog, form busy). Next: V5. |
| 2026-08-05 | US-01 | US-01.V5 | Marked US-01 Done; ticked R2A in RELEASE-2-TASKS; pointer → US-02.G1. |
| 2026-08-05 | US-02 | US-02.G1 | account_id required; credit_card_id nullable + required+consistent only for credit_card accounts. Next: G2. |
| 2026-08-05 | US-02 | US-02.G2 | Asset vs liability effect tables; card=outstanding, bank/cash/wallet=cash held; NW signs. Next: G3. |
| 2026-08-05 | US-02 | US-02.G3 | Correct Balance: target + reason + optional effective at; server-side delta; no contact in dialog. Next: P1. |

## Blockers

- Pre-existing: `mypy app` fails on `statement_service.create_statement_from_upload` (`period_start`/`period_end` untyped). Not from US-01 — see `docs/GOTCHAS.md`.
- Optional: live UI Validate residuals for US-01 V1–V3 when `docker compose` / browser available (see story notes).
