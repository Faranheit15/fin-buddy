# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary users are multi-card holders in India who also manage shared or friend spend: people juggling several credit cards (different limits, statement days, and due dates) while lending cards to friends and needing a clear picture of who spent what and who still owes them.

Secondary (later): a wider public audience with the same job-to-be-done; multi-tenant workspaces and platform admin are in the architecture so that expansion does not require a rewrite. Friends who borrow cards are contacts managed by the card owner — they do not log into the product in v1.

## Product Purpose

Fin Buddy is a credit-card and friend-lending ledger. It exists so users can stop reconstructing card limits, billing calendars, and informal IOUs from bank apps and spreadsheets.

Success means: the owner can see available credit and upcoming dues per card, attribute every spend, and know each contact’s outstanding balance — as a daily-driver system of record, then as a product suitable for a wider audience.

## Positioning

**Cards + billing cycles + friend-attributed ledger in one place.** Limits, statement/due dates, who used the card, and who still owes you — unified. A generic expense app or issuer bank app does not combine card inventory, cycle calendar, and person-level lending balances as one job.

## Operating Context

- Desktop-first web app (Next.js), with India-local time and money formatting in the product surface.
- Typical ritual: check dues and utilization → log spends (manual or statement-assisted) → track friend balances → record settlements when friends pay back.
- Companion surfaces: authenticated app shell (dashboard, cards, contacts, ledger, statements) and platform admin observability for operators.
- Backend is FastAPI + Supabase; UI talks to API with JWT and optional `X-Organization-Id`.

## Capabilities and Constraints

Confirmed or in-scope product capabilities:

- Multi-tenant organizations with roles; personal workspace on first auth.
- Credit cards: metadata only (last four, never full PAN/CVV/PIN), limits in paise, statement day, due-date rules.
- Full spend ledger with contact attribution; settlements (repayments) separate from payments to the issuer.
- Statement PDF upload with human review before ledger commit (parsing is pluggable / imperfect by design).
- In-app notifications for dues and import status (no email/SMS/WhatsApp in v1).
- Platform admin roles with activity, error, and API request logs.
- Auth via Supabase: Google, email, phone (as configured).

Constraints and non-goals for design and copy:

- No Open Banking aggregation in v1.
- Friends are not app users in v1.
- Money as integer paise; display as INR (`en-IN`), dates/times in IST.
- Do not invent testimonials, benchmarks, pricing, or compliance certifications.

Undecided (record only): public packaging, monetization, and marketing brand world beyond the product name.

## Brand Commitments

- Product name: **Fin Buddy**.
- India-first product language: INR, IST, en-IN formats, Indian card/billing terminology.
- App surfaces lean **operate-mode density**: sidebar shell, KPI cards, data tables, activity — Kanakku-inspired structure as a density reference, not a visual clone or licensed template.
- **Dark mode** is first-class.
- Platform **admin observability** (activity / error / request logs) is part of the product story for operators, not a hidden debug console.
- **Visual direction (standing preference):** play the **category standard** for finance/ops dashboards at full craft — no conceptual “world” overlay, no irony. Craft bar named for the app dashboard: **Zerodha Coin / Kite**-like Indian fintech ops density (scan positions, urgency, money figures). Structural density may still reference Kanakku-style shell layouts without cloning chrome.

Visual identity is documented in **`DESIGN.md`** (North Star: *The Ledger Shelf*; OKLCH tokens from the shadcn/Geist implementation). Keep tokens in sync when shell chrome changes materially.

## Evidence on Hand

- PRD: `docs/prd/2026-07-27-fin-buddy-prd.md`
- Authenticated app shell + feature pages: `frontend/` (landing, auth, dashboard, cards, contacts, ledger, statements, notifications, settings)
- Backend API and domain model: `backend/`
- UI inspiration reference (external): Kanakku admin template demo (layout density only)
- No customer testimonials, press, or marketing assets yet — do not fabricate them

## Product Principles

1. **Clarity under complexity** — many cards and shared spends must stay scannable; density without clutter.
2. **Truthful money and dates** — paise-level accuracy and India-local presentation; never blur who owes what.
3. **Owner control** — the card owner records and attributes; friends stay contacts until product expands.
4. **Operate first** — app UI optimizes for tasks and tables; persuasion is for marketing surfaces only when they exist.
5. **Observable system** — when the product is multi-user, operators can see usage and failures through admin logs.

## Accessibility & Inclusion

No product-specific accessibility standard was locked beyond common production expectations (keyboardable core flows, sufficient contrast). Prefer WCAG-minded defaults as implementation proceeds; formal target level remains open.
