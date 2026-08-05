# US-03 — Categories, transfers & splits

| Field | Value |
|--------|--------|
| **Status** | Todo |
| **Priority** | P1 |
| **Maps to** | R2C |
| **PRD** | FR-CAT1–FR-CAT3, FR-T10, FR-T12, UC19, UC20, G4, §8.9 |
| **Depends on** | US-01, US-02 |

## User story

**As** a Fin Buddy owner  
**I want** categories, tags, account transfers, and split transactions  
**So that** my income/expense reporting stays accurate and money movement between accounts is clear.

## Current architecture touchpoints

- Free-text `category` on transactions only
- No transfer pairing; no splits table
- Reporting today is card/friend oriented (dashboard), not income/expense

## Acceptance criteria

1. Org-scoped categories with income/expense kinds + seed defaults for new orgs.
2. Optional tags on transactions.
3. Transfers create paired legs (`transfer_group_id`) that do **not** inflate income/expense.
4. Split lines sum to parent amount; invalid splits rejected.
5. UI: category picker, transfer flow, split editor, ledger filters.

---

## Subtasks

### Gather

- [ ] **US-03.G1** Draft default India-personal category list (income vs expense).
- [ ] **US-03.G2** Decide tags storage: `text[]` vs join table.
- [ ] **US-03.G3** Confirm transfer posting: both legs posted atomically; draft transfers allowed or not.

### Plan

- [ ] **US-03.P1** Spec `categories`, `transaction_splits`, transfer fields on transactions.
- [ ] **US-03.P2** Spec income/expense helpers (exclude transfers + adjustments).
- [ ] **US-03.P3** Spec APIs: category CRUD, create transfer, create/update splits.
- [ ] **US-03.P4** Spec UI flows and empty/error states — **impeccable `shape`** (transfer + split editors; Operate mode).

### Implement

- [ ] **US-03.I1** Migrations + models + seed categories on org bootstrap (or first access).
- [ ] **US-03.I2** Transfer + split services with validation; reporting helpers.
- [ ] **US-03.I3** API endpoints + schemas.
- [ ] **US-03.I4** Frontend: category manager/picker, transfer UI, split editor, filters — **impeccable craft-floor**.
- [ ] **US-03.I5** Migrate free-text `category` to `category_id` where practical (keep text fallback if needed).

### Test

- [ ] **US-03.T1** Unit: transfer legs equal; excluded from income/expense.
- [ ] **US-03.T2** Unit: split sum validation.
- [ ] **US-03.T3** API: atomic transfer (no partial post on failure).
- [ ] **US-03.T4** Backend + frontend DoD.

### Validate

- [ ] **US-03.V1** Manual: transfer bank → cash; both balances move; income/expense unchanged.
- [ ] **US-03.V2** Manual: split a purchase across two categories; totals match.
- [ ] **US-03.V3** **Impeccable:** `polish` + `harden` + `clarify` on transfer/split/category UI; `adapt` if forms break on tablet widths.
- [ ] **US-03.V4** Mark Done; update PROGRESS + R2C checklist.

## Story notes

- Default categories:
- Tags storage:
- Transfer draft policy:
