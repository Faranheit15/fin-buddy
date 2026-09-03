# US-P10 — Dues and billing cockpit

| Field | Value |
| --- | --- |
| **Status** | `todo` |
| **Sequence** | 10 |
| **Depends on** | [US-P04](US-P04-tenant-authorization-lifecycle.md), [US-P08](US-P08-database-api-performance.md) |
| **One-loop objective** | Make the dashboard the single action-oriented answer to what needs attention today. |
| **Primary boundaries** | Dashboard API, dashboard page/components, card billing math, EMIs, obligations, contacts |

## User story

**As** a finance owner managing several cards and shared spends
**I want** one cockpit that explains every upcoming liability and next action
**So that** I do not have to reconstruct my financial state from six different screens.

## Why this matters

The dashboard already exposes net worth, assets/liabilities, card utilization,
income/expense, upcoming items, contacts, charts, and activity. The problem is
hierarchy and amount semantics: statement balance, minimum due, EMI installment,
formal debt, and friend receivable are not yet one clear action queue.

## Scope and non-goals

In scope: dashboard information hierarchy, unified dues/action contract,
billing-cycle calendar, date correctness, live/sample/empty/error states, and
action links. Out of scope: the broader capture and statement-review flows.

## Touchpoints

- [`backend/app/api/v1/dashboard.py`](../../../backend/app/api/v1/dashboard.py)
- [`backend/app/services/dashboard_analytics.py`](../../../backend/app/services/dashboard_analytics.py)
- [`backend/app/services/ledger_service.py`](../../../backend/app/services/ledger_service.py)
- [`frontend/src/app/app/page.tsx`](../../../frontend/src/app/app/page.tsx)
- [`frontend/src/components/dashboard/`](../../../frontend/src/components/dashboard)
- [`frontend/src/lib/api/dashboard.ts`](../../../frontend/src/lib/api/dashboard.ts)
- [`PRODUCT.md`](../../../PRODUCT.md)
- [`DESIGN.md`](../../../DESIGN.md)

## Acceptance criteria

1. Within the first viewport, a user can distinguish due soon, overdue, and
   informational items and choose the next action.
2. Every monetary item labels its meaning: statement balance, minimum due,
   installment, outstanding card liability, formal obligation, or friend
   receivable/payable.
3. Card statement dates, due dates, utilization, and EMI blocks are visible in
   a coherent calendar/timeline without fixed demo dates in live mode.
4. Missing due dates are shown as unknown/not configured, never silently treated
   as due today.
5. Contact settlements and formal obligations remain separate and the UI
   explains why they are not combined.
6. Live, sample, empty, loading, and error states are truthful and actionable;
   sample activity is not presented as live activity.
7. Dashboard API response fields, frontend types, calculations, and actions are
   covered by tests and preserve existing posted-only ledger semantics.

## Tasks

### Gather

- [ ] **US-P10.G1 — Inventory current dashboard data.** Map every API field to
  its source query, unit, sign, timezone, status, and UI consumer. Identify
  duplicate queries and fields returned by the backend but missing in frontend
  types.
- [ ] **US-P10.G2 — Define amount vocabulary.** Write a small glossary and
  examples for statement balance, minimum due, total outstanding, EMI
  installment, EMI principal block, obligation remaining, and friend balance.
  Confirm which values are estimates versus authoritative ledger totals.
- [ ] **US-P10.G3 — Trace date logic.** Inspect card due rules, statement dates,
  EMI dates, obligation dates, current-date injection, IST formatting, sample
  fixtures, and missing-date behavior. Reproduce the fixed-date/missing-date
  issues before editing.
- [ ] **US-P10.G4 — Observe current layout.** Capture desktop and 320–430px
  screenshots/measurements of the dashboard hierarchy, first actionable item,
  scroll depth, chart load, and sample/live/error state.

### Plan

- [ ] **US-P10.P1 — Shape the cockpit.** Use the impeccable skill in Operate
  mode to design a Ledger Shelf hierarchy: attention strip, dues/action queue,
  billing calendar, core KPIs, then secondary analytics. Keep near-monochrome
  primary ink and semantic urgency only.
- [ ] **US-P10.P2 — Define the action model.** For each item specify source,
  amount meaning, due state, destination route, CTA label, completion state, and
  whether the action records a payment, reviews data, or only navigates.
- [ ] **US-P10.P3 — Define aggregation contract.** Decide whether to extend the
  existing dashboard response or add a read model. Keep one authenticated
  request where possible and prohibit shared caching of private data.

### Implement

- [ ] **US-P10.I1 — Correct backend semantics.** Fix live `as_of` date handling,
  missing due-date representation, card/EMI/obligation amount labels, and any
  dashboard type omissions. Preserve INR paise and IST rules.
- [ ] **US-P10.I2 — Add the action queue.** Build a unified, sorted list of due,
  overdue, review, and settlement actions with clear source labels and deep
  links. Keep contact dues separate from obligations.
- [ ] **US-P10.I3 — Add the billing timeline/calendar.** Show each card's
  statement and due rhythm, utilization, EMI block, and relevant upcoming
  amount. Make unknown configuration visible instead of inventing a date.
- [ ] **US-P10.I4 — Reorder the dashboard.** Put the daily answer first, defer
  secondary charts, reduce nested-card overload, and keep live/sample/error/
  empty states visually and verbally distinct.

### Test

- [ ] **US-P10.T1 — Test financial semantics.** Cover card dues, minimum/full
  balance, EMI blocks, obligations, positive/negative contact balances, missing
  dates, current date, month boundaries, IST boundaries, and posted-only totals.
- [ ] **US-P10.T2 — Test action routing.** Assert every action type produces the
  correct route/identifier and no unsafe or missing destination is rendered.
- [ ] **US-P10.T3 — Test state truthfulness.** Cover live data, zero-data
  onboarding, API failure, expired session, sample mode, and partial data.
- [ ] **US-P10.T4 — Run UI checks.** Use the impeccable shape/polish/harden and
  run frontend lint, typecheck, and build plus a browser smoke at desktop and
  mobile widths.

### Validate

- [ ] **US-P10.V1 — Perform a daily-ritual walkthrough.** Starting with no
  context, answer what is due, why, how much, and what to do next using only
  the dashboard.
- [ ] **US-P10.V2 — Reconcile values.** Compare displayed values with API and
  synthetic ledger fixtures; verify no double counting between contacts,
  obligations, cards, and EMIs.
- [ ] **US-P10.V3 — Verify responsive hierarchy.** Confirm the first actionable
  item remains visible and usable at 320px, 390px, tablet, and desktop widths.
- [ ] **US-P10.V4 — Close the story.** Record the glossary, screenshots,
  response contract, test output, and known follow-up in this file and
  [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- Dashboard field/source/semantics matrix.
- Amount glossary and date rules.
- Before/after screenshots at target widths.
- API and financial reconciliation tests.
- Daily-ritual walkthrough result.

## Safety notes

Never make an unknown due date look like today. Do not change ledger signs or
merge settlements with obligations to simplify the UI. The dashboard must
explain financial semantics, not hide them behind decorative cards.

## Story notes

_(Append dated implementation decisions and evidence here.)_
