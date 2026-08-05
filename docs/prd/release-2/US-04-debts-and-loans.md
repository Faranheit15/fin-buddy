# US-04 — Debts & loans

| Field | Value |
|--------|--------|
| **Status** | Todo |
| **Priority** | P1 |
| **Maps to** | R2D |
| **PRD** | FR-OB1–FR-OB5, FR-S1–FR-S4, UC21, G5, §8.6 |
| **Depends on** | US-02 (accounts optional for repayment source); settlements already exist |

## User story

**As** a Fin Buddy owner  
**I want** first-class personal debts and institutional loans with partial repayments  
**So that** I can track money owed outside card-attributed friend spend without double-counting.

## Current architecture touchpoints

- [`backend/app/models/settlement.py`](../../../../backend/app/models/settlement.py) + contacts balances
- Contact detail UI for settlements
- No `obligations` table

## Acceptance criteria

1. Obligations: personal debt + institutional loan; receivable vs payable.
2. Partial repayments; remaining balance derived.
3. Contact or free-text counterparty supported.
4. Existing settlements keep working; friend dues not double-counted.
5. Compat decision documented in `docs/GOTCHAS.md`.
6. UI: `/app/debts`, `/app/debts/[id]`; contact detail shows related obligations.

---

## Subtasks

### Gather

- [x] **US-04.G1** Choose compat strategy: keep `settlements` + separate obligations **or** migrate settlements into `obligation_payments` with dual-read — **default if undecided: keep settlements, add obligations**.
- [x] **US-04.G2** Define how dashboard “friend dues” aggregates settlements vs receivable obligations.
- [x] **US-04.G3** Confirm overpayment policy (warn, allow) matches PRD.

### Plan

- [x] **US-04.P1** Spec `obligations` + `obligation_payments` schema + RLS.
- [x] **US-04.P2** Spec APIs + remaining-balance formula.
- [x] **US-04.P3** Spec UI wizard + repayment flow + contact integration — **impeccable `shape`**.
- [x] **US-04.P4** Write GOTCHAS note draft for settlement/obligation relationship.

### Implement

- [x] **US-04.I1** Models + migration + RLS.
- [x] **US-04.I2** Services: CRUD, payments, remaining balance, filters.
- [ ] **US-04.I3** API routes under `/api/v1/obligations` (or `/debts`).
- [ ] **US-04.I4** Frontend debts pages + contact detail section + sidebar — **impeccable craft-floor**; match contacts/cards list-detail patterns.
- [ ] **US-04.I5** Dashboard friend-dues aggregation respects compat decision.

### Test

- [ ] **US-04.T1** Unit: partial repayment; overpayment.
- [ ] **US-04.T2** Unit: no double-count with settlements under chosen strategy.
- [ ] **US-04.T3** API authz + status transitions.
- [ ] **US-04.T4** Backend + frontend DoD.

### Validate

- [ ] **US-04.V1** Manual: receivable + payable + two partial repayments.
- [ ] **US-04.V2** Manual: existing settlement on a contact still correct.
- [ ] **US-04.V3** **Impeccable:** `onboard` debts empty state; `polish` + `harden` + `audit` on `/app/debts`.
- [ ] **US-04.V4** Publish GOTCHAS note; mark Done; update PROGRESS + R2D.

## Story notes

### Gather Decisions
- **US-04.G1 (Compat strategy):** Keep `settlements` as they are. Add `obligations` and `obligation_payments` separately.
- **US-04.G2 (Friend dues):** Dashboard "friend dues" aggregates ONLY transactions minus settlements. Obligations are tracked separately and do not double-count in the friend dues KPI.
- **US-04.G3 (Overpayment):** Warn-and-allow. Repayments exceeding the balance are permitted, resulting in a negative remaining balance.

### Implementation Plan
- **US-04.P1 (Schema & RLS):** 
  - `obligations`: `id`, `organization_id`, `contact_id` (nullable), `counterparty_name` (nullable), `type` (`receivable`, `payable`), `amount_paise`, `currency`, `status` (`active`, `paid`, `defaulted`), `notes`. RLS restricts by `organization_id`.
  - `obligation_payments`: `id`, `organization_id`, `obligation_id`, `account_id` (nullable), `amount_paise`, `date`, `notes`. RLS restricts by `organization_id`.
- **US-04.P2 (API & Formula):** 
  - APIs: `POST /api/v1/obligations`, `GET /api/v1/obligations` (with balances joined), `GET /api/v1/obligations/{id}`, `POST /api/v1/obligations/{id}/payments`.
  - Formula: `remaining_balance = obligation.amount_paise - sum(payments.amount_paise)`. Overpayment yields negative balance.
- **US-04.P3 (UI Shape - Impeccable):**
  - `/app/debts`: Top-level tabbed layout (Receivables / Payables). Scannable lists with progress bars. "Add Debt" primary CTA.
  - `/app/debts/[id]`: Detail view showing original amount, remaining balance, and a table of payments. "Record Payment" opens a dialog (warns on overpayment).
  - Contacts integration: Add an "Obligations" tab on `/app/contacts/[id]` to list debts linked to the contact.
- **US-04.P4 (GOTCHAS Draft):** "Settlements vs Obligations: Settlements are exclusively used to reduce contact balances derived from ad-hoc shared card spends. Obligations (US-04) are explicit debts/loans. Do not mix them. Friend dues dashboard KPI excludes obligations to prevent double-counting."
