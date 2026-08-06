# US-06 — Insights, imports/exports & reminders

| Field | Value |
|--------|--------|
| **Status** | Todo |
| **Priority** | P1 |
| **Maps to** | R2F + R2G + R2H |
| **PRD** | FR-I8, FR-I9, FR-Z5, FR-D6–FR-D8, FR-N3, FR-Z3–FR-Z6, FR-O7, FR-SH1–FR-SH3, UC16, UC24–UC26, G8–G11 |
| **Depends on** | US-02, US-03, US-04, US-05 (for full net-worth/upcoming; import/export can start after US-02) |

## User story

**As** a Fin Buddy owner  
**I want** CSV/Excel import with review, data export, a net-worth dashboard, email due reminders, and account deletion  
**So that** Release 2 is a complete personal daily driver with trustworthy insights and compliance basics.

## Current architecture touchpoints

- Statements: [`backend/app/services/statement_service.py`](../../../../backend/app/services/statement_service.py) (PDF/text/CSV sample)
- Dashboard: [`backend/app/api/v1/dashboard.py`](../../../../backend/app/api/v1/dashboard.py)
- Notifications: in-app only
- Settings: [`frontend/src/app/app/settings/page.tsx`](../../../../frontend/src/app/app/settings/page.tsx)

## Acceptance criteria

1. CSV and Excel enter the same review → confirm → posted pipeline; never auto-post; PDF intact.
2. Excel export of core org data from Settings.
3. Dashboard shows net worth, period income/expense (transfers excluded), unified upcoming (cards + debts + EMIs).
4. Nav reaches Accounts, Debts, EMIs (if present), existing modules.
5. Email reminders honor preference thresholds for dues.
6. Account deletion request from Settings.
7. `record_shares` schema + authz stub (full UX is R3); PWA optional.

Work this story in **three slices** (still one story for Ralph sequencing): Import/Export → Dashboard/IA → Reminders/Privacy/Deletion.

---

## Subtasks

### Gather

- [x] **US-06.G1** Define Fin Buddy CSV/Excel template columns; document in story notes.
- [x] **US-06.G2** Confirm net-worth formula (receivables as assets — PRD default).
- [x] **US-06.G3** Choose email provider approach (Supabase email vs Resend/SES) and required env vars.
- [x] **US-06.G4** Define account deletion policy (hard delete vs anonymize; org cascade).

### Plan

- [x] **US-06.P1** Spec CSV/xlsx parsers into existing statement/import review models.
- [x] **US-06.P2** Spec export workbook sheets.
- [x] **US-06.P3** Spec dashboard API extensions + sidebar IA — **impeccable `shape`** for net-worth / upcoming dashboard composition (Operate; one job per section).
- [x] **US-06.P4** Spec reminder job, preference fields, deletion API, `record_shares` table.
- [x] **US-06.P5** Optional: PWA manifest plan — ship or explicitly defer to R3 in CONTEXT. Spec Settings deletion/reminder UI with **impeccable `shape`**.

### Implement — Slice A (Import/Export)

- [x] **US-06.I1** CSV + Excel parsers + upload content types + review path unchanged semantics.
- [ ] **US-06.I2** Export API + Settings download button.
- [ ] **US-06.I3** Frontend import UI accepts CSV/xlsx with format hints — **impeccable craft-floor**; keep review flow calm and dense.

### Implement — Slice B (Dashboard / IA)

- [ ] **US-06.I4** Dashboard service: assets, liabilities, net worth, income/expense, unified upcoming.
- [ ] **US-06.I5** Frontend dashboard sections + sidebar links for all R2 modules — **impeccable craft-floor**; no hero clutter; KPI strip remains operable.

### Implement — Slice C (Reminders / Privacy / Deletion)

- [ ] **US-06.I6** Preference fields + email reminder sender/job + `.env.example`.
- [ ] **US-06.I7** Account deletion request flow + session revoke.
- [ ] **US-06.I8** `record_shares` migration + minimal authz helper tests.
- [ ] **US-06.I9** Settings UI: reminder prefs + delete account; optional PWA shell — **impeccable craft-floor**; destructive delete must be `harden`ed.

### Test

- [ ] **US-06.T1** Parser fixtures CSV/xlsx; confirm idempotency; no partial post.
- [ ] **US-06.T2** Export contains expected sections for seeded org.
- [ ] **US-06.T3** Unit: net worth + income/expense excludes transfers.
- [ ] **US-06.T4** Unit: reminder threshold include/exclude.
- [ ] **US-06.T5** API: deletion authz; share stub membership ≠ visibility.
- [ ] **US-06.T6** Full backend + frontend DoD.

### Validate

- [ ] **US-06.V1** Manual: import CSV → review → confirm; balances only after confirm.
- [ ] **US-06.V2** Manual: export downloads; dashboard net worth matches hand calc on sample data.
- [ ] **US-06.V3** Manual: toggle email reminder prefs (dry-run or logged send acceptable in dev).
- [ ] **US-06.V4** **Impeccable:** `polish` + `harden` + `audit` on dashboard, import, and settings; `clarify` deletion confirm copy; `onboard` if new empty states appeared.
- [ ] **US-06.V5** Confirm all Release 2 exit criteria in [`../RELEASE-2-TASKS.md`](../RELEASE-2-TASKS.md); update CONTEXT; mark Done.

## Story notes

- CSV template: `Date` (YYYY-MM-DD), `Description`, `Amount` (INR), `Type` (Debit/Credit), `Category` (Optional), `Notes` (Optional), `Reference` (Optional). Context (Account) is derived from the upload target.
- Net-worth formula: `Assets = sum(bank, cash, wallet) + sum(receivables)`. `Liabilities = sum(card_outstanding) + sum(payables)`. (Card outstanding inherently includes EMI principal).
- Email provider: **Resend**. It integrates well with Next.js/FastAPI. Required env var: `RESEND_API_KEY`.
- Deletion policy: **Hard delete** via DB cascades for all Organization data (accounts, transactions, obligations, EMIs). Supabase `auth.users` deletion triggered via service role client.
- PWA: ship / defer: Defer to R3 per absolute rules defaults (not trivial).

### Implementation Specs (P1-P5)

**P1: CSV/Excel Parsers**
- Add `pandas` dependency. Extend `backend/app/services/statement_service.py`.
- Handle `text/csv` and `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
- Map typical columns (Date, Description, Amount, Type) to generate `StatementLineCandidate` objects exactly as PDF does, keeping the review flow unaltered.

**P2: Export Workbook**
- Provide `GET /api/v1/export` returning an `.xlsx` file.
- Sheets: Accounts (kind, balance), Transactions (date, amount, category), Contacts (net balance), Obligations (status, remaining), Cards (limit, outstanding, blocked).

**P3: Dashboard API & UI Shape**
- **API**: Add `assets_paise`, `liabilities_paise`, `net_worth_paise`, `period_income_paise`, `period_expense_paise` (excluding transfers) to `DashboardData`. Add `upcoming_items` (merged sorted list of card dues, EMI pending, and obligation dues).
- **UI Shape (Operate)**:
  - Top row: Net Worth strip displaying Assets, Liabilities, and Net Worth cleanly.
  - Second row: Income vs Expense for the current month.
  - Sidebar addition: Links to Accounts, Debts, EMIs.
  - Unified Upcoming column: Replace scattered reminders with a single dense list of action items.
  - Continue keeping `CardsTable` and `ContactsList` compact (The Ledger Shelf rule).

**P4: Reminders & Deletion Schema**
- **Preferences**: Add `email_reminders_enabled` to Profile.
- **Reminder Job**: Endpoint `POST /api/v1/jobs/send-reminders` (scans active users, checks dues within `due_soon_days`, uses Resend API via `RESEND_API_KEY`).
- **Deletion API**: `DELETE /api/v1/users/me` hard-cascades all Org data, then removes Supabase auth user via admin client.
- **Shares**: Alembic script for `record_shares` (id, org_id, record_type, record_id, shared_with_user_id) + basic authz stub.

**P5: Settings UI Shape**
- **UI Shape (Operate)**:
  - Reminders Card: Toggle for "Enable email reminders".
  - Export Card: "Download Excel Export" button.
  - Danger Zone Card: "Delete Account" button opening a double-confirmation modal requiring the user to type "DELETE".
