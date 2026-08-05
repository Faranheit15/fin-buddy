# US-02 — Multi-account balances

| Field | Value |
|--------|--------|
| **Status** | In progress |
| **Priority** | P0 |
| **Maps to** | R2B |
| **PRD** | FR-AC1–FR-AC6, UC17, UC18, G3, §5.7, §7.2 |
| **Depends on** | US-01 (adjustments / posted ledger) |

## User story

**As** a Fin Buddy owner  
**I want** bank, cash, and wallet accounts whose balances come only from posted ledger entries  
**So that** I can track all liquid money alongside credit cards without spreadsheet juggling.

## Current architecture touchpoints

- Cards only: [`backend/app/models/credit_card.py`](../../../../backend/app/models/credit_card.py)
- Transactions require `credit_card_id` today
- No `accounts` table
- UI nav: [`frontend/src/components/layout/app-sidebar.tsx`](../../../../frontend/src/components/layout/app-sidebar.tsx)
- Routes under `frontend/src/app/app/cards/*`

## Acceptance criteria

1. Account kinds: `bank`, `cash`, `wallet`, `credit_card`.
2. Every existing credit card gets a 1:1 `credit_card` account (migration).
3. Transactions gain `account_id` (backfilled from card mapping where needed).
4. Balance = sum of posted ledger effects; Correct Balance posts an `adjustment`.
5. CRUD + archive APIs with org authz + RLS.
6. UI: `/app/accounts`, `/app/accounts/[id]`, sidebar entry; cards still work.

---

## Subtasks

### Gather

- [x] **US-02.G1** Decide whether `credit_card_id` stays required on card spends or becomes optional when `account_id` points at a card account — document invariant.
- [x] **US-02.G2** List balance effect rules per account kind (asset accounts vs credit liability).
- [x] **US-02.G3** Confirm Correct Balance UX fields (target balance, reason, effective date).

### Plan

- [x] **US-02.P1** Spec `accounts` schema + RLS policies + indexes.
- [x] **US-02.P2** Spec migration/backfill: card → account; transaction `account_id`.
- [x] **US-02.P3** Spec `/api/v1/accounts` endpoints and balance response shape.
- [x] **US-02.P4** Spec frontend routes, empty states, Correct Balance dialog — **impeccable `shape`** (+ `onboard` notes for first bank/cash/wallet); keep `/app/cards` working.

### Implement

- [ ] **US-02.I1** Models + enums + Alembic migration + backfill.
- [ ] **US-02.I2** Account balance service + Correct Balance → adjustment (uses US-01).
- [ ] **US-02.I3** Accounts API + wire transactions to accept `account_id`.
- [ ] **US-02.I4** Frontend: accounts list/detail, nav, transaction account picker, Correct Balance — **impeccable craft-floor**; Operate density consistent with cards/contacts.
- [ ] **US-02.I5** Update `.env.example` only if new config needed (usually none).

### Test

- [ ] **US-02.T1** Unit: opening balance via adjustment.
- [ ] **US-02.T2** Unit: correct-balance delta.
- [ ] **US-02.T3** API: CRUD/archive; cross-org denied.
- [ ] **US-02.T4** Migration check: every card has an account; sample balances unchanged.
- [ ] **US-02.T5** Backend + frontend DoD commands for touched code.

### Validate

- [ ] **US-02.V1** Manual: create bank/cash/wallet; post spend/income; balances match.
- [ ] **US-02.V2** Manual: Correct Balance on cash; adjustment appears; history intact.
- [ ] **US-02.V3** Manual: existing cards dashboard KPIs still correct.
- [ ] **US-02.V4** **Impeccable:** `onboard` empty states; `polish` + `harden` + `audit` on `/app/accounts` surfaces.
- [ ] **US-02.V5** Mark Done; update PROGRESS + RELEASE-2-TASKS R2B.

## Story notes

### US-02.G1 — Card vs `account_id` invariant (2026-08-05)

**Code today:** `Transaction.credit_card_id` is **NOT NULL** (FK `credit_cards`, `ON DELETE RESTRICT`). All writers (manual create, adjust, reverse, statement import, opening balance) require a card. `ledger_service` card outstanding groups by `credit_card_id`. Statements are card-scoped. No `accounts` table yet.

**PRD:** `accounts.credit_card_id` set when `kind=credit_card`; transactions gain `account_id` (“card txs also resolve via credit_card account”). FR-AC5: card accounts retain billing specialization (1:1 with `credit_cards`).

#### Decision (invariant)

1. **`account_id` becomes required** on every transaction after US-02 migration (backfill: card → its 1:1 `credit_card` account).
2. **`credit_card_id` becomes nullable** (not dropped).
3. **Kind rules (service-enforced + DB check preferred):**
   - `account.kind == credit_card` → `credit_card_id` **MUST** be set and **MUST equal** `accounts.credit_card_id` for that account (denormalized pointer for existing card/dashboard/statement queries without forcing every reader to join).
   - `account.kind ∈ {bank, cash, wallet}` → `credit_card_id` **MUST be NULL**.
4. **API compat during R2B:**
   - Create with `credit_card_id` only → resolve `account_id` from card’s account.
   - Create with `account_id` only (card kind) → fill `credit_card_id` from `account.credit_card_id`.
   - Create with both → reject if mismatched (`account_card_mismatch`).
   - Bank/cash/wallet creates send `account_id` only.
5. **Statements / import** stay card-scoped: always set both IDs on the card’s account.
6. **Card outstanding KPIs** may keep grouping by `credit_card_id` where non-null; account balance service sums by `account_id` (posted-only, US-01). Do not double-count the same row in both “card outstanding” and a separate card-account balance for net worth later — one physical row, one contribution (G2 will define signs).

**Rejected:** Keep `credit_card_id` NOT NULL forever (blocks bank/cash/wallet). Drop `credit_card_id` immediately (breaks statement import + card filters + dashboard without a large rewrite in this story).

#### Related defaults (Gather ambiguity)

- **Settlements:** keep existing `settlements` table for friend repayments; **do not** fold them into ledger adjustments. Future **obligations** (US-04) are separate; friend dues must **not double-count** settlement rows and obligation repayments (document when US-04 lands).
- Adjust UI / Correct Balance lives on accounts in this story (US-01 deferred it here).

### US-02.G2 — Balance effect rules by account kind (2026-08-05)

**Code today:** `app/domain/ledger.py` `CARD_EFFECT` / `CONTACT_EFFECT` + `ledger_service` posted-only sums. Card “balance” = **issuer liability outstanding** (purchase/fee/interest/opening_balance **+**; refund/payment_to_issuer **−**; adjustment `delta_sign×amount`; reversal negates original). Matches PRD §8.1. Contact balance unchanged by this story (settlements still subtract separately).

#### Semantics of the reported balance number

| Account kind | Balance meaning | Net-worth role (FR-D6) |
|--------------|-----------------|------------------------|
| `bank`, `cash`, `wallet` | **Asset** — money held (higher = richer) | **+** balance |
| `credit_card` | **Liability** — spend outstanding to issuer (higher = more owed); same math as today’s card outstanding | **−** balance |

One posted row contributes once via `account_id`. Do **not** add the same card txs again as a separate “card KPI” in net worth — card KPI may still group by `credit_card_id` for dashboard, but NW uses account balances (G1).

#### Effect multipliers (posted only; drafts = 0)

**Liability** (`credit_card`) — keep `CARD_EFFECT`:

| Type | Effect on outstanding |
|------|----------------------|
| purchase, fee, interest, opening_balance | +amount |
| refund, payment_to_issuer | −amount |
| adjustment | `delta_sign × amount` |
| reversal | `−CARD_EFFECT[original] × amount` |

**Asset** (`bank` / `cash` / `wallet`) — new `ASSET_EFFECT` (opposite for spend/refund; opening stays +):

| Type | Effect on asset balance |
|------|-------------------------|
| purchase, fee, payment_to_issuer | −amount (money left the account) |
| refund, interest, opening_balance | +amount (inflow / starting cash / interest credited) |
| adjustment | `delta_sign × amount` (Correct Balance / opening via adjust) |
| reversal | `−ASSET_EFFECT[original] × amount` |

Notes:
- **`interest` is kind-dependent in meaning:** on cards = finance charge (+liability); on assets = interest earned (+cash). Same type enum; effect table selects by account kind.
- **`payment_to_issuer` on an asset account** = outflow paying a card (pre–US-03 transfer). On the card account a separate `payment_to_issuer` row still reduces liability — two rows, two accounts (not a single transfer_group yet).
- **Transfers / income category types** deferred to US-03; until then use purchase/refund/adjustment/`payment_to_issuer` as above.
- **Contact attribution:** keep `CONTACT_EFFECT` for rows with `contact_id` regardless of account kind (friend dues from attributed spend); settlements remain the only subtractor for friend dues in R2B.

#### Correct Balance (feeds G3)

`target_balance − current_derived_balance = delta_paise` → post posted `adjustment` with `delta_sign` / `amount_paise=abs(delta)` on that `account_id` (and card id if credit_card kind per G1).

### US-02.G3 — Correct Balance UX fields (2026-08-05)

**PRD §5.7 / FR-AC4 / UC18:** Account detail → Correct balance → target + reason → system posts `adjustment`; history intact.

**Code today:** `POST /transactions/adjust` takes `credit_card_id`, signed `delta_paise`, required `reason`, optional `occurred_at` / `contact_id` / `merchant`. No UI yet (US-01 deferred). No `account_id` on adjust. Card create already has optional opening outstanding → separate path.

#### Surface

- Primary: dialog on **`/app/accounts/[id]`** (and card account reachable from cards if linked).
- Not on the global ledger form (copy already points to Correct Balance).

#### Dialog fields

| Field | Required | Notes |
|-------|----------|-------|
| **Current balance** | read-only | Derived posted balance (G2 semantics); show INR; kind-aware caption (“Outstanding” for `credit_card`, “Balance” for bank/cash/wallet). |
| **Target balance** | yes | ₹ input → paise. Same unit as current (outstanding vs cash held). |
| **Delta preview** | read-only | `target − current` shown before submit (sign + INR). |
| **Reason** | yes | Free text, trim, min 1 / max ~2000 → `correction_reason`. Placeholder e.g. “Reconcile with bank statement”. |
| **Effective at** | no | datetime-local; default **now (IST display)** → `occurred_at`. |

**Out of dialog (defaults):**
- `merchant` = `"Balance adjustment"` (or `"Correct balance"`) — not editable in R2B.
- `contact_id` = **null** — Correct Balance is account reconciliation, not friend attribution (raw adjust API may still allow contact later if needed).
- Always **posted** adjustment (never draft).

#### API shape (Plan/Implement)

Prefer **account-scoped** Correct Balance that accepts `target_balance_paise` + `reason` + optional `occurred_at`; **server recomputes** `delta = target − current` and rejects `delta == 0` (`already_at_target` / `invalid_delta`). Do not trust client-only delta for posting. Wire through G1 ids (`account_id` + card id when kind=credit_card). Existing `/transactions/adjust` can remain as low-level delta API or be wrapped.

#### Edge cases

- Archived account → block Correct Balance.
- Target = current → inline error, no row.
- Concurrent posts → accept eventual balance; user can correct again (no optimistic lock in R2B).
- Opening balance on **new** bank/cash/wallet: optional create field → first posted adjustment (or `opening_balance` type); distinct from Correct Balance but same audit idea (FR-AC4).

#### Copy cues

- Title: “Correct balance”
- Confirm: “Post adjustment”
- Success: stay on account detail; balance updates; new adjustment visible in activity/ledger.

### US-02.P1 — Accounts schema + RLS + indexes (2026-08-05)

**File (I1):** `backend/alembic/versions/20260805_0005_accounts.py`  
**revision:** `20260805_0005` · **down_revision:** `20260805_0004`  
**Scope this plan:** `accounts` table + enum + constraints/indexes + RLS SQL. Transaction `account_id` + backfill = **P2**. ORM/API = I1–I3.

#### 1. Enum `account_kind`

```sql
DO $$ BEGIN
  CREATE TYPE account_kind AS ENUM ('bank', 'cash', 'wallet', 'credit_card');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
```

Python: `AccountKind(StrEnum)` with the same four values. Alembic: `_ensure_enum` / `create_type=False` style like `posting_status`.

#### 2. Table `accounts`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `id` | UUID PK | no | `gen_random_uuid()` / app uuid4 |
| `organization_id` | UUID FK → `organizations.id` ON DELETE CASCADE | no | |
| `kind` | `account_kind` | no | |
| `name` | VARCHAR(120) | no | Display name; for card accounts default = card nickname at backfill |
| `institution` | VARCHAR(120) | yes | Bank/wallet label; card issuer optional copy |
| `currency` | CHAR(3) | no | Default `'INR'` |
| `credit_card_id` | UUID FK → `credit_cards.id` ON DELETE RESTRICT | yes | Set **iff** `kind = credit_card` (G1) |
| `archived_at` | TIMESTAMPTZ | yes | Soft-archive (FR-AC6); NULL = active |
| `created_at` / `updated_at` | TIMESTAMPTZ | no | `now()` |

**Check constraints:**
```sql
CHECK (
  (kind = 'credit_card' AND credit_card_id IS NOT NULL)
  OR (kind <> 'credit_card' AND credit_card_id IS NULL)
)
```

**Uniqueness:**
```sql
CREATE UNIQUE INDEX uq_accounts_credit_card_id
  ON accounts (credit_card_id)
  WHERE credit_card_id IS NOT NULL;
```
→ at most one account per card (1:1).

Optional service-level uniqueness: active `(organization_id, kind, lower(name))` — not enforced in DB in R2B (users may rename; avoid blocking archive/restore).

#### 3. Indexes

```sql
CREATE INDEX ix_accounts_organization_id ON accounts (organization_id);
CREATE INDEX ix_accounts_org_kind ON accounts (organization_id, kind);
CREATE INDEX ix_accounts_org_active
  ON accounts (organization_id)
  WHERE archived_at IS NULL;
```

#### 4. RLS (defense in depth)

**Today:** no Postgres RLS policies exist in Alembic; FastAPI `OrgContext` + service-role DB is the real gate (same as cards/contacts).

**Still ship for `accounts` (and document):**

```sql
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts FORCE ROW LEVEL SECURITY;  -- optional; skip FORCE if service-role must bypass without SET ROLE

-- Membership-scoped access (Supabase JWT / auth.uid())
CREATE POLICY accounts_select_member ON accounts
  FOR SELECT USING (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
    )
  );
CREATE POLICY accounts_insert_member ON accounts
  FOR INSERT WITH CHECK (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
    )
  );
CREATE POLICY accounts_update_member ON accounts
  FOR UPDATE USING (
    organization_id IN (
      SELECT organization_id FROM organization_members
      WHERE user_id = auth.uid()
    )
  );
-- Soft-archive via UPDATE; no DELETE policy for members (or restrict DELETE to none)
```

**Notes for I1 / GOTCHAS:**
- If the app pool uses **service_role**, policies do not constrain backend; keep **API org checks** as source of truth.
- If `auth.uid()` is unavailable in plain Postgres CI, wrap RLS policy creation in a conditional or apply only when Supabase roles exist — prefer shipping SQL that matches contacts/cards when those gain RLS; until then document “policies ready; enable when auth.uid() path exists.”
- Do **not** grant anon unrestricted access.

#### 5. Out of P1 (explicit)

| Deferred | Story subtask |
|----------|----------------|
| `transactions.account_id` + nullable `credit_card_id` + backfill | **P2** |
| Account balance service / Correct Balance | **P3** / I2 |
| `/api/v1/accounts` routes | **P3** / I3 |
| Frontend | **P4** / I4 |

#### 6. Downgrade

Drop policies → drop indexes → drop table `accounts` → drop type `account_kind` only if unused (safe if table gone).

### US-02.P2 — Migration / backfill: card → account + `transactions.account_id` (2026-08-05)

**Files (I1):**  
1. `20260805_0005_accounts.py` — P1 DDL **plus** card→account row backfill (must exist before tx update).  
2. `20260805_0006_transaction_account_id.py` — `account_id` column, backfill, NOT NULL, nullable `credit_card_id`, indexes.  
**down_revision chain:** `0004` → `0005` → `0006`.

Implements G1: every card gets one `credit_card` account; every existing transaction gets that account’s id; `credit_card_id` becomes nullable for future bank/cash/wallet rows.

#### A. Inside `0005` after `accounts` create (amend P1 implement)

```sql
INSERT INTO accounts (
  id, organization_id, kind, name, institution, currency,
  credit_card_id, archived_at, created_at, updated_at
)
SELECT
  gen_random_uuid(),
  c.organization_id,
  'credit_card'::account_kind,
  c.nickname,
  c.issuer,
  c.currency,
  c.id,
  CASE WHEN c.status = 'closed' THEN now() ELSE NULL END,  -- optional; or leave NULL and map status only in app
  now(),
  now()
FROM credit_cards c
WHERE NOT EXISTS (
  SELECT 1 FROM accounts a WHERE a.credit_card_id = c.id
);
```

**Verify:** `SELECT count(*) FROM credit_cards` = `SELECT count(*) FROM accounts WHERE kind = 'credit_card'`.

Idempotent: `NOT EXISTS` guard. Use `gen_random_uuid()` (pgcrypto/`uuid-ossp` — confirm extension; else app-side uuid in Python migration loop). Prefer SQL if extension already used; else `op.get_bind()` + executemany with uuid4.

**Card status note:** MVP `card_status` may be `active`/`closed` — only archive account if product wants closed cards hidden; default **leave `archived_at` NULL** for all backfilled rows (safer; cards UI still filters by card status).

#### B. Revision `0006` — transactions

| Step | DDL / DML |
|------|-----------|
| 1 | `ADD COLUMN account_id UUID NULL` |
| 2 | Backfill: `UPDATE transactions t SET account_id = a.id FROM accounts a WHERE a.credit_card_id = t.credit_card_id AND t.account_id IS NULL` |
| 3 | Fail migration if any `account_id IS NULL` remain (raise) — every tx had a card |
| 4 | `ALTER COLUMN account_id SET NOT NULL` |
| 5 | `ADD CONSTRAINT fk_transactions_account_id FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE RESTRICT` |
| 6 | `ALTER COLUMN credit_card_id DROP NOT NULL` |
| 7 | Indexes (below) |

**No DB check** tying `credit_card_id` to `accounts.kind` (needs join/trigger). G1 rules stay **service-enforced** after I3.

```sql
CREATE INDEX ix_transactions_account_id ON transactions (account_id);
CREATE INDEX ix_transactions_org_account
  ON transactions (organization_id, account_id);
-- keep existing credit_card_id indexes for dashboard/statement filters
```

#### C. Balance / data integrity expectations

- Posted outstanding per card **unchanged**: same rows, same `credit_card_id`, same amounts; only add `account_id`.
- Account balance for a card account (G2 liability effects) **equals** card outstanding for that card after backfill.
- T4 / DoD: sample org — sum by card vs sum by linked account_id match.

#### D. Downgrade `0006`

1. Reject or no-op if any row has `credit_card_id IS NULL` (bank accounts already used).  
2. Else `ALTER credit_card_id SET NOT NULL` → drop FK/indexes/`account_id`.  
3. Do **not** delete `accounts` rows here (belongs to `0005` downgrade).

#### E. App follow-ups (not this migration file)

| After migrate | Owner |
|---------------|--------|
| ORM: `Account` model; `Transaction.account_id` required; `credit_card_id` optional | I1 |
| Create card → also insert 1:1 account | I3 / cards service |
| Create/adjust/reverse/import resolve G1 ids | I3 |
| Correct Balance / account balance by `account_id` | I2 / P3 |

#### F. Out of P2

API response shapes, Correct Balance endpoint details → **P3**. Frontend → **P4**.

### US-02.P3 — `/api/v1/accounts` + balance response (2026-08-05)

**Router:** `backend/app/api/v1/accounts.py` · prefix `/accounts` · include in `api/v1/__init__.py`.  
**Auth:** `CurrentUser` + `OrgContext` (same as cards).  
**Services:** `account_service` (CRUD/archive) + `ledger_service` extensions (`account_balance_paise` / `accounts_balances_map` using G2 ASSET/LIABILITY effects, posted-only).

#### 1. Response shape

```text
AccountResponse
  id, organization_id
  kind: AccountKind                  # bank | cash | wallet | credit_card
  name, institution, currency
  credit_card_id: UUID | null        # set iff kind=credit_card
  archived_at: datetime | null
  balance_paise: int                 # derived; G2 meaning by kind
  balance_label: "balance" | "outstanding"   # optional helper for UI; or derive client-side from kind
  created_at, updated_at
```

- **List/detail always include `balance_paise`** (mirror `CreditCardResponse.outstanding_paise`).
- For `credit_card` kind: `balance_paise` == card spend outstanding (same formula as `card_outstanding_paise` for linked card).
- For asset kinds: cash held (ASSET_EFFECT sum).
- Do **not** embed full card billing fields here — link via `credit_card_id` to existing `/cards/{id}`.

**AccountDetailResponse** (GET by id, optional): `AccountResponse` + `recent_transactions: list[TransactionResponse]` (page_size ≤ 20, newest first) — nice-to-have in I3; list can omit recent.

#### 2. Endpoints

| Method | Path | Body / query | Status | Behavior |
|--------|------|--------------|--------|----------|
| GET | `/accounts` | `page`, `page_size`, `kind?`, `include_archived=false` | 200 | `PaginatedResponse[AccountResponse]`; default hide `archived_at IS NOT NULL`; order by kind then name |
| POST | `/accounts` | `AccountCreate` | 201 | Create bank/cash/wallet only (`kind ≠ credit_card`). Optional `opening_balance_paise` → posted adjustment (or `opening_balance`) after insert. Reject `credit_card` kind (`use_cards_api`). |
| GET | `/accounts/{id}` | — | 200 | Org-scoped; 404 if missing/wrong org |
| PATCH | `/accounts/{id}` | `AccountUpdate` | 200 | `name`, `institution` only (not kind, not credit_card_id). Archived: allow unarchive (`archived_at=null`) + name edits |
| POST | `/accounts/{id}/archive` | — | 200 | Set `archived_at=now()`; idempotent if already archived. Block archive of last? — no. Card-linked accounts: allow archive but card CRUD remains on `/cards` |
| POST | `/accounts/{id}/correct-balance` | `CorrectBalanceRequest` | 201 | See §3; returns created `TransactionResponse` (adjustment) **or** `{ adjustment, account }` — prefer **TransactionResponse** + client refetches account |

**Card accounts:** created only by card create path (I3), not `POST /accounts`. List still returns them.

#### 3. Correct Balance request

```text
CorrectBalanceRequest
  target_balance_paise: int          # same unit as balance_paise for that kind
  reason: str (min 1, max 2000)
  occurred_at: datetime | null       # default now UTC
```

Server:
1. Load account; 404 / `account_archived` if archived.
2. `current = account_balance_paise(account_id)`.
3. `delta = target_balance_paise - current`; if `delta == 0` → 400 `already_at_target`.
4. Call adjust with G1 ids (`account_id`, `credit_card_id` if card kind), `delta_paise=delta`, reason, occurred_at; merchant default `"Balance adjustment"`.
5. Commit; return adjustment tx.

Keep `POST /transactions/adjust` as low-level delta API (extend with optional `account_id` in I3).

#### 4. Create / update schemas

```text
AccountCreate
  kind: bank | cash | wallet     # not credit_card
  name: str
  institution: str | null
  currency: str = "INR"
  opening_balance_paise: int | null   # ≥0; asset opening only

AccountUpdate
  name: str | null
  institution: str | null
  archived_at: datetime | null        # clear to unarchive; or use archive endpoint only — prefer archive endpoint + PATCH name/institution only
```

#### 5. Error codes

| Code | When |
|------|------|
| `not_found` | Wrong org / missing id |
| `use_cards_api` | POST kind=credit_card |
| `account_archived` | Correct Balance / mutating money on archived |
| `already_at_target` | delta 0 |
| `invalid_delta` / `invalid_reason` | reuse adjust codes |
| `account_card_mismatch` | adjust/create path G1 violation |

#### 6. Transaction create wiring (I3 note)

`TransactionCreate` gains optional `account_id`; resolve per G1. Response includes `account_id` + nullable `credit_card_id`.

#### 7. Out of P3

Frontend routes / Correct Balance dialog shape → **P4**. Implement balance helpers → **I2**.

### US-02.P4 — Frontend shape brief (2026-08-05)

**Impeccable:** `context.mjs` (Operate; Ledger Shelf / PRODUCT+DESIGN; target cards page as incumbent). **`shape`** for accounts list/detail + Correct Balance. **Assumptions** (Ralph autonomous — no human interview): refine within existing app shell density (match `/app/cards` + `/app/transactions`); do not invent a new visual world; Cards nav stays; Accounts is additive.

#### Job and audience
Owner scanning liquid money + card liabilities in one place (Zerodha/Kite-like ops). Need: see bank/cash/wallet balances at a glance; open an account; reconcile with Correct Balance without leaving the shelf.

#### Outcome and proof
1. Sidebar **Accounts** → list with kind + INR balance (G2 labels). 2. Add bank/cash/wallet in-page (not card — cards stay on Cards). 3. Detail shows balance + Correct Balance. 4. Empty first-run nudges one cash/bank account without a tutorial carousel. 5. `/app/cards` unchanged in behavior.

#### Selected direction
- **Visual authority:** incumbent cards/contacts/transactions pages — `max-w-5xl`, header + primary CTA, optional inline form Card, dense table or compact list rows, `EmptyState`, mono tabular INR.
- **Thesis:** Accounts = money pots; Cards = billing specialization. List mixes kinds with a quiet kind badge; card rows link through to `/app/cards/[id]` when `credit_card_id` set.
- **Focal moment:** Correct Balance dialog (reuse Dialog primitive from reverse flow) — current / target / delta preview / reason / optional effective at.

#### Scope and boundaries

| In | Out |
|----|-----|
| Routes `/app/accounts`, `/app/accounts/[id]` | Redesign dashboard net worth (US-06) |
| Nav item **Accounts** (Wallet/Landmark icon) between Dashboard and Cards | Nested KPI strip / purple glow |
| List + add form (bank/cash/wallet) + archive | Creating credit_card accounts from Accounts UI |
| Detail: balance, Correct Balance, link to card if any, recent txs if API provides | Full transaction edit on detail |
| Tx form: optional account picker (I4) preferring account_id | Replacing card picker entirely in R2B |

#### States and ranges (onboard)
- **Empty (no bank/cash/wallet yet):** EmptyState — title “No accounts yet”; body “Add cash, bank, or wallet. Card balances stay under Cards.” CTA **Add account**. Card-only orgs after migration still see **credit_card** rows in list — empty state only when **zero accounts of any kind** OR when filtered to assets and none exist. **Decision:** empty when `items.length === 0`; after backfill card accounts exist so empty is rare — onboard copy on first **Add account** form helper instead: one line “Start with Cash if you track pocket money.”
- Loading / error: same compact patterns as cards (text + Retry).
- Archived: muted row or hidden by default; toggle “Show archived” like cards’ closed filter.

#### Interaction and layout
1. **Nav:** `{ href: "/app/accounts", label: "Accounts", icon: Wallet }` — insert after Dashboard.
2. **List page:** header “Accounts” / subtitle “Balances from posted ledger entries”; primary **Add account**; kind filter chips or select (All / Bank / Cash / Wallet / Cards); table or stacked rows: Name · Kind badge · Balance (mono) · actions (Open).
3. **Add form:** kind select (bank/cash/wallet), name, institution optional, opening ₹ optional; submit posts then refreshes list.
4. **Detail:** large balance (kind-aware caption Outstanding vs Balance); **Correct balance** button; for card kind secondary link “View card”; Archive.
5. **Correct Balance dialog:** fields per G3 — current read-only, target, delta preview, reason, effective at; confirm **Post adjustment**; errors `already_at_target` / network inline.
6. **Transactions:** add Account select on create form (accounts list); keep Card select for compatibility or derive card from account when kind=credit_card — **Decision:** Account select primary for new spends; when account is credit_card, set card implicitly; bank/cash/wallet clear card.

#### Components to touch (I4)
- `nav-items.ts` — Accounts entry
- `app/app/accounts/page.tsx`, `app/app/accounts/[id]/page.tsx`
- `features/accounts/*` — form, correct-balance-dialog, maybe list row
- `lib/api/accounts.ts` — client types matching P3
- `transaction-form.tsx` — account picker
- Reuse `Dialog`, `EmptyState`, `Badge`, `Button`, `Card`

#### Copy (clarify-ready)
- Correct balance title / Post adjustment (G3)
- `already_at_target`: “Already at that balance.”
- Archive confirm: “Archive this account? History stays; it hides from the default list.”

#### Anti-goals
- No marketing hero on Accounts
- No duplicate “card outstanding” widgets that fight Cards page
- Don’t remove or demote Cards nav

#### Open for builder
- List as table vs card-rows: prefer **table** on desktop to match transactions density
- Whether detail shows recent txs: yes if cheap (P3 optional detail payload)


