# US-P11 — Fast capture and relationship ledger

| Field | Value |
| --- | --- |
| **Status** | `todo` |
| **Sequence** | 11 |
| **Depends on** | [US-P04](US-P04-tenant-authorization-lifecycle.md), [US-P05](US-P05-safe-financial-mutations.md), [US-P10](US-P10-dues-billing-cockpit.md) |
| **One-loop objective** | Make everyday spending, settlements, repayments, and corrections fast while keeping their accounting meanings distinct. |
| **Primary boundaries** | Transaction form, accounts/cards, contacts, settlements, obligations, correction flows |

## User story

**As** a Fin Buddy owner recording a spend or repayment on a phone
**I want** fast, contextual capture with clear ownership and correction paths
**So that** the ledger stays current without forcing me to understand the database model.

## Why this matters

The original product problem is shared credit-card spending: a friend uses a
card, the owner records it, and later settles the balance. The expanded app now
also has formal obligations and account repayments. The current surfaces make
these concepts easy to confuse, and common edit/correction affordances are
missing even though backend support exists.

## Scope and non-goals

In scope: quick-add actions, defaults, editing drafts, posted correction
affordances, settlement/obligation distinction, repayment cash-source clarity,
and relationship-ledger copy. Out of scope: the statement review table and
global accessibility pass, covered by US-P12 and US-P13.

## Touchpoints

- [`frontend/src/app/app/transactions/page.tsx`](../../../frontend/src/app/app/transactions/page.tsx)
- [`frontend/src/features/transactions/`](../../../frontend/src/features/transactions)
- [`frontend/src/features/contacts/`](../../../frontend/src/features/contacts)
- [`frontend/src/app/app/contacts/`](../../../frontend/src/app/app/contacts)
- [`frontend/src/app/app/debts/`](../../../frontend/src/app/app/debts)
- [`frontend/src/lib/api/`](../../../frontend/src/lib/api)
- [`backend/app/api/v1/transactions.py`](../../../backend/app/api/v1/transactions.py)
- [`backend/app/api/v1/settlements.py`](../../../backend/app/api/v1/settlements.py)
- [`backend/app/api/v1/obligations.py`](../../../backend/app/api/v1/obligations.py)
- [`docs/GOTCHAS.md`](../../GOTCHAS.md)

## Acceptance criteria

1. A user can quickly start transaction, transfer, settlement, or obligation
   repayment capture with sensible card/account/contact/category defaults.
2. The UI clearly distinguishes `they owe me`, `I owe them`, issuer payment,
   contact settlement, and formal debt repayment.
3. Draft transactions are editable/deletable; posted transactions are not
   silently mutated and expose a clear reverse/correct path.
4. Settlement and repayment forms explain whether and how a cash/bank account
   changes, without changing existing accounting semantics accidentally.
5. Common validation, pending, duplicate-submit, success, and failure states
   are recoverable and do not discard entered money values.
6. Desktop dense mode and mobile quick capture both complete the intended flow
   using the idempotency behavior from US-P05.
7. The product copy and routes make the contact-versus-obligation distinction
   understandable without requiring a documentation lookup.

## Tasks

### Gather

- [ ] **US-P11.G1 — Trace capture flows.** Map every field, default, API call,
  status transition, balance effect, and refresh path for transaction, transfer,
  settlement, repayment, draft, post, reverse, adjust, and account correction.
- [ ] **US-P11.G2 — Identify friction.** Walk through new spend, friend spend,
  settlement, formal loan repayment, EMI payment, and correction on desktop and
  390px mobile. Record keystrokes/taps, missing defaults, confusing labels, and
  lost-context refreshes.
- [ ] **US-P11.G3 — Define semantic copy.** Write examples using one contact
  spend, one issuer payment, one receivable, and one payable. Confirm each
  example's effect on card, account, contact, obligation, and net worth.

### Plan

- [ ] **US-P11.P1 — Shape quick capture.** Use impeccable Operate-mode guidance
  to design a compact action launcher and forms that preserve the Ledger Shelf
  density. Define keyboard order, mobile primary action, focus return, and
  confirmation behavior.
- [ ] **US-P11.P2 — Define defaults and progressive disclosure.** Choose the
  safest prefilled account/card, date in IST, transaction type, contact/category
  search, optional notes, and when advanced fields appear.
- [ ] **US-P11.P3 — Define correction language.** Specify when an action is
  edit, reverse, adjust, delete draft, or record a new settlement. Explain the
  audit consequence before confirmation.

### Implement

- [ ] **US-P11.I1 — Improve the action launcher.** Add transaction, transfer,
  settlement, repayment, and relevant card/EMI actions with route-aware context
  from the cockpit and detail pages.
- [ ] **US-P11.I2 — Improve capture forms.** Add safe defaults, searchable
  selectors, keyboard flow, preserved input on error, idempotency key handling,
  and explicit pending/success/error states.
- [ ] **US-P11.I3 — Finish correction affordances.** Expose draft edit/delete,
  posted reverse/correct, account correction, and card/contact/obligation edit
  actions where backend support exists. Do not add silent posted mutation.
- [ ] **US-P11.I4 — Clarify relationships.** Add explanatory labels and empty
  states for friend ledger, settlement, formal debt, repayment account, and
  issuer payment. Keep obligations separate from contact balance totals.
- [ ] **US-P11.I5 — Preserve context after writes.** Refresh the smallest
  affected list/detail/dashboard data, return focus to the initiating action,
  and avoid an unexplained full-page reset.

### Test

- [ ] **US-P11.T1 — Test financial scenarios.** Cover owner spend, friend spend,
  refund, issuer payment, settlement, receivable, payable, partial repayment,
  EMI payment, transfer, draft, reverse, and correction with expected balances.
- [ ] **US-P11.T2 — Test retry and validation.** Cover duplicate submit, network
  timeout, invalid amount/date, overpayment, missing source account, stale
  record, and unauthorized relationship.
- [ ] **US-P11.T3 — Test responsive capture.** Run keyboard and touch flows at
  320px/390px and desktop widths; assert focus, scroll, dialog, and form state.
- [ ] **US-P11.T4 — Run quality gates.** Run relevant backend tests and frontend
  lint/typecheck/build plus an authenticated browser smoke using synthetic data.

### Validate

- [ ] **US-P11.V1 — Perform the original user ritual.** Record a friend spend
  against a card, view what the friend owes, record the settlement, and confirm
  the issuer liability remains distinct and correct.
- [ ] **US-P11.V2 — Perform the formal-debt ritual.** Create or use a formal
  obligation, record a repayment from an account, and confirm the contact KPI
  and obligation balance do not double count.
- [ ] **US-P11.V3 — Verify corrections.** Correct a draft and reverse a posted
  entry; confirm history, balances, and copy communicate what happened.
- [ ] **US-P11.V4 — Close the story.** Record scenario results, screenshots,
  route/API changes, and any intentionally deferred capture action in this file
  and [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- Capture-flow map and friction notes.
- Financial scenario reconciliation table.
- Before/after desktop/mobile screenshots.
- Retry/idempotency and correction test output.
- Copy decision for settlements versus obligations.

## Safety notes

Do not hide whether a repayment changes an account. Do not turn a contact
settlement into an obligation or vice versa. Do not add optimistic balance
updates that can show money the backend has not committed.

## Story notes

_(Append dated implementation decisions and evidence here.)_
