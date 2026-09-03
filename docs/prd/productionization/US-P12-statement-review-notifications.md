# US-P12 — Statement review and notification clarity

| Field | Value |
| --- | --- |
| **Status** | `todo` |
| **Sequence** | 12 |
| **Depends on** | [US-P05](US-P05-safe-financial-mutations.md), [US-P06](US-P06-durable-statement-ingestion.md), [US-P10](US-P10-dues-billing-cockpit.md) |
| **One-loop objective** | Make statement review and notifications trustworthy, recoverable, and explicit about what will affect the ledger. |
| **Primary boundaries** | Statement detail/review UI, candidate rows, import status, notifications, settings copy |

## User story

**As** a Fin Buddy owner importing a card statement
**I want** to understand, correct, and approve every candidate before it enters my ledger
**So that** automation saves time without silently changing my financial truth.

## Why this matters

Human-reviewed statement import is a differentiator, but the review table has
wide repeated controls with weak labels and limited row-level feedback. The
workflow also needs stronger progress/retry/partial-failure states. Notifications
and reminder settings currently contain contradictory copy and weak action
feedback.

## Scope and non-goals

In scope: review row semantics, amount/date correction, validation/duplicates,
parse/import states, import summary, notification sync/read behavior, and
reminder copy. Out of scope: the signed upload protocol, covered by US-P06,
and the general accessibility/token pass, covered by US-P13.

## Touchpoints

- [`frontend/src/app/app/statements/page.tsx`](../../../frontend/src/app/app/statements/page.tsx)
- [`frontend/src/app/app/statements/[id]/page.tsx`](../../../frontend/src/app/app/statements/[id]/page.tsx)
- [`frontend/src/features/statements/`](../../../frontend/src/features/statements)
- [`frontend/src/app/app/notifications/page.tsx`](../../../frontend/src/app/app/notifications/page.tsx)
- [`frontend/src/app/app/settings/page.tsx`](../../../frontend/src/app/app/settings/page.tsx)
- [`backend/app/api/v1/statements.py`](../../../backend/app/api/v1/statements.py)
- [`backend/app/services/statement_service.py`](../../../backend/app/services/statement_service.py)
- [`backend/app/api/v1/notifications.py`](../../../backend/app/api/v1/notifications.py)
- [`backend/app/services/notification_service.py`](../../../backend/app/services/notification_service.py)

## Acceptance criteria

1. A reviewer can see statement status, source, parse progress, candidate count,
   reviewed count, rejected/duplicate count, and the exact import consequence.
2. Every editable review control has an accessible name tied to its row/field;
   amount, date, merchant, type, category, contact, and notes validate clearly.
3. Duplicate/confidence/exception rows are identifiable and can be resolved or
   rejected without losing the original parsed value.
4. Import is an explicit human-confirmed action, idempotent, and reports
   created/skipped/failed counts with a retry path.
5. Parse, upload, review, import, retry, expired session, and partial failure
   states are recoverable and never imply success prematurely.
6. Notifications show truthful source/action/status, announce mark-read/read-all
   outcomes, do not silently swallow failures, and paginate or explain limits.
7. Settings copy accurately describes card/EMI/email reminder coverage and
   provider availability.

## Tasks

### Gather

- [ ] **US-P12.G1 — Trace the statement state machine.** Document upload,
  stored, parsing, ready, review, rejected, importing, imported, failed, and
  retry transitions; identify stale status races and which fields are editable.
- [ ] **US-P12.G2 — Walk a review.** Use a synthetic statement with normal,
  duplicate, unknown merchant, unknown contact, invalid amount/date, refund,
  transfer, and split candidates. Record how a reviewer discovers and resolves
  each case.
- [ ] **US-P12.G3 — Audit notification behavior.** Trace list/unread/read/read-all
  calls, `sync=true` behavior, refreshes, failures, caps, and action links.
  Compare backend notification types with settings/reminder copy.

### Plan

- [ ] **US-P12.P1 — Shape the review workflow.** Use impeccable guidance for
  the critical review surface: summary/header, progress, exception filters,
  compact desktop table, mobile row editor, explicit import CTA, and recovery
  states. Preserve the Ledger Shelf hierarchy.
- [ ] **US-P12.P2 — Define candidate semantics.** Specify original versus edited
  value, confidence/duplicate marker, accepted/rejected/committed state,
  validation rules, bulk action scope, and how a partial import is represented.
- [ ] **US-P12.P3 — Define notification contract.** Specify event source, title,
  action route, unread transition, sync result, retry copy, pagination, and
  reminder coverage. No GET should unexpectedly create durable data without a
  documented reason.

### Implement

- [ ] **US-P12.I1 — Improve review controls.** Add row/field labels, amount/date
  editing where API support exists, original-value affordances, validation,
  duplicate/confidence indicators, and rejection reasons.
- [ ] **US-P12.I2 — Improve state transitions.** Show upload/parse/import
  progress, disable conflicting actions, handle stale/expired states, and
  provide retry/partial-failure summaries. Preserve accepted rows until the
  user explicitly commits them.
- [ ] **US-P12.I3 — Improve import results.** Show created/skipped/failed counts,
  link imported transactions, identify rows needing correction, and ensure a
  repeated commit cannot duplicate ledger entries.
- [ ] **US-P12.I4 — Improve notifications.** Add truthful sync/read status,
  retry/announcement behavior, explicit pagination/limits, and stable action
  links. Keep notification refresh work bounded.
- [ ] **US-P12.I5 — Correct reminder copy.** Align settings, notifications, and
  email controls with the actual supported card/EMI reminder behavior and the
  optional provider configuration.

### Test

- [ ] **US-P12.T1 — Test review editing.** Cover every field, invalid values,
  duplicate/confidence flags, rejected rows, bulk actions, keyboard navigation,
  and preservation of original parsed data.
- [ ] **US-P12.T2 — Test import safety.** Cover empty/partial/all-valid/all-
  invalid statements, retry-after-timeout, concurrent commit, already-imported
  statement, and summary counts.
- [ ] **US-P12.T3 — Test notifications.** Cover unread count, read/read-all,
  sync failure, retry, pagination, stale notification, action link, and
  settings/reminder coverage.
- [ ] **US-P12.T4 — Run UI and backend gates.** Run relevant backend tests,
  frontend lint/typecheck/build, impeccable audit/harden, and a browser smoke
  with a synthetic file.

### Validate

- [ ] **US-P12.V1 — Complete a review ritual.** Upload a safe fixture, review
  exceptions, edit/reject rows, import accepted rows, and reconcile the result
  with the transaction list and dashboard.
- [ ] **US-P12.V2 — Verify recovery.** Interrupt parse/import/network at each
  stage and confirm the next action is clear and no duplicate rows appear.
- [ ] **US-P12.V3 — Verify notifications.** Trigger each supported notification
  type, mark it read, follow its action, and confirm failure/retry feedback.
- [ ] **US-P12.V4 — Close the story.** Record fixture summary, state machine,
  screenshots, import reconciliation, notification results, and residual copy
  decisions in this file and [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- Statement state transition table.
- Synthetic fixture case matrix.
- Import summary and ledger reconciliation.
- Review screenshots at desktop/mobile widths.
- Notification/read/retry test results.

## Safety notes

Never auto-post merely because parsing succeeded. Never discard the original
parsed candidate when an edit is made. Do not use real statements or email
addresses in fixtures or screenshots.

## Story notes

_(Append dated implementation decisions and evidence here.)_
