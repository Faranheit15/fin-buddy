# Fin Buddy — Product Requirements Document

| Field | Value |
|--------|--------|
| **Document version** | 1.0 |
| **Date** | 2026-07-27 |
| **Status** | Draft — approved for Phase 0 scaffold |
| **Owner** | Product / Engineering |
| **Audience** | Personal use first; public multi-user release later |

---

## 1. Overview & problem statement

### 1.1 Product name

**Fin Buddy**

### 1.2 One-liner

Fin Buddy is a production-grade credit card and friend-lending ledger for people who juggle multiple cards, billing cycles, and shared spend — starting with India (INR).

### 1.3 Problem

Card holders often manage many credit cards with different:

- Credit limits and utilization
- Statement generation dates
- Payment due dates
- Billing cycle conventions

On top of that, cards are sometimes lent to friends. Without a dedicated system it is hard to answer:

1. How much available credit remains on each card?
2. When is the next statement date and payment due date?
3. Who spent what, on which card, and when?
4. How much does each friend still owe?

Spreadsheets and bank apps do not combine **card inventory**, **billing calendar**, and **person-attributed spend + settlements** in one place.

### 1.4 Solution

A web application with a modern finance-admin UI where the owner:

- Registers credit cards (metadata only — never full PAN/CVV)
- Tracks statement and due dates from billing configuration
- Records a full spend ledger with attribution to contacts (friends)
- Tracks running balances and records repayments
- Optionally uploads statement PDFs for assisted import (human review before commit)
- Sees an in-app dashboard of utilization, dues, and friend outstanding balances

### 1.5 Target user journey over time

| Stage | Audience | Implication |
|--------|----------|-------------|
| **Now** | Single power user (you) | Ship daily-driver quality; multi-tenant schema ready |
| **Later** | Wider public audience | Same core product; packaging, onboarding, billing as needed |

---

## 2. Goals & non-goals

### 2.1 Goals (v1)

| ID | Goal |
|----|------|
| G1 | Single source of truth for cards, cycles, spends, and friend dues |
| G2 | Full spend ledger with contact attribution |
| G3 | Contact balances and repayment tracking |
| G4 | Clear next statement / next due dates per card |
| G5 | Manual transaction entry + statement PDF upload with review |
| G6 | Multi-tenant org model from day one (personal workspace auto-created) |
| G7 | Production-grade code: modular, typed, tested, deployable |
| G8 | Elegant modern UI (Kanakku-inspired layout language, original product design) |

### 2.2 Non-goals (v1)

| ID | Non-goal |
|----|----------|
| NG1 | Open Banking / bank account aggregation APIs |
| NG2 | Friends as logged-in users or self-service spend confirmation |
| NG3 | Email, SMS, or WhatsApp reminders |
| NG4 | Multi-currency as a first-class product surface (default INR; currency field allowed for future) |
| NG5 | Native mobile apps |
| NG6 | Full double-entry accounting / tax filing / GST modules |
| NG7 | Automatic payment of credit card bills from bank accounts |

### 2.3 Success criteria

- Owner can manage all personal cards and see upcoming dues without external tools.
- Every spend can be attributed; each contact shows an accurate outstanding balance.
- Codebase has clear module boundaries, automated tests for core domain rules, lint/typecheck, and deploy configs suitable for Vercel + FastAPI Cloud + Supabase.
- No full card numbers, CVVs, or PINs are ever stored.

---

## 3. Personas & use cases

### 3.1 Primary persona — Card owner (you)

- Holds multiple credit cards across Indian issuers
- Lends cards to friends occasionally
- Wants clarity on limits, dues, and who owes what
- Enters data manually and/or from statement PDFs
- Uses the app as the system of record (not a bank replacement)

### 3.2 Secondary persona (later) — Public multi-user

- Same needs as primary; may share a household workspace later via org memberships
- **Not in v1 product packaging**, but schema/roles support it

### 3.3 Explicit non-persona (v1)

- Friends who borrow cards: **contacts only**, no login

### 3.4 Core use cases

| ID | Use case | Priority |
|----|----------|----------|
| UC1 | Sign up / sign in (Google, email, phone) | Must |
| UC2 | Auto-create personal organization on first login | Must |
| UC3 | Add / edit / archive credit cards | Must |
| UC4 | Configure statement day and due-date rule per card | Must |
| UC5 | View dashboard: limits, utilization, upcoming dues, friend dues | Must |
| UC6 | Add contacts (friends) | Must |
| UC7 | Record transactions (purchase, refund, fee, interest, payment to bank) | Must |
| UC8 | Attribute transaction to a contact (or self) | Must |
| UC9 | View contact balance and history | Must |
| UC10 | Record settlement (repayment from contact) | Must |
| UC11 | Upload statement PDF and review proposed imports | Must |
| UC12 | Filter/search transactions | Must |
| UC13 | In-app notifications (due soon, parse ready, etc.) | Must |
| UC14 | Switch organizations / invite members | Should (schema + basic; polish later) |
| UC15 | Bank-specific PDF auto-parse accuracy for all issuers | Later |
| UC16 | External channel reminders | Later |

---

## 4. Functional requirements

### 4.1 Authentication

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-A1 | Google OAuth via Supabase Auth | Must |
| FR-A2 | Email auth via Supabase (magic link as primary for v1) | Must |
| FR-A3 | Phone OTP via Supabase (provider configurable; may ship after Google+email if SMS cost/setup blocks) | Should |
| FR-A4 | Secure session handling (HTTP-only cookies / Supabase session best practices on Next.js) | Must |
| FR-A5 | Sign out clears session client + protected routes | Must |
| FR-A6 | On first authenticated API access: ensure personal org + owner membership exist | Must |

### 4.2 Organizations (multi-tenant)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-O1 | Every piece of domain data belongs to an `organization_id` | Must |
| FR-O2 | Roles: `owner`, `admin`, `member` | Must |
| FR-O3 | Personal org named from user profile on signup | Must |
| FR-O4 | All API mutations verify membership | Must |
| FR-O5 | Supabase RLS enforces org isolation | Must |
| FR-O6 | Org switcher in UI (even if only one org initially) | Should |

### 4.3 Credit cards

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-C1 | Create card with nickname, issuer/bank, network, last 4 digits, credit limit (INR) | Must |
| FR-C2 | Never accept or store full PAN, CVV, PIN, or full track data | Must |
| FR-C3 | Billing config: statement day-of-month (1–28 recommended, handle 29–31 safely) | Must |
| FR-C4 | Due-date rule: either fixed day-of-month **or** N days after statement date | Must |
| FR-C5 | Soft-archive / close card (retain history) | Must |
| FR-C6 | Display utilization % and available credit | Must |
| FR-C7 | Derive next statement date and next due date in IST | Must |
| FR-C8 | Optional: who currently holds physical card (self vs contact) | Should |

### 4.4 Contacts

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-P1 | CRUD contacts: name (required), phone, email, notes, tags | Must |
| FR-P2 | Contacts are not auth users | Must |
| FR-P3 | Soft-delete or archive contacts with history retained | Must |
| FR-P4 | Contact detail shows running balance and ledger | Must |

### 4.5 Transactions (ledger)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-T1 | Record transaction types: `purchase`, `refund`, `fee`, `interest`, `payment_to_issuer` | Must |
| FR-T2 | Fields: amount, currency (default INR), occurred_at, merchant/description, card_id, optional contact_id, category, notes | Must |
| FR-T3 | Amounts stored as integer **paise** (minor units) to avoid float errors | Must |
| FR-T4 | `contact_id = null` means spend by the card owner (self) | Must |
| FR-T5 | List with filters: card, contact, date range, type, category, text search | Must |
| FR-T6 | Edit/delete with audit-friendly constraints (prefer reverse entries for settled history later if needed; v1 allows edit/delete with org membership) | Must |
| FR-T7 | Optional link to statement import batch | Should |

### 4.6 Settlements (repayments)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-S1 | Record settlement: contact, amount, settled_at, method (`upi`, `cash`, `bank_transfer`, `other`), notes | Must |
| FR-S2 | Contact outstanding balance decreases by settlement amount | Must |
| FR-S3 | Settlements do not automatically create `payment_to_issuer` transactions (different concepts) | Must |
| FR-S4 | Optional allocation notes linking settlement to specific spends (simple note/link list OK in v1) | Should |

### 4.7 Statements & PDF import

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-I1 | Upload PDF to private storage; create `Statement` record | Must |
| FR-I2 | Statement fields: card, period start/end, statement_date, due_date, status | Must |
| FR-I3 | Parse pipeline statuses: `uploaded`, `parsing`, `needs_review`, `imported`, `failed` | Must |
| FR-I4 | Human review UI: accept/edit/reject proposed line items before commit | Must |
| FR-I5 | Never auto-commit parsed transactions without user confirmation | Must |
| FR-I6 | Pluggable parser interface per issuer; generic text extraction fallback | Must |
| FR-I7 | Manual transaction entry always available without PDF | Must |

### 4.8 Dashboard & notifications

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-D1 | KPIs: total credit limit, total outstanding, total available, total friend dues, dues within N days | Must |
| FR-D2 | List of cards with utilization bars and next due | Must |
| FR-D3 | Upcoming dues calendar/list | Must |
| FR-D4 | Recent activity feed | Must |
| FR-D5 | Top contacts by outstanding balance | Must |
| FR-N1 | In-app notifications for: due soon, overdue, high utilization, statement ready for review | Must |
| FR-N2 | Mark notification read / read-all | Must |
| FR-N3 | External channels (email/SMS) | Later |

### 4.9 Settings

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-Z1 | Profile display name, avatar (from auth provider when available) | Must |
| FR-Z2 | Org name edit | Should |
| FR-Z3 | In-app notification preference thresholds (e.g. due in 3/5/7 days) | Should |

---

## 5. User flows

### 5.1 First-time onboarding

1. User lands on marketing/login page.
2. Signs in with Google, email magic link, or phone OTP.
3. Backend ensures personal organization + owner membership.
4. Empty-state dashboard with CTAs: **Add card**, **Add contact**.
5. Optional short checklist (dismissible).

### 5.2 Add card and configure cycle

1. Cards → Add card.
2. Enter nickname, issuer, network, last 4, limit.
3. Set statement day + due rule.
4. Save → card appears on dashboard with next statement/due computed.

### 5.3 Record spend for a friend

1. Transactions → Add (or quick action from dashboard).
2. Select card, amount, merchant, date/time.
3. Select contact (friend).
4. Save → contact balance increases; card outstanding updates.

### 5.4 Record repayment

1. Contact detail → Record settlement.
2. Enter amount, method (e.g. UPI), date.
3. Save → contact balance decreases; activity logged.

### 5.5 Statement PDF import

1. Card detail → Statements → Upload PDF.
2. System stores file; parse job runs.
3. User opens review screen, corrects rows, assigns contacts if needed.
4. Confirm import → transactions committed; statement status `imported`.

### 5.6 Due-date check

1. User opens dashboard / notifications.
2. Sees cards due within threshold and outstanding amounts.
3. Optionally records `payment_to_issuer` when bill is paid to the bank.

---

## 6. Information architecture & screens

### 6.1 Public / auth

- `/` — landing (can be minimal for personal phase)
- `/login`, `/auth/callback` — auth flows

### 6.2 Authenticated app shell

Inspired by Kanakku (sidebar + header + content), not a visual clone:

| Route | Screen |
|-------|--------|
| `/app` | Dashboard |
| `/app/cards` | Cards list |
| `/app/cards/[id]` | Card detail |
| `/app/contacts` | Contacts list |
| `/app/contacts/[id]` | Contact detail |
| `/app/transactions` | Transactions ledger |
| `/app/statements` | Statements / imports |
| `/app/statements/[id]/review` | Import review |
| `/app/notifications` | Notification center |
| `/app/settings` | Settings |

### 6.3 UI principles

- Production finance-admin aesthetic: dense but calm, clear hierarchy, strong empty states
- Dark mode first-class
- shadcn/ui for primitives; Aceternity UI sparingly for high-impact visual moments
- Responsive: desktop-first, usable tablet; mobile acceptable for dashboards/lists
- Accessibility: keyboard navigable core flows, sufficient contrast

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
          ┌───────────────────┼────────────────────┐
          ▼                   ▼                    ▼
       contacts          credit_cards        settlements
                              │
                    ┌─────────┼──────────┐
                    ▼         ▼          ▼
              transactions  statements  (billing fields on card)
                    │              │
                    └──────────────┘ (optional statement_id on tx)
                              │
                              ▼
                     in_app_notifications
```

### 7.2 Core tables (conceptual)

#### `profiles`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | = auth.users.id |
| display_name | text | |
| avatar_url | text nullable | |
| timezone | text | default `Asia/Kolkata` |
| created_at / updated_at | timestamptz | |

#### `organizations`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| name | text | |
| slug | text unique | |
| created_at / updated_at | timestamptz | |

#### `organization_members`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| user_id | uuid FK | |
| role | enum | owner, admin, member |
| unique(organization_id, user_id) | | |

#### `contacts`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| name | text | |
| phone | text nullable | E.164 preferred |
| email | text nullable | |
| notes | text nullable | |
| tags | text[] | optional |
| archived_at | timestamptz nullable | |
| created_at / updated_at | timestamptz | |

#### `credit_cards`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| nickname | text | e.g. "HDFC Regalia" |
| issuer | text | bank/issuer name |
| network | text | Visa/Mastercard/RuPay/Amex |
| last_four | char(4) | only |
| credit_limit_paise | bigint | |
| currency | char(3) | default `INR` |
| statement_day | int | 1–31 |
| due_rule_type | enum | `fixed_day` \| `days_after_statement` |
| due_rule_value | int | day-of-month or N days |
| status | enum | `active` \| `closed` |
| held_by_contact_id | uuid nullable | physical card holder |
| notes | text nullable | |
| created_at / updated_at | timestamptz | |

#### `transactions`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| credit_card_id | uuid FK | |
| contact_id | uuid nullable | null = self |
| statement_id | uuid nullable | |
| type | enum | see FR-T1 |
| amount_paise | bigint | always positive; sign/effect by type |
| currency | char(3) | default INR |
| occurred_at | timestamptz | |
| merchant | text | |
| category | text nullable | |
| notes | text nullable | |
| created_at / updated_at | timestamptz | |
| created_by | uuid nullable | auth user |

#### `settlements`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| contact_id | uuid FK | |
| amount_paise | bigint | |
| currency | char(3) | |
| settled_at | timestamptz | |
| method | enum | upi, cash, bank_transfer, other |
| notes | text nullable | |
| created_at / updated_at | timestamptz | |
| created_by | uuid nullable | |

#### `statements`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| credit_card_id | uuid FK | |
| period_start | date | |
| period_end | date | |
| statement_date | date | |
| due_date | date nullable | |
| pdf_storage_path | text nullable | |
| status | enum | uploaded, parsing, needs_review, imported, failed |
| parse_error | text nullable | |
| created_at / updated_at | timestamptz | |

#### `statement_line_candidates` (import review)

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| statement_id | uuid FK | |
| raw_payload | jsonb | parser output |
| occurred_at | timestamptz | |
| merchant | text | |
| amount_paise | bigint | |
| proposed_type | enum | |
| proposed_contact_id | uuid nullable | |
| review_status | enum | pending, accepted, rejected, edited |
| committed_transaction_id | uuid nullable | |

#### `in_app_notifications`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| organization_id | uuid FK | |
| user_id | uuid FK | recipient |
| type | text | |
| title | text | |
| body | text | |
| href | text nullable | |
| read_at | timestamptz nullable | |
| created_at | timestamptz | |

### 7.3 Money representation

- All money values: **integer paise** (`bigint`)
- Display layer formats with `Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })`
- Never use floating point for ledger math

---

## 8. Business rules

### 8.1 Card outstanding balance

Define **card outstanding** as the tracked liability still owed to the issuer:

```text
outstanding = sum(effect of transactions on card)
```

Suggested effect by type (v1):

| Type | Effect on card outstanding |
|------|----------------------------|
| `purchase` | +amount |
| `fee` | +amount |
| `interest` | +amount |
| `refund` | −amount |
| `payment_to_issuer` | −amount |

```text
available_credit = max(credit_limit − outstanding, 0)
utilization = outstanding / credit_limit  (0 if limit = 0)
```

**Note:** Opening balances can be modeled as an initial `purchase` or a dedicated `opening_balance` type in a later revision if needed. PRD v1 allows an optional one-time “set current outstanding” on card create (implementation may insert a system transaction).

### 8.2 Contact outstanding balance

```text
contact_balance =
    sum(purchases + fees attributed to contact)
  − sum(refunds attributed to contact)
  − sum(settlements for contact)
```

- `payment_to_issuer` never affects contact balances.
- Interest attributed to a contact is optional; default interest to self unless user attributes it.

### 8.3 Statement date computation (IST)

Given `statement_day = D` and today in `Asia/Kolkata`:

- Next statement date = next calendar date with day `D`, clamping to month length (e.g. day 31 → last day of month).
- Previous statement date = previous such date.

### 8.4 Due date computation

| Rule | Computation |
|------|-------------|
| `fixed_day` + value `V` | Next occurrence of day `V` on or after statement date (product rule: typically due date in the following cycle window; exact algorithm documented in domain code with unit tests) |
| `days_after_statement` + `N` | `statement_date + N days` |

Implementation must unit-test edge cases: month ends, leap years, statement on 31st.

### 8.5 Settlement constraints

- Settlement amount must be > 0
- Settlement may exceed current balance (overpayment → negative balance / credit with contact); UI should warn but allow (configurable later)

### 8.6 PDF import

- Candidates start as `pending`
- Only `accepted` / `edited` rows create `transactions` on confirm
- Idempotent confirm: re-confirm does not duplicate committed rows

---

## 9. Auth & multi-tenancy

### 9.1 Auth provider: Supabase Auth

- Google OAuth
- Email magic link (primary email path)
- Phone OTP (SMS provider required in Supabase project)

### 9.2 API auth

- Frontend obtains Supabase session JWT
- FastAPI validates JWT (JWKS / secret per Supabase config)
- Request context includes `user_id` and active `organization_id`
- Membership check on every org-scoped operation

### 9.3 Defense in depth

1. FastAPI authorization layer  
2. Supabase RLS policies on all tenant tables  
3. Storage policies for private statement PDFs  

### 9.4 Personal workspace bootstrap

On first authenticated request (or auth webhook):

1. Create `profiles` row if missing  
2. If user has zero memberships → create organization + owner membership  

---

## 10. Integrations

| System | Role |
|--------|------|
| **Supabase Auth** | Identity providers & sessions |
| **Supabase Postgres** | System of record |
| **Supabase Storage** | Private statement PDFs |
| **FastAPI** | Business logic, PDF pipeline, computed APIs |
| **Vercel** | Frontend hosting |
| **FastAPI Cloud** | Backend hosting |

### 10.1 PDF parsing

- Pluggable `StatementParser` interface: `detect(issuer) → parse(pdf_bytes) → list[LineCandidate]`
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
- Full i18n framework not required in v1

### 11.6 Quality bar

- TypeScript strict mode (frontend)
- Pydantic models + mypy/pyright (backend)
- Unit tests for domain math (balances, billing dates)
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

One git repository; two top-level apps without monorepo tooling.

---

## 13. Risks & open questions

### 13.1 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| PDF formats differ by issuer | Failed imports | Review UI + pluggable parsers; manual entry always works |
| Phone OTP SMS cost | Friction for personal use | Ship Google + email first; phone config-ready |
| Multi-tenant overbuild | Slow delivery | Simple personal UX; org model under the hood |
| Incorrect due-date rules | Missed payments | Configurable rules + unit tests; user-visible next due always shown |
| Float money bugs | Ledger corruption | Integer paise only |

### 13.2 Open questions (resolve during build)

1. Exact email auth preference confirmed as magic link (recommended).  
2. Which 1–2 issuers for first PDF parsers?  
3. Preferred due-date rules for your actual cards (samples).  
4. Supabase project credentials when wiring Phase 1.  
5. Whether overpayment to a contact is allowed without warning (currently: warn, allow).  

---

## 14. Phased roadmap

| Phase | Scope | Outcome |
|-------|--------|---------|
| **0** | PRD + frontend/backend scaffold + README | Runnable empty shells |
| **1** | Auth + org bootstrap + app shell | Secure multi-tenant foundation |
| **2** | Cards + billing cycle math + dashboard KPIs | Card inventory usable daily |
| **3** | Contacts + transactions + settlements | Full lending ledger |
| **4** | Statement PDF upload + review + first parsers | Assisted import |
| **5** | Polish, empty states, deploy personal prod | Daily driver live |
| **Later** | Public packaging, invites polish, external reminders | Wider audience |

---

## 15. Acceptance criteria (v1 personal daily driver)

v1 is accepted when:

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

---

## 16. Appendix — glossary

| Term | Meaning |
|------|---------|
| **Statement date** | Date issuer generates the billing statement |
| **Due date** | Date payment to issuer is due |
| **Contact** | Person who may use a lent card; not an app user |
| **Settlement** | Money a contact pays back to the owner |
| **Payment to issuer** | Money the owner pays the bank toward the card bill |
| **Outstanding (card)** | Tracked amount still owed to the issuer |
| **Outstanding (contact)** | Tracked amount the contact still owes the owner |
| **Paise** | 1/100 of one INR; storage unit for money |

---

## 17. Document history

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-07-27 | Initial PRD from discovery decisions |
