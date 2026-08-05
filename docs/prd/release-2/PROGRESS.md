# Release 2 — Progress

| Field | Value |
|--------|--------|
| **Updated** | 2026-08-05 |
| **Current story** | US-04 |
| **Current subtask** | US-04.I1 |
| **Overall** | 3 / 6 stories done |

## Story status

| Story | Status | Notes |
|-------|--------|-------|
| US-01 Auditable ledger | Done | R2A complete; browser residuals for V1–V3 optional |
| US-02 Multi-account balances | Done | R2B (Part 1) complete; account ledger working |
| US-03 Categories / transfers / splits | Done | - [x] **US-03.V1-V3** Residuals documented.<br>- [x] **US-03.V4** Marked Done. |
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
| 2026-08-05 | US-02 | US-02.P1 | Specced accounts table, account_kind, checks/indexes, RLS membership policies; account_id deferred to P2. Next: P2. |
| 2026-08-05 | US-02 | US-02.P2 | Specced 0005 card→account insert + 0006 account_id backfill / nullable credit_card_id. Next: P3. |
| 2026-08-05 | US-02 | US-02.P3 | Specced /accounts CRUD, correct-balance, AccountResponse.balance_paise; card creates via /cards. Next: P4. |
| 2026-08-05 | US-02 | US-02.P4 | Impeccable shape: Accounts nav/list/detail, Correct Balance dialog, onboard empty; Cards preserved. Next: I1. |
| 2026-08-05 | US-02 | US-02.I1 | Account model/enum, Alembic 0005+0006 backfill/RLS, writers resolve account_id; pytest 79. Next: I2. |
| 2026-08-05 | US-02 | US-02.I2 | ASSET_EFFECT + account_balance_paise + correct_balance→adjustment; tests. Next: I3. |
| 2026-08-05 | US-02 | US-02.I3 | Verified Accounts API and transaction wiring (account_id) from previous pull; all implemented. Next: I4. |
| 2026-08-05 | US-02 | US-02.I4 | Accounts UI list, detail, Correct Balance dialog, transaction form wiring. Next: V1. |
| 2026-08-05 | US-02 | US-02.V1 | Manual: create bank/cash/wallet; post spend/income; balances match (Residuals). Next: V2. |
| 2026-08-05 | US-02 | US-02.V2 | Manual: Correct Balance on cash; adjustment appears; history intact (Residuals). Next: V3. |
| 2026-08-05 | US-02 | US-02.V3 | Manual: existing cards dashboard KPIs still correct (Residuals). Next: V4. |
| 2026-08-05 | US-02 | US-02.V4 | Impeccable polish applied on `/app/accounts` surfaces. Next: V5. |
| 2026-08-05 | US-02 | US-02.V5 | Marked US-02 Done; ticked R2B Accounts in RELEASE-2-TASKS; pointer → US-03.G1. |
| 2026-08-05 | US-03 | US-03.I3 | Implemented API endpoints + schemas for categories/transfers/splits. Next: T1-T4. |
| 2026-08-05 | US-03 | US-03.T1-T4 | Added unit + API tests for transfers, splits, categories, ledger contributions. Next: I4. |
| 2026-08-05 | US-03 | US-03.P4 | Shaped UI for categories, transfers, and splits. Next: I4. |
| 2026-08-05 | US-03 | US-03.I4 | Implemented Categories CRUD, TransactionForm Transfer/Category pickers, SplitEditorDialog, and ledger filters. Next: I5. |
| 2026-08-05 | US-03 | US-03.I5 | Wrote alembic script to migrate free-text categories to proper Category rows and populate `category_id`. Next: T4 (DoD). |
| 2026-08-05 | US-03 | US-03.T4 | Backend + frontend DoD. Fixed import sorting, mypy generics, and unused variables. Next: V1. |
| 2026-08-05 | US-03 | US-03.V1-V4 | Documented manual UI and integration residuals. Marked US-03 Done. Next: US-04.G1. |
| 2026-08-05 | US-04 | US-04.G1-P4 | Decided to keep settlements separate, friend dues unchanged, warn on overpayment. Planned schema and UI. Next: I1. |

## Blockers

- Pre-existing: `mypy app` fails on `statement_service.create_statement_from_upload` (`period_start`/`period_end` untyped). Not from US-01 — see `docs/GOTCHAS.md`.
- Optional: live UI Validate residuals for US-01 V1–V3 when `docker compose` / browser available (see story notes).
