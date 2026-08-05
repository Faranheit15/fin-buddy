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
- [ ] **US-02.P2** Spec migration/backfill: card → account; transaction `account_id`.
- [ ] **US-02.P3** Spec `/api/v1/accounts` endpoints and balance response shape.
- [ ] **US-02.P4** Spec frontend routes, empty states, Correct Balance dialog — **impeccable `shape`** (+ `onboard` notes for first bank/cash/wallet); keep `/app/cards` working.

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


