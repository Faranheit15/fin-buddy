# Release 2 — Progress

| Field | Value |
|--------|--------|
| **Updated** | 2026-08-05 |
| **Current story** | US-01 |
| **Current subtask** | US-01.T5 |
| **Overall** | 0 / 6 stories done |

## Story status

| Story | Status | Notes |
|-------|--------|-------|
| US-01 Auditable ledger | In progress | T4 done → next T5 DoD suite |
| US-02 Multi-account balances | Todo | Blocked on US-01 |
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

## Blockers

_(None yet.)_
