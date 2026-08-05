# Fin Buddy — Release 2 Tasks

| Field | Value |
|--------|--------|
| **Status** | In progress (R2A done) |
| **Date** | 2026-08-05 |
| **PRD** | [`2026-07-27-fin-buddy-prd.md`](2026-07-27-fin-buddy-prd.md) v2.0 |
| **Baseline** | Phases 0–5 MVP shipped (cards, contacts, transactions, settlements, statement review, notifications, settings, deploy) |
| **Stack** | Next.js (`frontend/`) + FastAPI (`backend/`) + Supabase — do not rewrite |

---

## Purpose

Implement the Release 2 expansion: turn Fin Buddy from a card + friend-lending MVP into an India-first personal finance ledger with accounts, auditable history, debts/loans, card EMIs, GST tracking, richer imports/exports, net-worth dashboard, and email reminders.

## Principles

- Ship each workstream in a runnable state; prefer vertical slices over big-bang rewrites.
- Money stays **integer paise**; never binary floats in domain math.
- Imports and drafts never affect balances until the user explicitly posts/confirms.
- Preserve existing MVP routes and data; migrate forward with additive schema where possible.
- Primary code touchpoints: `backend/app/models`, `backend/app/services`, `backend/app/api/v1`, `backend/alembic`, `frontend/src/app/app/*`, `frontend/src/features`, `frontend/src/lib/api`.

## Dependency graph

```text
R2A LedgerFoundation
 ├──► R2B AccountsTransfers
 ├──► R2C CategoriesSplits
 │
 R2B ──► R2D DebtsLoans
 R2B ──► R2E CardEMIsGST
 R2C ──► R2F ImportExport
 │
 R2D + R2E + R2F ──► R2G NetWorthDashboard
 R2G ──► R2H RemindersPrivacyExport
```

Suggested order: **R2A → R2B ∥ R2C → R2D ∥ R2E → R2F → R2G → R2H**.

**User stories (implementation units):** [`release-2/README.md`](release-2/README.md) — US-01…US-06 with Gather/Plan/Implement/Test/Validate subtasks. Progress: [`release-2/PROGRESS.md`](release-2/PROGRESS.md). Ralph loop: [`release-2/RALPH-LOOP-PROMPT.md`](release-2/RALPH-LOOP-PROMPT.md).

---

## R2A — Auditable ledger foundation

**Goal:** Draft vs posted posting states; no silent mutation of posted history; adjustments and reversals as first-class corrections.

**PRD refs:** FR-T6, FR-T8, FR-T9, FR-AC3, FR-AC4, G2, §8.8

### Backend

- [x] Add `posting_status` enum (`draft` | `posted`) to transactions (default existing rows to `posted` via migration).
- [x] Add transaction types (or dedicated events) for `adjustment` and `reversal`.
- [x] Add optional `reverses_id` / `reversed_by_id` (or equivalent) links.
- [x] Change update/delete APIs: reject silent edit/delete of `posted` rows; expose `reverse` and `adjust` endpoints/services.
- [x] Ensure balance calculations (card, contact, later account) only include `posted` rows.
- [x] Import confirm path continues to create `posted` rows only for accepted candidates (drafts optional for mid-review staging).

### Frontend

- [x] Transaction forms: explicit save as draft vs post (or post-by-default with “save draft” secondary).
- [x] Posted row UI: hide destructive edit; offer Reverse / Correct actions with reason notes.
- [x] Show posting status badge on ledger list and detail.
- [x] **Impeccable:** `shape` before UI changes; craft-floor on implement; Validate with `polish` + `harden` (+ `clarify` if needed).

### Tests

- [x] Unit: draft rows excluded from outstanding/balance.
- [x] Unit: reversal negates original effect; double-reverse blocked.
- [x] Unit: adjustment delta math.
- [x] API: posted update/delete returns 4xx; reverse/adjust succeed with authz.

### Definition of done

- [x] Existing MVP data migrates to `posted` without balance drift.
- [x] User cannot silently overwrite a posted transaction.
- [x] Domain tests green for draft exclusion, reversal, and adjustment.

---

## R2B — Accounts: bank, cash, wallet (+ card specialization)

**Goal:** Unified accounts layer so Fin Buddy tracks more than credit cards; balances derived only from posted ledger entries.

**PRD refs:** FR-AC1–FR-AC6, UC17, UC18, G3, §5.7, §7.2 `accounts`

### Backend

- [ ] Create `accounts` table: `kind` (`bank` | `cash` | `wallet` | `credit_card`), name, institution, currency, optional `credit_card_id`, archive fields.
- [ ] Migration: create a `credit_card` account row for each existing `credit_cards` record (1:1).
- [ ] Add `account_id` on transactions (backfill from card → account mapping where applicable).
- [ ] Account balance service: sum posted ledger effects by account kind rules.
- [ ] Correct Balance API: compute delta vs target → post `adjustment` with reason.
- [ ] CRUD APIs under `/api/v1/accounts` with org membership checks + RLS.

### Frontend

- [ ] Routes: `/app/accounts`, `/app/accounts/[id]`.
- [ ] Sidebar nav entry: Accounts.
- [ ] List/detail UI: balances, recent activity, Correct Balance dialog.
- [ ] Transaction form: select account (cards still selectable via their account or card picker).
- [ ] Empty states for first bank/cash/wallet.
- [ ] **Impeccable:** `shape` + `onboard` empty states; craft-floor; Validate with `polish` + `harden` + `audit`.

### Tests

- [ ] Unit: opening balance via adjustment.
- [ ] Unit: correct-balance delta posting.
- [ ] API: CRUD + archive; cross-org denied.
- [ ] Migration test or script check: every card has an account; balances unchanged after backfill.

### Definition of done

- [ ] User can CRUD bank/cash/wallet accounts and see derived balances.
- [ ] Correct Balance creates an adjustment; no silent stored-balance overwrite.
- [ ] Existing cards remain usable; dashboard card KPIs still work.

---

## R2C — Categories, tags, transfers, splits

**Goal:** Structured categorization and multi-account movement without corrupting income/expense reporting.

**PRD refs:** FR-CAT1–FR-CAT3, FR-T10, FR-T12, UC19, UC20, G4, §8.9

### Backend

- [ ] `categories` table (org-scoped; seed sensible INR personal-finance defaults: income/expense kinds).
- [ ] Optional tags on transactions (array or join table).
- [ ] `transfer` support: `transfer_group_id` pairing equal opposite legs across two accounts.
- [ ] Income/expense reporting helpers that **exclude** transfers and adjustments (document rules).
- [ ] `transaction_splits` table; validate sum(splits) == parent amount.
- [ ] APIs: category CRUD; create transfer; create/update split parents (draft/posted aware from R2A).

### Frontend

- [ ] Category picker on transaction forms; settings or lightweight category manager.
- [ ] Transfer flow UI (from account → to account, amount, date, notes).
- [ ] Split editor on transaction create/edit (draft/posted rules apply).
- [ ] Ledger filters by category/tag.
- [ ] **Impeccable:** `shape` forms; craft-floor; Validate with `polish` + `harden` + `clarify` (+ `adapt` if needed).

### Tests

- [ ] Unit: transfer legs equal; excluded from income/expense totals.
- [ ] Unit: split sum validation.
- [ ] API: transfer creates both legs atomically (or fails with no partial post).

### Definition of done

- [ ] Transfers never inflate income or expense period totals.
- [ ] Splits and categories work on posted ledger paths.
- [ ] Seed categories usable out of the box for a new org.

---

## R2D — Debts & loans (obligations)

**Goal:** First-class personal debts and institutional loans with partial repayments, while keeping v1 settlements coherent.

**PRD refs:** FR-OB1–FR-OB5, FR-S1–FR-S4, UC21, G5, §8.6

### Backend

- [ ] `obligations` + `obligation_payments` tables (see PRD §7.2).
- [ ] CRUD + list filters (direction, status, contact, due window).
- [ ] Remaining balance derived from principal − payments (± interest/penalty if modeled).
- [ ] Migration/compat plan: document how contact balances from card-attributed spend + `settlements` relate to obligations; either:
  - keep settlements and sync summaries, or
  - migrate settlements into obligation_payments with dual-read period.
- [ ] Upcoming dues feed includes obligation due dates.

### Frontend

- [ ] Routes: `/app/debts`, `/app/debts/[id]`.
- [ ] Create debt/loan wizard (receivable vs payable; contact or free-text institution).
- [ ] Record repayment UI; payment history; remaining balance.
- [ ] Contact detail: show related obligations alongside existing settlement ledger.
- [ ] **Impeccable:** `shape` wizard/list-detail; craft-floor; Validate with `onboard` + `polish` + `harden` + `audit`.

### Tests

- [ ] Unit: partial repayment math; overpayment warn-and-allow.
- [ ] Unit: contact outstanding reconciliation under chosen migration strategy.
- [ ] API: authz + archive/settle status transitions.

### Definition of done

- [ ] User can create a receivable and a payable, record partial repayments, and see correct remaining balances.
- [ ] Existing friend settlement flows still work (no double-counting in dashboard friend dues).
- [ ] Migration/compat decision documented in `docs/GOTCHAS.md` or PRD open-questions resolution note.

---

## R2E — Credit-card EMIs + GST tracking

**Goal:** Correct Indian card EMI semantics (principal blocks limit; interest/GST on billing) plus optional GST amounts on spends.

**PRD refs:** FR-E1–FR-E7, FR-C9, FR-C10, FR-T11, UC22, UC23, G6, G7, §8.1–§8.2

### Backend

- [ ] `emi_plans` + `emi_installments` models and APIs.
- [ ] Schedule generator: tenure, principal, interest, fees, GST on interest.
- [ ] Card utilization service:
  - `spend_outstanding`
  - `emi_principal_blocked`
  - `available_credit`
  - split utilization fields on dashboard/card APIs
- [ ] Installment payment posting; advance payment / contact-paid installment allocation (Should).
- [ ] Optional `gst_paise` on transactions for reclaim/reimbursement tracking (no filing module).
- [ ] Plain-language calc payload (structured numbers + short explanation string) for plan detail.

### Frontend

- [ ] Card detail: EMI section (list plans, add plan, schedule table).
- [ ] Optional `/app/emis` index.
- [ ] Utilization UI shows spend vs EMI block separately.
- [ ] “How this is calculated” explainer using API explanation payload.
- [ ] Transaction form: optional GST amount field when relevant.
- [ ] **Impeccable:** `shape` utilization/EMI section; craft-floor; Validate with `polish` + `harden` + `clarify` + `audit`.

### Tests

- [ ] Unit: principal block vs interest/GST billing effect.
- [ ] Unit: available credit after EMI create and after installment principal reduction.
- [ ] Unit: schedule length and sum(principal installments) ≈ plan principal (within defined rounding rules).
- [ ] API: create plan updates card utilization response.

### Definition of done

- [ ] At least one real-world-shaped EMI plan reconciles: principal block, installment breakdown, remaining liability.
- [ ] Dashboard/card utilization no longer treats EMI principal as ordinary spend alone.
- [ ] GST field storable on lines without implying tax filing.

---

## R2F — Import expansion & data export

**Goal:** CSV and Excel enter the same human-review pipeline as PDF; exports available for core records.

**PRD refs:** FR-I8, FR-I9, FR-Z5, UC24, G8, G10 (export portion), §8.7

> Account deletion UX is completed in **R2H** together with reminder preferences; this workstream owns export file generation and import parsers.

### Backend

- [ ] First-class CSV parser (column mapping or Fin Buddy template + generic bank CSV heuristics).
- [ ] Excel parser (`.xlsx`) into `statement_line_candidates` (or generalized `import_batches` if renaming).
- [ ] Keep review → confirm → posted path; fail closed (no partial post).
- [ ] Export API: Excel (and PDF summary if feasible) for accounts, transactions, contacts, obligations, cards.
- [ ] Storage content-types and size limits for xlsx; rate limit uploads.

### Frontend

- [ ] Statements/import UI accepts PDF, CSV, Excel with clear format hints.
- [ ] Column-mapping UI if generic CSV requires it (keep MVP: documented template + best-effort auto).
- [ ] Settings: Export data button → download.
- [ ] **Impeccable:** `shape` import/export affordances; craft-floor; Validate with `polish` + `harden`.

### Tests

- [ ] Parser fixtures for sample CSV and xlsx.
- [ ] Confirm idempotency unchanged.
- [ ] Export contains expected sheets/sections for a seeded org.

### Definition of done

- [ ] CSV and Excel imports cannot affect balances before review confirm.
- [ ] User can download an Excel export of core org data.
- [ ] PDF path remains intact.

---

## R2G — Dashboard & information architecture expansion

**Goal:** Net worth and period P&amp;L-style totals; upcoming items across cards, debts, and EMIs; nav for new modules.

**PRD refs:** FR-D6–FR-D8, UC26, G9, §8.10

### Backend

- [ ] Extend dashboard API:
  - assets, liabilities, net worth
  - period income / expense (transfers excluded)
  - upcoming: card dues + obligation dues + EMI installments
  - retain existing card/friend KPIs
- [ ] Document receivable-as-asset treatment in API/UI copy.

### Frontend

- [ ] Dashboard redesign section: net worth strip + income/expense + unified upcoming list.
- [ ] Sidebar: Accounts, Debts, EMIs (if not card-only), keep Cards/Contacts/Transactions/Statements.
- [ ] Attention items include debt/EMI urgency, not only cards.
- [ ] **Impeccable:** `shape` dashboard composition (Operate; one job per section); craft-floor; Validate with `polish` + `harden` + `audit`.

### Tests

- [ ] Unit: net worth formula with sample accounts + card + EMI + obligation.
- [ ] Unit: income/expense excludes transfers.
- [ ] API contract tests for new dashboard fields.

### Definition of done

- [ ] Dashboard answers: what do I have, what do I owe, what’s due soon — across accounts/cards/debts/EMIs.
- [ ] Nav reaches all R2 modules without dead ends.

---

## R2H — Reminders, privacy schema, deletion, optional PWA

**Goal:** Email due reminders, preference thresholds, account deletion, share-schema readiness, optional installable PWA shell.

**PRD refs:** FR-N3, FR-Z3, FR-Z4, FR-Z6, FR-O7, FR-SH1–FR-SH3, UC16, UC25, G11

### Backend

- [ ] Notification preference fields (due-in N days; email on/off).
- [ ] Email reminder job/endpoint: due soon / overdue for cards, obligations, EMI installments.
- [ ] Wire transactional email provider (document choice in `.env.example`).
- [ ] Account deletion request flow: confirm, cascade/anonymize per policy, revoke sessions.
- [ ] `record_shares` table + minimal service stubs/authorization hooks (full UX can be R3).
- [ ] Audit log events for preference changes, deletion requests, share grant/revoke (if share APIs land).

### Frontend

- [ ] Settings: email reminder toggles + threshold.
- [ ] Settings: Delete account confirm flow.
- [ ] Optional late slice: PWA manifest + service worker shell (offline not required).
- [ ] **Impeccable:** `shape` settings/destructive flows; craft-floor; Validate with `harden` + `clarify` + `polish`.

### Tests

- [ ] Unit: threshold selection includes/excludes dues correctly.
- [ ] API: deletion request authz; only self/owner paths as designed.
- [ ] Share stub: membership alone does not grant record visibility in authorization helper tests.

### Definition of done

- [ ] Email reminders respect preferences for at least card dues (debts/EMIs if those modules shipped).
- [ ] User can request account deletion from Settings.
- [ ] `record_shares` schema exists; privacy principle documented and covered by a unit/authz test.
- [ ] PWA optional: if shipped, app is installable on desktop Chromium; if deferred, note in CONTEXT as R3.

---

## Cross-cutting checklist (every workstream)

- [ ] Alembic migration(s) reviewed; RLS policies updated for new tables.
- [ ] Pydantic schemas + TypeScript API client types updated.
- [ ] No secrets committed; `.env.example` updated when new config is required.
- [ ] Lint / typecheck / targeted tests pass for touched packages.
- [ ] Frontend UI changes: Impeccable `shape` (plan) → craft-floor (implement) → `polish`/`harden`/`audit`/`onboard`/`clarify` as applicable (validate). See [`release-2/README.md`](release-2/README.md).
- [ ] `docs/GOTCHAS.md` updated when a migration trap or retired approach appears.
- [ ] Do not import across `frontend/` ↔ `backend/` divide.

---

## Release 2 exit criteria

Mapped to PRD §15.2:

1. Bank/cash/wallet accounts with ledger-derived balances.
2. Correct Balance → adjustment; no silent posted mutation.
3. Transfers excluded from income/expense.
4. Personal debt/loan + partial repayments.
5. Card EMI with separate principal-block utilization.
6. Optional GST amounts on lines.
7. CSV/Excel review imports never auto-post.
8. Dashboard net worth + period income/expense + unified upcoming.
9. Data export + account deletion request.
10. Email reminders with preference thresholds.
11. Domain tests for EMI block, transfer exclusion, adjustments.

When all exit criteria pass, update [`docs/CONTEXT.md`](../CONTEXT.md) to the next focus and mark Release 2 complete in the PRD roadmap notes.

---

## Explicitly out of scope (Release 3+)

- Connected-user debt confirmation / dispute
- Full share/unshare product UX beyond schema readiness
- Salary / PF / NPS modules
- Investments / XIRR
- Account Aggregators / Open Banking
- AI extraction agents
- Native mobile apps
- SMS / WhatsApp reminders
- Subscription / commercial SaaS packaging

---

## Document history

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-08-05 | Initial Release 2 backlog from PRD v2.0 expand decision |
