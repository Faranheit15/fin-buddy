# Fin Buddy — Product Requirements Document

| Field | Value |
|--------|--------|
| **Document version** | 2.0 |
| **Date** | 2026-08-05 |
| **Status** | Approved for Release 2 planning |
| **Owner** | Product / Engineering |
| **Audience** | Personal use first; public multi-user release later |
| **Prior version** | 1.0 (2026-07-27) — Phases 0–5 MVP shipped |

---

## 1. Overview & problem statement

### 1.1 Product name

**Fin Buddy**

### 1.2 One-liner

Fin Buddy is an India-first personal finance ledger with deep credit-card, EMI, and shared-spend workflows — so limits, dues, accounts, debts, and who owes whom live in one system of record.

### 1.3 Problem

People who juggle money across cards, bank accounts, cash, wallets, EMIs, and informal loans struggle to answer:

1. How much do I actually have and owe across all accounts?
2. How much available credit remains on each card — after normal spend **and** EMI principal blocks?
3. When is the next statement date, EMI installment, loan due, or payment due date?
4. Who spent what, on which card, and how much does each friend still owe?
5. Can I trust the history — or did an edit silently rewrite the past?

Spreadsheets and bank apps do not combine **multi-account balances**, **card billing calendars**, **EMI math**, **person-attributed spend + settlements**, and an **auditable ledger** in one place.

### 1.4 Solution

A web application with a modern finance-admin UI where the owner:

- Manages accounts: bank, cash, wallets, and credit cards (metadata only — never full PAN/CVV)
- Tracks statement and due dates from billing configuration
- Records an auditable spend ledger (draft → posted; corrections via adjustments/reversals)
- Attributes spend to contacts (friends) and tracks repayments / personal debts
- Models credit-card EMIs with correct principal-block vs billing interest/GST behavior
- Optionally tracks GST amounts on spends and reimbursements (no tax filing)
- Uploads statement PDFs, CSV, or Excel for assisted import (human review before commit)
- Sees a dashboard of net worth, utilization, dues, EMIs, and friend outstanding balances
- Exports data and can request account deletion

### 1.5 Target user journey over time

| Stage | Audience | Implication |
|--------|----------|-------------|
| **Shipped (v1 / Phases 0–5)** | Single power user | Card + friend-lending daily driver |
| **Release 2** | Same founder / power user | Full personal-finance breadth on the same stack |
| **Release 3+** | Wider public / invited users | Connected debts, PWA polish, salary/investments, commercial packaging |

### 1.6 What shipped in v1 (baseline)

Phases 0–5 are **done** and remain the foundation:

- Auth (Google, email/password, magic link) + personal org bootstrap + multi-tenant schema
- Credit cards, billing cycle math, dashboard card KPIs
- Contacts, transactions, settlements (friend repayments)
- Statement PDF/text upload + human review import
- In-app notifications, settings, polish, deploy configs

Release 2 **extends** this product; it does not replace the stack (Next.js + FastAPI + Supabase).

---

## 2. Goals & non-goals

### 2.1 Goals (Release 2)

| ID | Goal |
|----|------|
| G1 | Single source of truth for accounts, cards, cycles, spends, debts, EMIs, and friend dues |
| G2 | Auditable ledger: draft vs posted; no silent mutation of posted history |
| G3 | Bank, cash, and wallet accounts alongside credit cards; balances derived from ledger |
| G4 | Categories, tags, transfers, and split entries with correct income/expense reporting |
| G5 | First-class personal debts and institutional loans (contacts supported; linked users later) |
| G6 | Credit-card EMI plans with principal block vs normal spend utilization, interest, and GST |
| G7 | Optional GST amount tracking for spends and reimbursements (no filing) |
| G8 | CSV, Excel, and PDF imports all require human review before ledger commit |
| G9 | Dashboard: net worth, period income/expense, upcoming dues (cards + debts + EMIs), friend dues |
| G10 | Data export (Excel/PDF) and account deletion request |
| G11 | Email reminders for due soon / overdue (in-app notifications already exist) |
| G12 | Production-grade code: modular, typed, tested, deployable |
| G13 | Elegant modern UI (Kanakku-inspired layout language, original product design) |

### 2.2 Non-goals (Release 2)

| ID | Non-goal |
|----|----------|
| NG1 | Open Banking / Account Aggregator APIs |
| NG2 | Friends as logged-in users with debt confirmation (Release 3+) |
| NG3 | SMS or WhatsApp reminders (email only in R2) |
| NG4 | Multi-currency as a first-class product surface (default INR; currency field allowed for future) |
| NG5 | Native mobile apps (installable PWA is optional late R2; native stays later) |
| NG6 | Full double-entry accounting for tax filing / GST returns |
| NG7 | Automatic payment of credit card bills from bank accounts |
| NG8 | Salary / PF / NPS deep modules |
| NG9 | Investments, portfolio, XIRR |
| NG10 | AI agents for insights or auto-parsing to posted ledger |
| NG11 | Silent overwrite of balances without an adjustment event |
| NG12 | Subscription billing / commercial SaaS packaging |

### 2.3 Success criteria (Release 2)

- Owner can manage bank/cash/wallet/card accounts and see net worth without external tools.
- Posted ledger history is correctable only via adjustments/reversals; drafts never affect balances until posted.
- Card utilization separates normal spend from EMI principal blocked on the limit.
- At least one real card EMI cycle and one personal debt can be reconciled end-to-end.
- CSV/Excel/PDF imports cannot affect balances before approval.
- Owner can export core data and request account deletion.
- Email reminders fire for configured due thresholds.
- No full card numbers, CVVs, or PINs are ever stored.

---

## 3. Personas & use cases

### 3.1 Primary persona — Personal finance owner (you)

- Holds multiple credit cards across Indian issuers; may have EMIs on cards
- Uses bank accounts, cash, and UPI/wallets day to day
- Lends cards or money to friends occasionally
- Wants clarity on limits, dues, net worth, and who owes what
- Enters data manually and/or from statement files
- Uses the app as the system of record (not a bank replacement)

### 3.2 Secondary persona (later) — Public multi-user

- Same needs as primary; may share a household workspace later via org memberships
- Adult household members do **not** automatically see each other’s private finances
- **Not required for Release 2 packaging**, but schema/roles continue to support it

### 3.3 Explicit non-persona (Release 2)

- Friends who borrow cards/money: **contacts only**, no login (connected-user confirm in Release 3+)

### 3.4 Core use cases

| ID | Use case | Priority | Status |
|----|----------|----------|--------|
| UC1 | Sign up / sign in (Google, email/password, magic link) | Must | Shipped |
| UC2 | Auto-create personal organization on first login | Must | Shipped |
| UC3 | Add / edit / archive credit cards | Must | Shipped |
| UC4 | Configure statement day and due-date rule per card | Must | Shipped |
| UC5 | View dashboard: limits, utilization, upcoming dues, friend dues | Must | Shipped (expand in R2) |
| UC6 | Add contacts (friends) | Must | Shipped |
| UC7 | Record transactions (purchase, refund, fee, interest, payment to bank) | Must | Shipped (extend types in R2) |
| UC8 | Attribute transaction to a contact (or self) | Must | Shipped |
| UC9 | View contact balance and history | Must | Shipped |
| UC10 | Record settlement (repayment from contact) | Must | Shipped (generalize into obligations in R2) |
| UC11 | Upload statement PDF and review proposed imports | Must | Shipped |
| UC12 | Filter/search transactions | Must | Shipped |
| UC13 | In-app notifications (due soon, parse ready, etc.) | Must | Shipped |
| UC14 | Switch organizations / invite members | Should | Partial |
| UC15 | Bank-specific PDF auto-parse accuracy for all issuers | Later | Open |
| UC16 | External channel reminders (email) | Must (R2) | New |
| UC17 | Manage bank, cash, and wallet accounts | Must (R2) | New |
| UC18 | Correct balance via audited adjustment | Must (R2) | New |
| UC19 | Transfer between accounts | Must (R2) | New |
| UC20 | Categorize, tag, and split transactions | Must (R2) | New |
| UC21 | Create personal debt / loan with partial repayments | Must (R2) | New |
| UC22 | Create credit-card EMI plan and track schedule | Must (R2) | New |
| UC23 | Track GST amounts on spends / reimbursements | Should (R2) | New |
| UC24 | Import CSV / Excel with review before post | Must (R2) | New |
| UC25 | Export data; request account deletion | Must (R2) | New |
| UC26 | View net worth and period income/expense | Must (R2) | New |
| UC27 | Connected-user debt confirm / dispute | Later (R3+) | Deferred |

---

## 4. Functional requirements

### 4.1 Authentication

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-A1 | Google OAuth via Supabase Auth | Must | Shipped |
| FR-A2 | Email auth via Supabase (password + magic link) | Must | Shipped |
| FR-A3 | Phone OTP via Supabase (provider configurable) | Should | Partial / later |
| FR-A4 | Secure session handling (HTTP-only cookies / Supabase session best practices on Next.js) | Must | Shipped |
| FR-A5 | Sign out clears session client + protected routes | Must | Shipped |
| FR-A6 | On first authenticated API access: ensure personal org + owner membership exist | Must | Shipped |
| FR-A7 | Authenticator MFA | Later | Deferred |

### 4.2 Organizations (multi-tenant)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-O1 | Every piece of domain data belongs to an `organization_id` | Must | Shipped |
| FR-O2 | Roles: `owner`, `admin`, `member` | Must | Shipped |
| FR-O3 | Personal org named from user profile on signup | Must | Shipped |
| FR-O4 | All API mutations verify membership | Must | Shipped |
| FR-O5 | Supabase RLS enforces org isolation | Must | Shipped |
| FR-O6 | Org switcher in UI (even if only one org initially) | Should | Partial |
| FR-O7 | Membership in an org/household does **not** by itself grant visibility into another adult’s private financial records; explicit share grants are required for cross-user record access (schema in R2; full UX may land late R2 / R3) | Must (R2 design) | New |

### 4.3 Accounts (Release 2)

Credit cards remain a specialized account type with billing metadata. Release 2 introduces a unified account layer.

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-AC1 | Account kinds: `bank`, `cash`, `wallet`, `credit_card` | Must |
| FR-AC2 | Create/edit/archive accounts with name, currency (default INR), optional institution metadata | Must |
| FR-AC3 | Account balance is always derived from posted ledger entries (never a silently overwritten stored balance) | Must |
| FR-AC4 | Opening balance and “Correct Balance” create explicit `adjustment` events | Must |
| FR-AC5 | Credit-card accounts retain all FR-C* billing fields (or linked 1:1 specialization) | Must |
| FR-AC6 | Soft-archive retains history | Must |

### 4.4 Credit cards (shipped; EMI extensions in R2)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-C1 | Create card with nickname, issuer/bank, network, last 4 digits, credit limit (INR) | Must | Shipped |
| FR-C2 | Never accept or store full PAN, CVV, PIN, or full track data | Must | Shipped |
| FR-C3 | Billing config: statement day-of-month (1–28 recommended, handle 29–31 safely) | Must | Shipped |
| FR-C4 | Due-date rule: either fixed day-of-month **or** N days after statement date | Must | Shipped |
| FR-C5 | Soft-archive / close card (retain history) | Must | Shipped |
| FR-C6 | Display utilization % and available credit | Must | Shipped (extend in R2) |
| FR-C7 | Derive next statement date and next due date in IST | Must | Shipped |
| FR-C8 | Optional: who currently holds physical card (self vs contact) | Should | Shipped / partial |
| FR-C9 | Utilization splits **normal spend outstanding** vs **EMI principal blocked** on the limit | Must (R2) | New |
| FR-C10 | Plain-language explanation of card utilization and EMI block math in UI | Should (R2) | New |

### 4.5 Contacts

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-P1 | CRUD contacts: name (required), phone, email, notes, tags | Must | Shipped |
| FR-P2 | Contacts are not auth users | Must | Shipped |
| FR-P3 | Soft-delete or archive contacts with history retained | Must | Shipped |
| FR-P4 | Contact detail shows running balance and ledger | Must | Shipped |
| FR-P5 | Contacts may be linked to a Fin Buddy user later without exposing historic records by default | Should (R2 schema / R3 UX) | New |

### 4.6 Ledger & transactions

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-T1 | Record transaction types: `purchase`, `refund`, `fee`, `interest`, `payment_to_issuer`, plus R2 types: `income`, `expense`, `transfer`, `adjustment`, `reversal`, `emi_principal`, `emi_interest`, `emi_fee` as needed | Must | Partial → R2 |
| FR-T2 | Fields: amount, currency (default INR), occurred_at, merchant/description, account/card, optional contact_id, category, notes | Must | Shipped (extend) |
| FR-T3 | Amounts stored as integer **paise** (minor units) to avoid float errors | Must | Shipped |
| FR-T4 | `contact_id = null` means spend by the card/account owner (self) | Must | Shipped |
| FR-T5 | List with filters: account/card, contact, date range, type, category, text search | Must | Shipped (extend) |
| FR-T6 | Posted records must not be silently edited/deleted; use reverse or correction entries | Must (R2) | New |
| FR-T7 | Optional link to statement import batch | Should | Shipped |
| FR-T8 | Ledger posting states: `draft` and `posted`; only `posted` affects balances | Must (R2) | New |
| FR-T9 | Imports and AI (future) create drafts/candidates only until user confirms | Must | Shipped for imports |
| FR-T10 | Transfers create paired legs that do **not** inflate income or expense totals | Must (R2) | New |
| FR-T11 | Optional GST amount fields (paise) on applicable lines for reclaim/reimbursement tracking | Should (R2) | New |
| FR-T12 | Split entries: one parent transaction with multiple category/amount lines summing to parent | Must (R2) | New |

### 4.7 Categories & tags

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CAT1 | Org-scoped category taxonomy (system defaults + user-defined) | Must |
| FR-CAT2 | Tags as free-form labels on transactions and obligations | Should |
| FR-CAT3 | Categories classify income vs expense for reporting | Must |

### 4.8 Settlements & obligations (debts / loans)

Existing friend **settlements** remain valid. Release 2 generalizes into first-class obligations.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-S1 | Record settlement: contact, amount, settled_at, method (`upi`, `cash`, `bank_transfer`, `other`), notes | Must | Shipped |
| FR-S2 | Contact outstanding balance decreases by settlement amount | Must | Shipped |
| FR-S3 | Settlements do not automatically create `payment_to_issuer` transactions | Must | Shipped |
| FR-S4 | Optional allocation notes linking settlement to specific spends | Should | Partial |
| FR-OB1 | Obligations: personal debt (I owe / they owe) and institutional loan | Must (R2) | New |
| FR-OB2 | Obligation fields: counterparty (contact or institution name), principal, interest/penalty optional, due dates, status | Must (R2) | New |
| FR-OB3 | Partial repayments with history; remaining balance derived | Must (R2) | New |
| FR-OB4 | Unregistered contacts supported; later user-link without exposing history by default | Must (R2) | New |
| FR-OB5 | Existing card-attributed friend balances continue to reconcile with obligation/settlement model (migration path documented) | Must (R2) | New |

### 4.9 Credit-card EMIs

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-E1 | Create EMI plan linked to a credit card: principal, tenure, interest, fees, start date | Must |
| FR-E2 | Generate installment schedule (due dates + principal/interest/GST/fee breakdown) | Must |
| FR-E3 | Only **principal** blocks available credit limit; interest and GST on interest hit the billing statement when due | Must |
| FR-E4 | Track limit utilized by normal expenses vs EMI principal block separately (see FR-C9) | Must |
| FR-E5 | Support processing fees, GST on EMI interest, and advance payments | Must |
| FR-E6 | Another person may pay an installment (contact attribution / advance allocation) with auditable history | Should |
| FR-E7 | Plain-language calculation explanation available for each plan | Should |

### 4.10 Statements & file import

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-I1 | Upload PDF to private storage; create `Statement` record | Must | Shipped |
| FR-I2 | Statement fields: card, period start/end, statement_date, due_date, status | Must | Shipped |
| FR-I3 | Parse pipeline statuses: `uploaded`, `parsing`, `needs_review`, `imported`, `failed` | Must | Shipped |
| FR-I4 | Human review UI: accept/edit/reject proposed line items before commit | Must | Shipped |
| FR-I5 | Never auto-commit parsed transactions without user confirmation | Must | Shipped |
| FR-I6 | Pluggable parser interface per issuer; generic text extraction fallback | Must | Shipped |
| FR-I7 | Manual transaction entry always available without file import | Must | Shipped |
| FR-I8 | First-class CSV and Excel imports into the same review pipeline | Must (R2) | New |
| FR-I9 | Import errors must not partially post data | Must | Shipped / reinforce |

### 4.11 Dashboard & notifications

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-D1 | KPIs: total credit limit, total outstanding, total available, total friend dues, dues within N days | Must | Shipped |
| FR-D2 | List of cards with utilization bars and next due | Must | Shipped |
| FR-D3 | Upcoming dues calendar/list | Must | Shipped (expand) |
| FR-D4 | Recent activity feed | Must | Shipped |
| FR-D5 | Top contacts by outstanding balance | Must | Shipped |
| FR-D6 | Net worth = assets (bank/cash/wallet) − liabilities (card outstanding + debts + loans + EMI remaining as defined) | Must (R2) | New |
| FR-D7 | Period income and expense totals (transfers excluded) | Must (R2) | New |
| FR-D8 | Upcoming items include card dues, debt dues, and EMI installments | Must (R2) | New |
| FR-N1 | In-app notifications for: due soon, overdue, high utilization, statement ready for review | Must | Shipped |
| FR-N2 | Mark notification read / read-all | Must | Shipped |
| FR-N3 | Email reminders for due soon / overdue (configurable threshold) | Must (R2) | New |
| FR-N4 | SMS / WhatsApp | Later | Deferred |

### 4.12 Settings, export, deletion

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-Z1 | Profile display name, avatar (from auth provider when available) | Must | Shipped |
| FR-Z2 | Org name edit | Should | Shipped / partial |
| FR-Z3 | In-app notification preference thresholds (e.g. due in 3/5/7 days) | Should | Partial → R2 |
| FR-Z4 | Email reminder preferences (enable/disable, threshold days) | Must (R2) | New |
| FR-Z5 | Export org financial data to Excel and/or PDF | Must (R2) | New |
| FR-Z6 | Request permanent account deletion (cascade/anonymize per policy; confirm UX) | Must (R2) | New |

### 4.13 Record sharing (schema readiness)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-SH1 | Schema supports explicit record-share grants: grantor, recipient, record type, record id, permission, created_at, revoked_at | Should (R2) |
| FR-SH2 | Connections/household membership alone never authorize financial visibility | Must (design) |
| FR-SH3 | Full share/unshare UX and connected-user debt confirm | Later (R3+) |

---

## 5. User flows

### 5.1 First-time onboarding (shipped)

1. User lands on marketing/login page.
2. Signs in with Google, email password, or magic link.
3. Backend ensures personal organization + owner membership.
4. Empty-state dashboard with CTAs: **Add card**, **Add contact** (R2 also: **Add account**).
5. Optional short checklist (dismissible).

### 5.2 Add card and configure cycle (shipped)

1. Cards → Add card.
2. Enter nickname, issuer, network, last 4, limit.
3. Set statement day + due rule.
4. Save → card appears on dashboard with next statement/due computed.

### 5.3 Record spend for a friend (shipped)

1. Transactions → Add (or quick action from dashboard).
2. Select card/account, amount, merchant, date/time.
3. Select contact (friend).
4. Save (post) → contact balance increases; card/account outstanding updates.

### 5.4 Record repayment (shipped; extends to obligations in R2)

1. Contact detail → Record settlement (or obligation repayment).
2. Enter amount, method (e.g. UPI), date.
3. Save → contact/obligation balance decreases; activity logged.

### 5.5 Statement / file import (shipped PDF; R2 CSV/Excel)

1. Statements → Upload PDF, CSV, or Excel.
2. System stores file; parse job runs; candidates enter review.
3. User corrects rows, assigns contacts/categories if needed.
4. Confirm import → transactions posted; import status `imported`.

### 5.6 Due-date check (shipped; expands in R2)

1. User opens dashboard / notifications.
2. Sees cards, debts, and EMIs due within threshold.
3. Optionally records `payment_to_issuer` or obligation repayment.
4. Email reminder may have been sent per preferences.

### 5.7 Correct balance (Release 2)

1. Account detail → Correct balance.
2. Enter target balance and reason.
3. System posts an `adjustment` for the delta; history remains intact.

### 5.8 Create credit-card EMI (Release 2)

1. Card detail → Add EMI.
2. Enter principal, tenure, rate/fees; review generated schedule and principal block impact.
3. Confirm → schedule created; available credit reflects principal block.
4. On billing dates, interest/GST lines appear per plan rules (draft or posted per product choice; default: system-proposed draft for review if imported, else scheduled posted events with clear type).

### 5.9 Data export / deletion (Release 2)

1. Settings → Export data → download Excel/PDF package.
2. Settings → Delete account → confirm → deletion request processed per policy.

---

## 6. Information architecture & screens

### 6.1 Public / auth

- `/` — landing (can be minimal for personal phase)
- `/login`, `/signup`, `/auth/callback` — auth flows

### 6.2 Authenticated app shell

Inspired by Kanakku (sidebar + header + content), not a visual clone:

| Route | Screen | Status |
|-------|--------|--------|
| `/app` | Dashboard | Shipped (expand KPIs) |
| `/app/accounts` | Accounts list (bank/cash/wallet) | R2 |
| `/app/accounts/[id]` | Account detail | R2 |
| `/app/cards` | Cards list | Shipped |
| `/app/cards/[id]` | Card detail (+ EMI section) | Shipped / R2 EMI |
| `/app/contacts` | Contacts list | Shipped |
| `/app/contacts/[id]` | Contact detail | Shipped |
| `/app/transactions` | Transactions ledger | Shipped |
| `/app/debts` | Debts & loans | R2 |
| `/app/debts/[id]` | Obligation detail | R2 |
| `/app/emis` | EMI plans list (optional; also on card) | R2 |
| `/app/statements` | Statements / imports | Shipped |
| `/app/statements/[id]/review` | Import review | Shipped |
| `/app/notifications` | Notification center | Shipped |
| `/app/settings` | Settings, export, deletion, reminder prefs | Shipped / R2 |

### 6.3 UI principles

- Production finance-admin aesthetic: dense but calm, clear hierarchy, strong empty states
- Dark mode first-class
- shadcn/ui for primitives; Aceternity UI sparingly for high-impact visual moments
- Responsive: desktop-first, usable tablet; mobile acceptable for dashboards/lists
- Accessibility: keyboard navigable core flows, sufficient contrast
- Optional late-R2: installable PWA shell (offline not required)

---

## 7. Data model

### 7.1 Entity relationship (logical)

```text
auth.users (Supabase)
    │
    ▼
profiles ──────────────────────────────┐
    │                                  │
    ▼                                  │
organization_members ──► organizations ◄── all domain tables via organization_id
                              │
     ┌───────────┬────────────┼──────────────┬──────────────┐
     ▼           ▼            ▼              ▼              ▼
  contacts    accounts    categories    obligations    settlements
                 │            │              │
                 │            └──── splits ──┘
                 │
       ┌─────────┼──────────┬────────────┐
       ▼         ▼          ▼            ▼
 credit_cards  ledger    statements    emi_plans
  (specialization) entries               │
       │              │                  ▼
       └──────────────┴────────── emi_installments
                              │
                              ▼
                     in_app_notifications
                     record_shares (R2 schema)
```

### 7.2 Core tables (conceptual)

#### Existing (v1) — retained

`profiles`, `organizations`, `organization_members`, `contacts`, `credit_cards`, `transactions`, `settlements`, `statements`, `statement_line_candidates`, `in_app_notifications` — as in v1.0, with R2 columns added where noted.

#### `accounts` (R2)

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| kind | enum | bank, cash, wallet, credit_card |
| name | text | |
| institution | text nullable | bank/wallet name |
| currency | char(3) | default INR |
| credit_card_id | uuid nullable | set when kind = credit_card |
| archived_at | timestamptz nullable | |
| created_at / updated_at | timestamptz | |

#### Ledger posting (R2 evolution of `transactions`)

| Column / concept | Notes |
|------------------|-------|
| posting_status | `draft` \| `posted` |
| reversed_by_id / reverses_id | optional links for reversals |
| account_id | FK to accounts (card txs also resolve via credit_card account) |
| gst_paise | nullable; GST portion when tracked |
| transfer_group_id | uuid nullable; pairs transfer legs |
| category_id | uuid nullable |

#### `categories` (R2)

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| name | text | |
| kind | enum | income, expense, transfer, system |
| parent_id | uuid nullable | optional hierarchy |
| archived_at | timestamptz nullable | |

#### `transaction_splits` (R2)

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| transaction_id | uuid FK | |
| category_id | uuid nullable | |
| amount_paise | bigint | |
| notes | text nullable | |

#### `obligations` (R2)

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| kind | enum | personal_debt, institutional_loan |
| direction | enum | receivable, payable |
| contact_id | uuid nullable | |
| counterparty_name | text nullable | when no contact |
| principal_paise | bigint | |
| currency | char(3) | |
| interest_paise | bigint nullable | accrued/agreed |
| due_at | timestamptz nullable | |
| status | enum | open, settled, written_off |
| notes | text nullable | |
| created_at / updated_at | timestamptz | |

#### `obligation_payments` (R2)

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| obligation_id | uuid FK | |
| amount_paise | bigint | |
| paid_at | timestamptz | |
| method | enum | upi, cash, bank_transfer, other |
| notes | text nullable | |
| ledger_transaction_id | uuid nullable | optional link |

#### `emi_plans` / `emi_installments` (R2)

| Concept | Notes |
|---------|-------|
| Plan | card_id, principal_paise, tenure_months, interest fields, fee fields, status |
| Installment | due_date, principal_paise, interest_paise, gst_paise, fee_paise, status, paid_at, paid_by_contact_id |

#### `record_shares` (R2 schema readiness)

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| grantor_user_id | uuid | |
| recipient_user_id | uuid | |
| record_type | text | |
| record_id | uuid | |
| permission | text | read / write |
| created_at | timestamptz | |
| revoked_at | timestamptz nullable | |

### 7.3 Money representation

- All money values: **integer paise** (`bigint`)
- Display layer formats with `Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })`
- Never use floating point for ledger math
- API may expose decimal strings for display convenience, but storage and domain math stay integer paise

---

## 8. Business rules

### 8.1 Card outstanding balance (v1 retained)

Define **card spend outstanding** as the tracked liability still owed to the issuer from non-EMI activity:

```text
spend_outstanding = sum(effect of non-EMI transactions on card)
```

Suggested effect by type:

| Type | Effect on spend outstanding |
|------|----------------------------|
| `purchase` | +amount |
| `fee` | +amount |
| `interest` | +amount |
| `refund` | −amount |
| `payment_to_issuer` | −amount (allocated per product rules; document if EMI-aware) |

### 8.2 EMI principal block (R2)

```text
emi_principal_blocked = sum(remaining principal on active EMI plans for card)
available_credit = max(credit_limit − spend_outstanding − emi_principal_blocked, 0)
utilization_spend = spend_outstanding / credit_limit
utilization_emi = emi_principal_blocked / credit_limit
utilization_total = (spend_outstanding + emi_principal_blocked) / credit_limit
```

Interest and GST on EMI interest affect the **billing statement** when due; they do **not** increase the principal block.

### 8.3 Contact outstanding balance (v1 retained; reconcile with obligations)

```text
contact_balance =
    sum(purchases + fees attributed to contact)
  − sum(refunds attributed to contact)
  − sum(settlements for contact)
  ± obligation effects where contact is counterparty
```

- `payment_to_issuer` never affects contact balances.
- Interest attributed to a contact is optional; default interest to self unless user attributes it.

### 8.4 Statement date computation (IST)

Given `statement_day = D` and today in `Asia/Kolkata`:

- Next statement date = next calendar date with day `D`, clamping to month length (e.g. day 31 → last day of month).
- Previous statement date = previous such date.

### 8.5 Due date computation

| Rule | Computation |
|------|-------------|
| `fixed_day` + value `V` | Next occurrence of day `V` on or after statement date (product rule: typically due date in the following cycle window; exact algorithm documented in domain code with unit tests) |
| `days_after_statement` + `N` | `statement_date + N days` |

Implementation must unit-test edge cases: month ends, leap years, statement on 31st.

### 8.6 Settlement / obligation constraints

- Settlement/repayment amount must be > 0
- Overpayment → negative balance / credit with contact; UI should warn but allow (configurable later)

### 8.7 PDF / CSV / Excel import

- Candidates start as `pending`
- Only `accepted` / `edited` rows create posted `transactions` on confirm
- Idempotent confirm: re-confirm does not duplicate committed rows
- Failures do not partially post

### 8.8 Draft vs posted

- Draft rows do not affect account, card, contact, or obligation balances
- Posting is explicit (manual save-as-posted, or import confirm)
- Posted rows: correct via `adjustment` or `reversal` linked to original

### 8.9 Transfers

- Transfer is two legs (or one group) with equal amounts
- Excluded from income and expense period totals

### 8.10 Net worth (R2)

```text
assets = sum(positive balances of bank + cash + wallet)
liabilities = card spend outstanding + emi remaining principal
            + payable obligations remaining
            − receivable obligations remaining (or show receivables under assets — pick one definition and document in UI)
```

Product default: receivables count as assets; payables and card/EMI liabilities count as liabilities.

---

## 9. Auth & multi-tenancy

### 9.1 Auth provider: Supabase Auth

- Google OAuth
- Email password + magic link
- Phone OTP (SMS provider required; may ship after Google+email)
- MFA later

### 9.2 API auth

- Frontend obtains Supabase session JWT
- FastAPI validates JWT (JWKS / secret per Supabase config)
- Request context includes `user_id` and active `organization_id`
- Membership check on every org-scoped operation
- API never trusts a caller user ID from the request body as identity

### 9.3 Defense in depth

1. FastAPI authorization layer  
2. Supabase RLS policies on all tenant tables  
3. Storage policies for private statement files  

### 9.4 Personal workspace bootstrap

On first authenticated request (or auth webhook):

1. Create `profiles` row if missing  
2. If user has zero memberships → create organization + owner membership  

### 9.5 Privacy principle (R2+)

Zero-trust default for multi-user: everyone sees only their finances unless an explicit share grant says otherwise. Org membership alone is not a blanket finance browse permission across adults.

---

## 10. Integrations

| System | Role |
|--------|------|
| **Supabase Auth** | Identity providers & sessions |
| **Supabase Postgres** | System of record |
| **Supabase Storage** | Private statement / import files |
| **FastAPI** | Business logic, import pipeline, computed APIs |
| **Vercel** | Frontend hosting |
| **FastAPI Cloud** | Backend hosting |
| **Email provider** (R2) | Due reminders (via Supabase or transactional email) |

### 10.1 File parsing

- Pluggable `StatementParser` / `ImportParser` interface: `detect(format/issuer) → parse(bytes) → list[LineCandidate]`
- Background execution interface ready for queue (can start with in-process async for personal scale)
- Human review mandatory before ledger commit

---

## 11. Non-functional requirements

### 11.1 Security

- No full PAN/CVV/PIN storage
- Secrets only in server env / platform secret stores
- HTTPS everywhere in deployed environments
- CORS locked to known frontend origins
- Rate limiting on auth-sensitive and upload endpoints (platform or app level)

### 11.2 Performance

- Dashboard API p95 < 500ms for personal-scale data (≤ 50 cards, ≤ 50k transactions target design)
- Paginated lists (default page size 25–50)
- Indexes on `(organization_id, occurred_at)`, FKs, membership lookups

### 11.3 Reliability

- Structured logging (JSON) on API
- Health endpoint for deploy probes
- Graceful validation errors (RFC7807-style problem details preferred)

### 11.4 Observability

- Request IDs
- Error tracking hook points (Sentry optional later)

### 11.5 Accessibility & i18n

- Core flows keyboard accessible
- Copy in English; amounts/dates in `en-IN` / IST
- Full i18n framework not required in Release 2

### 11.6 Quality bar

- TypeScript strict mode (frontend)
- Pydantic models + mypy/pyright (backend)
- Unit tests for domain math (balances, billing dates, EMI principal block, transfer exclusion)
- API tests for authz happy/sad paths
- Lint: ESLint + Ruff

---

## 12. Tech stack & deployment

| Layer | Choice |
|-------|--------|
| Frontend | Next.js (App Router), TypeScript, Tailwind, shadcn/ui, Aceternity UI (selected components) |
| Backend | FastAPI, Python 3.12+ (uv managed), layered architecture |
| DB / Auth / Storage | Supabase |
| Frontend deploy | Vercel |
| Backend deploy | FastAPI Cloud |
| Primary market | India, INR, IST |

### 12.1 Repository layout

```text
fin-buddy/
  docs/prd/
  frontend/
  backend/
  README.md
```

One git repository; two top-level apps without monorepo tooling. Do **not** rewrite onto Angular/Nest/Prisma.

---

## 13. Risks & open questions

### 13.1 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| PDF/CSV/Excel formats differ by issuer | Failed imports | Review UI + pluggable parsers; manual entry always works |
| EMI math misunderstood by users | Wrong available credit | Plain-language explanations + unit tests + UI split of spend vs EMI block |
| Migrating settlements → obligations | Double-counting friend dues | Explicit migration plan and reconciliation tests |
| Auditable ledger retrofit on edit/delete MVP | Data migration pain | Mark existing rows posted; soft-lock edits behind reversal path |
| Email reminder deliverability | Missed dues | Prefer transactional provider; keep in-app notifications primary |
| Scope creep into salary/investments/AI | Delayed R2 | Hard non-goals; Release 3+ only |
| Multi-tenant overbuild | Slow delivery | Simple personal UX; org + share schema under the hood |

### 13.2 Open questions (resolve during R2 build)

1. Exact migration path: keep `settlements` table forever vs fold into `obligation_payments`.  
2. Whether EMI interest lines auto-post on statement date or require confirmation.  
3. Net-worth treatment of receivables (asset vs contra-liability) — default: asset.  
4. Which 1–2 issuers for first improved PDF parsers?  
5. Email provider choice (Supabase native vs Resend/SES).  
6. Whether overpayment to a contact remains warn-and-allow (yes for R2).  

---

## 14. Phased roadmap

| Phase | Scope | Outcome |
|-------|--------|---------|
| **0** | PRD + frontend/backend scaffold + README | **Done** |
| **1** | Auth + org bootstrap + app shell | **Done** |
| **2** | Cards + billing cycle math + dashboard KPIs | **Done** |
| **3** | Contacts + transactions + settlements | **Done** |
| **4** | Statement PDF upload + review + first parsers | **Done** |
| **5** | Polish, empty states, deploy personal prod | **Done** |
| **Release 2** | Accounts, auditable ledger, categories/transfers/splits, debts/loans, card EMIs + GST tracking, CSV/Excel import, net-worth dashboard, export/deletion, email reminders, share schema readiness | Expanded personal finance daily driver |
| **Release 3+** | Connected-user debt confirm, fine-grained share UX, PWA polish, salary/investments, Account Aggregators, AI review, commercial packaging | Wider audience |

Detailed Release 2 implementation backlog: [`RELEASE-2-TASKS.md`](RELEASE-2-TASKS.md).  
User stories (US-01…US-06): [`release-2/README.md`](release-2/README.md). Ralph loop prompt: [`release-2/RALPH-LOOP-PROMPT.md`](release-2/RALPH-LOOP-PROMPT.md).

---

## 15. Acceptance criteria

### 15.1 v1 personal daily driver (shipped)

1. User can sign in with at least Google and email.  
2. User can CRUD cards with limits and cycle config; next statement/due are correct for configured rules (covered by tests).  
3. User can CRUD contacts and transactions; contact balances match the business rules above.  
4. User can record settlements and see balances update.  
5. User can upload a statement PDF and complete a review import without duplicate posts.  
6. Dashboard shows utilization and upcoming dues.  
7. In-app notifications surface due-soon and import-ready events.  
8. No secrets in client bundles; no full card numbers stored.  
9. Frontend deploys to Vercel; backend to FastAPI Cloud; data in Supabase.  
10. CI-ready lint/typecheck/test scripts pass on main paths.

### 15.2 Release 2 acceptance

1. User can CRUD bank/cash/wallet accounts; balances derive from posted ledger only.  
2. Correct Balance creates an adjustment; posted history cannot be silently overwritten.  
3. Transfers do not inflate income/expense totals.  
4. User can create a personal debt/loan, record partial repayments, and see remaining balance.  
5. User can create a card EMI; available credit reflects principal block separately from spend.  
6. Optional GST amounts can be stored on applicable lines.  
7. CSV and Excel imports go through review and never auto-post.  
8. Dashboard shows net worth, period income/expense, and upcoming card/debt/EMI items.  
9. User can export data and request account deletion.  
10. Email reminders respect preference thresholds for due soon/overdue.  
11. Domain unit tests cover EMI block math, transfer exclusion, and adjustment rules.

---

## 16. Appendix — glossary

| Term | Meaning |
|------|---------|
| **Account** | Bank, cash, wallet, or credit-card container whose balance derives from the ledger |
| **Statement date** | Date issuer generates the billing statement |
| **Due date** | Date payment to issuer (or obligation) is due |
| **Contact** | Person who may use a lent card or be a debt counterparty; not an app user in R2 |
| **Settlement** | Money a contact pays back to the owner (v1 concept; aligns with obligation payments) |
| **Obligation** | First-class personal debt or institutional loan |
| **EMI** | Equated monthly installment plan, often on a credit card |
| **Principal block** | Remaining EMI principal that reduces available credit limit |
| **Payment to issuer** | Money the owner pays the bank toward the card bill |
| **Outstanding (card spend)** | Tracked non-EMI amount still owed to the issuer |
| **Outstanding (contact)** | Tracked amount the contact still owes the owner |
| **Draft** | Ledger row that does not yet affect balances |
| **Posted** | Ledger row that affects balances |
| **Adjustment** | Explicit correction event that changes balance without silent edit |
| **Paise** | 1/100 of one INR; storage unit for money |

---

## 17. Document history

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-07-27 | Initial PRD from discovery decisions |
| 2.0 | 2026-08-05 | Expand to personal-finance scope; absorb best ideas from peer FINANCY BRD/PRD (accounts, auditable ledger, debts/loans, card EMIs, GST tracking, CSV/Excel import, net worth, export/deletion, email reminders). Phases 0–5 marked shipped. Release 2 backlog added. |
