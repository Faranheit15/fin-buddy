# US-P13 — Mobile, accessibility, and visual consistency

| Field | Value |
| --- | --- |
| **Status** | `todo` |
| **Sequence** | 13 |
| **Depends on** | [US-P10](US-P10-dues-billing-cockpit.md), [US-P11](US-P11-fast-capture-relationships.md), [US-P12](US-P12-statement-review-notifications.md) |
| **One-loop objective** | Make the Ledger Shelf experience usable and coherent for touch, keyboard, screen-reader, reduced-motion, dark-mode, and narrow-screen users. |
| **Primary boundaries** | Shared UI primitives, app shell, tables/dialogs/forms/charts, tokens, responsive layouts |

## User story

**As** a Fin Buddy user working from a phone, keyboard, or assistive technology
**I want** every important state and action to remain understandable and reachable
**So that** dense finance tooling feels deliberate rather than fragile.

## Why this matters

The Ledger Shelf visual foundation is strong, but the audit found compact touch
targets, wide action-heavy tables, dialogs without reliable mobile overflow,
missing live announcements, weak table/chart semantics, ungrouped navigation,
and ad-hoc color tokens. These issues affect trust in a finance product, not
just visual polish.

## Scope and non-goals

In scope: responsive shell, touch targets, forms/statuses, navigation/tabs,
tables/charts, dialogs, motion, dark mode, and semantic tokens. Out of scope:
new financial features and data-fetch architecture, covered by other stories.

## Touchpoints

- [`DESIGN.md`](../../../DESIGN.md)
- [`frontend/src/app/globals.css`](../../../frontend/src/app/globals.css)
- [`frontend/src/components/ui/`](../../../frontend/src/components/ui)
- [`frontend/src/components/layout/`](../../../frontend/src/components/layout)
- [`frontend/src/components/shared/`](../../../frontend/src/components/shared)
- [`frontend/src/components/charts/`](../../../frontend/src/components/charts)
- [`frontend/src/app/app/`](../../../frontend/src/app/app)
- [`frontend/src/features/`](../../../frontend/src/features)

## Acceptance criteria

1. Critical actions have comfortable coarse-pointer targets while desktop
   density remains intact; no important mobile action is hidden only inside a
   horizontally scrolling table.
2. Forms expose field errors through `aria-invalid`, `aria-describedby`, and
   announced status regions; focus moves predictably after submit/error/dialog.
3. Navigation exposes current location, mobile menu state, and logical groups;
   tabs/tables/dialogs have appropriate semantics and labels.
4. Charts have a keyboard/screen-reader equivalent such as a data table or
   accessible summary; hover is not the only way to inspect money data.
5. Dialogs fit short mobile viewports with safe max-height, scrolling, close
   controls, and focus trapping/return.
6. Dark mode, reduced motion, empty/loading/error/success states, and semantic
   urgency colors are consistent with `DESIGN.md`; undefined or ad-hoc color
   classes are removed or documented.
7. Keyboard, screen-reader-oriented, mobile, and visual audit results are
   recorded for representative routes.

## Tasks

### Gather

- [ ] **US-P13.G1 — Establish the design baseline.** Read `DESIGN.md`, run the
  impeccable context/audit workflow, and record the current token, typography,
  spacing, radius, motion, dark-mode, and operate-mode rules. Do not auto-update
  stale design metadata without recording the decision.
- [ ] **US-P13.G2 — Audit representative surfaces.** Test login, dashboard,
  cards, transactions, statement review, contacts/debts, notifications, and
  settings at 320px, 390px, tablet, and desktop. Record overflow, target size,
  focus order, dialog behavior, and state visibility.
- [ ] **US-P13.G3 — Audit semantics.** Inspect errors/statuses, nav/current
  state, tabs, tables, form labels, chart alternatives, heading order, contrast,
  reduced motion, and duplicate controls. Capture violations with route and
  component references.

### Plan

- [ ] **US-P13.P1 — Shape the system pass.** Use impeccable in Operate mode to
  plan shared primitives before one-off fixes: field error, status announcer,
  data table, mobile list, dialog shell, nav group, and semantic badge.
- [ ] **US-P13.P2 — Define responsive rules.** Set target widths, minimum touch
  size, table-to-card transformation rules, safe-area behavior, dialog height,
  breakpoint hierarchy, and what remains dense on desktop.
- [ ] **US-P13.P3 — Define token rules.** Map primary ink, muted text, border,
  quiet accent, success, warning, destructive coral, EMI/attention status, and
  dark equivalents. Remove indigo/emerald/undefined utility drift unless an
  explicit semantic role requires it.

### Implement

- [ ] **US-P13.I1 — Add shared accessibility primitives.** Implement reusable
  field errors, `aria-live` status, loading/error recovery, focus return, and
  disabled/busy behavior; migrate representative auth and finance forms.
- [ ] **US-P13.I2 — Refine the shell.** Group navigation into understandable
  areas, add `aria-current`, remove duplicate notification ambiguity, and ensure
  the mobile primary action exposes the full intended capture set.
- [ ] **US-P13.I3 — Refine tables/charts.** Add captions/scopes/labels, mobile
  row representations or clear action affordances, keyboard chart summaries or
  data views, and visible filter/result counts.
- [ ] **US-P13.I4 — Refine dialogs and motion.** Add viewport max-height,
  overflow, safe close target, focus trap/return, submit busy state, and
  reduced-motion behavior to shared dialog/skeleton/chart transitions.
- [ ] **US-P13.I5 — Apply tokens and copy consistency.** Replace ad-hoc colors,
  align dark mode, fix contradictory settings/privacy/demo copy, and preserve
  the near-monochrome Ledger Shelf direction.

### Test

- [ ] **US-P13.T1 — Test keyboard use.** Tab through nav, forms, tables, dialogs,
  charts, and destructive actions; assert visible focus, logical order, Escape,
  focus return, and no keyboard trap.
- [ ] **US-P13.T2 — Test accessibility semantics.** Run axe or equivalent on
  representative routes; inspect labels, live regions, table headers, headings,
  contrast, status announcements, and reduced-motion preference.
- [ ] **US-P13.T3 — Test responsive behavior.** Run browser checks at 320px,
  390px, tablet, and desktop; assert no unexpected horizontal overflow and that
  important actions are reachable.
- [ ] **US-P13.T4 — Run impeccable validation.** Run the required polish,
  harden, clarify, onboard, and audit checks applicable to touched surfaces,
  then run frontend lint/typecheck/build.

### Validate

- [ ] **US-P13.V1 — Complete representative journeys.** Perform login, add
  spend, statement review, settlement, notification read, and settings actions
  using keyboard and narrow-screen layouts.
- [ ] **US-P13.V2 — Verify visual parity.** Compare light/dark screenshots and
  ensure accents communicate semantic urgency rather than decoration.
- [ ] **US-P13.V3 — Verify assistive recovery.** Trigger validation, network,
  parse, and destructive-action errors and confirm the user is told what failed
  and what to do next.
- [ ] **US-P13.V4 — Close the story.** Record audit output, screenshots,
  representative routes, token decisions, and residual violations in this file
  and [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- Impeccable context/audit/polish/harden notes.
- Before/after screenshots at target widths and themes.
- Keyboard and accessibility results.
- Token mapping and any intentional exceptions.
- Route/component residual list.

## Safety notes

Do not solve a mobile table problem by hiding financial columns. Do not use
color as the only indicator of due/overdue status. Do not introduce a generic
dashboard visual language that conflicts with the existing Ledger Shelf.

## Story notes

_(Append dated implementation decisions and evidence here.)_
