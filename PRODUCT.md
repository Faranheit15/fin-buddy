# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are India-based personal finance owners who juggle bank accounts, cash, wallets, and multiple credit cards (different limits, statement days, due dates, and EMIs) while also managing shared or friend spend and informal debts — people who need one system of record for balances, dues, and who owes whom.

Secondary (later): a wider public audience with the same job-to-be-done; multi-tenant workspaces and platform admin are in the architecture so that expansion does not require a rewrite. Friends who borrow cards or money are contacts managed by the owner — they do not log into the product in Release 2 (connected-user debt confirm is Release 3+).

## Product Purpose

Fin Buddy is an India-first personal finance ledger with deep credit-card, EMI, and shared-spend workflows. It exists so users can stop reconstructing limits, billing calendars, account balances, EMIs, and informal IOUs from bank apps and spreadsheets.

Success means: the owner can see net worth, available credit (including EMI principal blocks), upcoming dues across cards/debts/EMIs, attribute spend, and know each contact’s outstanding balance — as a daily-driver system of record, then as a product suitable for a wider audience.

## Positioning

**Accounts + cards + billing cycles + EMIs + friend-attributed ledger in one place.** Limits, statement/due dates, EMI principal blocks, who used the card, debts, and who still owes you — unified. A generic expense app or issuer bank app does not combine multi-account balances, cycle calendar, EMI math, and person-level lending balances as one job.

## Operating Context

- Desktop-first web app (Next.js), with India-local time and money formatting in the product surface.
- Typical ritual: check net worth and dues → log spends (manual or file-assisted) → track friend balances and debts → record settlements/repayments → manage EMIs.
- Companion surfaces: authenticated app shell (dashboard, accounts, cards, contacts, ledger, debts, EMIs, statements) and platform admin observability for operators.
- Backend is FastAPI + Supabase; UI talks to API with JWT and optional `X-Organization-Id`.

## Capabilities and Constraints

Confirmed or in-scope product capabilities:

- Multi-tenant organizations with roles; personal workspace on first auth.
- Accounts: bank, cash, wallet, and credit cards; balances derived from an auditable ledger (draft vs posted; corrections via adjustments/reversals).
- Credit cards: metadata only (last four, never full PAN/CVV/PIN), limits in paise, statement day, due-date rules, EMI principal-block utilization.
- Spend ledger with contact attribution; settlements/obligation repayments separate from payments to the issuer.
- Categories, tags, transfers, and split entries.
- Personal debts / institutional loans with partial repayments.
- Optional GST amount tracking on spends/reimbursements (no tax filing).
- Statement PDF/CSV/Excel upload with human review before ledger commit (parsing is pluggable / imperfect by design).
- In-app notifications plus email due reminders (Release 2).
- Data export and account deletion request (Release 2).
- Platform admin roles with activity, error, and API request logs.
- Auth via Supabase: Google, email/password, magic link, phone (as configured).

Constraints and non-goals for design and copy:

- No Open Banking / Account Aggregator in Release 2.
- Friends are not app users in Release 2.
- No salary/PF/NPS, investments/XIRR, or AI agents in Release 2.
- Money as integer paise; display as INR (`en-IN`), dates/times in IST.
- Do not invent testimonials, benchmarks, pricing, or compliance certifications.

Undecided (record only): public packaging, monetization, and marketing brand world beyond the product name.

## Brand Commitments

- Product name: **Fin Buddy**.
- India-first product language: INR, IST, en-IN formats, Indian card/billing/EMI terminology.
- App surfaces lean **operate-mode density**: sidebar shell, KPI cards, data tables, activity — Kanakku-inspired structure as a density reference, not a visual clone or licensed template.
- **Dark mode** is first-class.
- Platform **admin observability** (activity / error / request logs) is part of the product story for operators, not a hidden debug console.
- **Visual direction (standing preference):** play the **category standard** for finance/ops dashboards at full craft — no conceptual “world” overlay, no irony. Craft bar named for the app dashboard: **Zerodha Coin / Kite**-like Indian fintech ops density (scan positions, urgency, money figures). Structural density may still reference Kanakku-style shell layouts without cloning chrome.

Visual identity is documented in **`DESIGN.md`** (North Star: *The Ledger Shelf*; OKLCH tokens from the shadcn/Geist implementation). Keep tokens in sync when shell chrome changes materially.

## Evidence on Hand

- PRD: `docs/prd/2026-07-27-fin-buddy-prd.md` (v2.0)
- Release 2 backlog: `docs/prd/RELEASE-2-TASKS.md`
- Release 2 user stories: `docs/prd/release-2/` (US-01…US-06, PROGRESS, Ralph prompt)
- Authenticated app shell + feature pages: `frontend/` (landing, auth, dashboard, cards, contacts, ledger, statements, notifications, settings)
- Backend API and domain model: `backend/`
- UI inspiration reference (external): Kanakku admin template demo (layout density only)
- No customer testimonials, press, or marketing assets yet — do not fabricate them

## Product Principles

1. **Clarity under complexity** — many accounts, cards, EMIs, and shared spends must stay scannable; density without clutter.
2. **Truthful money and dates** — paise-level accuracy, auditable history, and India-local presentation; never blur who owes what.
3. **Owner control** — the owner records and attributes; friends stay contacts until product expands.
4. **Operate first** — app UI optimizes for tasks and tables; persuasion is for marketing surfaces only when they exist.
5. **Observable system** — when the product is multi-user, operators can see usage and failures through admin logs.

## Accessibility & Inclusion

No product-specific accessibility standard was locked beyond common production expectations (keyboardable core flows, sufficient contrast). Prefer WCAG-minded defaults as implementation proceeds; formal target level remains open.
