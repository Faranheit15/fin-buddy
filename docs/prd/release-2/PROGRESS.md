# Release 2 — Progress

| Field | Value |
|--------|--------|
| **Updated** | 2026-08-05 |
| **Current story** | US-01 |
| **Current subtask** | US-01.I2 |
| **Overall** | 0 / 6 stories done |

## Story status

| Story | Status | Notes |
|-------|--------|-------|
| US-01 Auditable ledger | In progress | I1 done → next I2 posted-only balance filters |
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

## Blockers

_(None yet.)_
