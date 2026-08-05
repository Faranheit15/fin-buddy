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

- [x] **US-03.G1** Draft default India-personal category list (income vs expense).
- [x] **US-03.G2** Decide tags storage: `text[]` vs join table.
- [x] **US-03.G3** Confirm transfer posting: both legs posted atomically; draft transfers allowed or not.

### Plan

- [x] **US-03.P1** Spec `categories`, `transaction_splits`, transfer fields on transactions.
- [x] **US-03.P2** Spec income/expense helpers (exclude transfers + adjustments).
- [x] **US-03.P3** Spec APIs: category CRUD, create transfer, create/update splits.
- [x] **US-03.P4** Spec UI flows and empty/error states — **impeccable `shape`** (transfer + split editors; Operate mode).

### Implement

- [x] **US-03.I1** Migrations + models + seed categories on org bootstrap (or first access).
- [x] **US-03.I2** Transfer + split services with validation; reporting helpers.
- [x] **US-03.I3** API endpoints + schemas.
- [x] **US-03.I4** Frontend: category manager/picker, transfer UI, split editor, filters — **impeccable craft-floor**.
- [x] **US-03.I5** Migrate free-text `category` to `category_id` where practical (keep text fallback if needed).

### Test

- [x] **US-03.T1** Unit: transfer legs equal; excluded from income/expense.
- [x] **US-03.T2** Unit: split sum validation.
- [x] **US-03.T3** API: atomic transfer (no partial post on failure).
- [ ] **US-03.T4** Backend + frontend DoD.

### Validate

- [ ] **US-03.V1** Manual: transfer bank → cash; both balances move; income/expense unchanged.
- [ ] **US-03.V2** Manual: split a purchase across two categories; totals match.
- [ ] **US-03.V3** **Impeccable:** `polish` + `harden` + `clarify` on transfer/split/category UI; `adapt` if forms break on tablet widths.
- [ ] **US-03.V4** Mark Done; update PROGRESS + R2C checklist.

## Story notes

### US-03.G1 — Default category list
**Expense:** Food & Dining, Groceries, Shopping, Transport, Utilities, Housing, Entertainment, Health & Fitness, Travel, Subscriptions, Personal Care, Education, EMI/Debt, Miscellaneous.
**Income:** Salary, Business, Investments, Rental, Gifts, Refunds, Other Income.

### US-03.G2 — Tags storage
**Decision:** Use PostgreSQL `text[]` (array of strings) on the `transactions` table. It's much simpler than a join table for personal finance tags and can be indexed with GIN if needed.

### US-03.G3 — Transfer posting
**Decision:** Transfers are two transaction rows linked by a `transfer_group_id` (UUID). They are created atomically. Draft transfers are allowed. The service will enforce that both legs always share the same `posting_status`. Posting one leg automatically posts the other leg atomically.

### US-03.P4 — UI Shaping
**1. Category Picker:** Replace the free-text `Category` input in `TransactionForm` with a dropdown/select bound to `GET /api/v1/categories`. Add a Settings/Categories page (`/app/categories`) for full CRUD.
**2. Transfer Flow:** In `TransactionForm`, add a "Transfer" toggle or select option. When selected, show "From Account" and "To Account" dropdowns. Submit will `POST /api/v1/transfers`.
**3. Split Editor:** Add a "Split" button to draft transactions in the ledger. Opens a dialog to define `TransactionSplit` rows (category, amount) that must validate against the total amount. Submit `PUT /api/v1/transactions/{id}/splits`.
**4. Ledger Filters:** Add a category dropdown filter to the ledger view.
