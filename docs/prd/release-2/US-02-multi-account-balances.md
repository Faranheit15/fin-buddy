# US-02 — Multi-account balances

| Field | Value |
|--------|--------|
| **Status** | Todo |
| **Priority** | P0 |
| **Maps to** | R2B |
| **PRD** | FR-AC1–FR-AC6, UC17, UC18, G3, §5.7, §7.2 |
| **Depends on** | US-01 (adjustments / posted ledger) |

## User story

**As** a Fin Buddy owner  
**I want** bank, cash, and wallet accounts whose balances come only from posted ledger entries  
**So that** I can track all liquid money alongside credit cards without spreadsheet juggling.

## Current architecture touchpoints

- Cards only: [`backend/app/models/credit_card.py`](../../../../backend/app/models/credit_card.py)
- Transactions require `credit_card_id` today
- No `accounts` table
- UI nav: [`frontend/src/components/layout/app-sidebar.tsx`](../../../../frontend/src/components/layout/app-sidebar.tsx)
- Routes under `frontend/src/app/app/cards/*`

## Acceptance criteria

1. Account kinds: `bank`, `cash`, `wallet`, `credit_card`.
2. Every existing credit card gets a 1:1 `credit_card` account (migration).
3. Transactions gain `account_id` (backfilled from card mapping where needed).
4. Balance = sum of posted ledger effects; Correct Balance posts an `adjustment`.
5. CRUD + archive APIs with org authz + RLS.
6. UI: `/app/accounts`, `/app/accounts/[id]`, sidebar entry; cards still work.

---

## Subtasks

### Gather

- [ ] **US-02.G1** Decide whether `credit_card_id` stays required on card spends or becomes optional when `account_id` points at a card account — document invariant.
- [ ] **US-02.G2** List balance effect rules per account kind (asset accounts vs credit liability).
- [ ] **US-02.G3** Confirm Correct Balance UX fields (target balance, reason, effective date).

### Plan

- [ ] **US-02.P1** Spec `accounts` schema + RLS policies + indexes.
- [ ] **US-02.P2** Spec migration/backfill: card → account; transaction `account_id`.
- [ ] **US-02.P3** Spec `/api/v1/accounts` endpoints and balance response shape.
- [ ] **US-02.P4** Spec frontend routes, empty states, Correct Balance dialog — **impeccable `shape`** (+ `onboard` notes for first bank/cash/wallet); keep `/app/cards` working.

### Implement

- [ ] **US-02.I1** Models + enums + Alembic migration + backfill.
- [ ] **US-02.I2** Account balance service + Correct Balance → adjustment (uses US-01).
- [ ] **US-02.I3** Accounts API + wire transactions to accept `account_id`.
- [ ] **US-02.I4** Frontend: accounts list/detail, nav, transaction account picker, Correct Balance — **impeccable craft-floor**; Operate density consistent with cards/contacts.
- [ ] **US-02.I5** Update `.env.example` only if new config needed (usually none).

### Test

- [ ] **US-02.T1** Unit: opening balance via adjustment.
- [ ] **US-02.T2** Unit: correct-balance delta.
- [ ] **US-02.T3** API: CRUD/archive; cross-org denied.
- [ ] **US-02.T4** Migration check: every card has an account; sample balances unchanged.
- [ ] **US-02.T5** Backend + frontend DoD commands for touched code.

### Validate

- [ ] **US-02.V1** Manual: create bank/cash/wallet; post spend/income; balances match.
- [ ] **US-02.V2** Manual: Correct Balance on cash; adjustment appears; history intact.
- [ ] **US-02.V3** Manual: existing cards dashboard KPIs still correct.
- [ ] **US-02.V4** **Impeccable:** `onboard` empty states; `polish` + `harden` + `audit` on `/app/accounts` surfaces.
- [ ] **US-02.V5** Mark Done; update PROGRESS + RELEASE-2-TASKS R2B.

## Story notes

- Card/account invariant:
- Asset vs liability effect rules:
