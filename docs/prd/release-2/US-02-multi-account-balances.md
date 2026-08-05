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
- [ ] **US-02.G3** Confirm Correct Balance UX fields (target balance, reason, effective date).

### Plan

- [ ] **US-02.P1** Spec `accounts` schema + RLS policies + indexes.
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

