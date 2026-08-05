# US-01 — Auditable ledger foundation

| Field | Value |
|--------|--------|
| **Status** | In progress |
| **Priority** | P0 — must ship first |
| **Maps to** | R2A |
| **PRD** | FR-T6, FR-T8, FR-T9, FR-AC3, FR-AC4, G2, §8.8 |
| **Depends on** | None (MVP transactions exist) |

## User story

**As** a Fin Buddy owner  
**I want** drafts and posted ledger entries with corrections via adjustments/reversals  
**So that** I can trust history and never lose truth to a silent edit.

## Current architecture touchpoints

- Model: [`backend/app/models/transaction.py`](../../../../backend/app/models/transaction.py) — no `posting_status` today; edit/delete allowed
- Enums: [`backend/app/models/enums.py`](../../../../backend/app/models/enums.py) — `TransactionType` lacks `adjustment` / `reversal`
- API: [`backend/app/api/v1/transactions.py`](../../../../backend/app/api/v1/transactions.py)
- Services: balance math in card/contact/dashboard services
- UI: [`frontend/src/app/app/transactions/page.tsx`](../../../../frontend/src/app/app/transactions/page.tsx)

## Acceptance criteria

1. Existing transactions migrate to `posted` with no balance drift.
2. Draft rows do not affect card/contact (later account) balances.
3. Posted rows cannot be silently updated/deleted (API returns 4xx).
4. Reverse and adjust flows create linked correction entries.
5. Import confirm still posts only accepted lines.
6. Domain + API tests cover draft exclusion, reversal, adjustment.

---

## Subtasks

### Gather (requirements)

- [x] **US-01.G1** Inventory all balance consumers (card outstanding, contact balance, dashboard, statement import confirm) and list which queries must filter `posted`.
- [x] **US-01.G2** Decide draft UX default: post-by-default with “Save draft”, vs explicit Post — document choice in story notes below.
- [x] **US-01.G3** Confirm migration strategy: backfill `posting_status='posted'`; nullable new FKs for reverse links.

### Plan

- [x] **US-01.P1** Spec Alembic migration: enum extensions, columns (`posting_status`, `reverses_id`, `reversed_by_id`, reason/notes for corrections).
- [x] **US-01.P2** Spec service API: `create_draft`, `post`, `reverse`, `adjust`; reject update/delete on posted.
- [x] **US-01.P3** Spec frontend states: badge, disabled edit, Reverse/Correct dialogs — **impeccable `shape`** (Operate mode; match existing ledger density).
- [x] **US-01.P4** Write test matrix (unit + API) before coding.

### Implement

- [x] **US-01.I1** Backend: enums + model columns + migration + backfill.
- [x] **US-01.I2** Backend: domain/service balance filters for `posted` only.
- [x] **US-01.I3** Backend: transaction API changes (create draft/post, reverse, adjust; lock posted mutate/delete).
- [x] **US-01.I4** Frontend: API client types + ledger UI (status badge, draft/post, reverse/correct) — follow **impeccable craft-floor**; preserve existing transactions page patterns.
- [x] **US-01.I5** Ensure statement import confirm creates `posted` rows only.

### Test

- [x] **US-01.T1** Unit: draft excluded from outstanding.
- [x] **US-01.T2** Unit: reversal negates; double-reverse blocked.
- [x] **US-01.T3** Unit: adjustment delta math.
- [x] **US-01.T4** API: posted update/delete → 4xx; reverse/adjust succeed with authz.
- [x] **US-01.T5** Run backend DoD: `pytest`, `ruff`, `mypy`; frontend `lint` + `typecheck` for touched UI.

### Validate

- [ ] **US-01.V1** Manual: create draft → balances unchanged → post → balances update.
- [ ] **US-01.V2** Manual: reverse a posted purchase; ledger and card outstanding correct.
- [ ] **US-01.V3** Manual: import review confirm still posts without duplicates.
- [ ] **US-01.V4** **Impeccable** on ledger UI: `polish` + `harden` (and `clarify` if reverse/correct copy is unclear).
- [ ] **US-01.V5** Mark story Status = Done; update [`PROGRESS.md`](PROGRESS.md); tick corresponding R2A items in [`../RELEASE-2-TASKS.md`](../RELEASE-2-TASKS.md).

## Story notes

_(Agent: record Gather decisions here.)_

### US-01.G1 — Balance consumers inventory (2026-08-05)

Today every row in `transactions` is treated as live. There is no `posting_status`. All balance math lives in `backend/app/services/ledger_service.py` and is consumed by cards / contacts / dashboard / notifications. Frontend only displays API-returned `outstanding_paise` (no client-side ledger sums).

#### Must filter `posting_status = posted` (balance math)

| Consumer | Location | Query / helper | Notes |
|----------|----------|----------------|-------|
| Card outstanding (single) | `ledger_service.card_outstanding_paise` | `sum(_card_outstanding_expr)` on `Transaction.credit_card_id` — **no status filter** | Core card KPI; also used after create/update/archive in `api/v1/cards.py` |
| Card outstanding (org map) | `ledger_service.cards_outstanding_map` | group-by `credit_card_id` — **no status filter** | Used by dashboard, cards list, notifications |
| Contact balance (single) | `ledger_service.contact_balance_paise` | `_contact_spend_expr` on `Transaction.contact_id` − settlements — **no status filter** | Contact detail/get after update |
| Contact balances (org map) | `ledger_service.contacts_balances_map` | spend group-by `contact_id` − settlements — **no status filter** | Contacts list + dashboard friend dues |
| Friend dues aggregate | `ledger_service.total_friend_dues` | org-wide contact spend − settlements — **no status filter** | Present in service; dashboard currently sums positive map values instead |
| Dashboard totals / utilization / attention | `api/v1/dashboard.py` | calls `cards_outstanding_map` + `contacts_balances_map` | Available credit = limit − outstanding; util % derived |
| Cards list/detail responses | `api/v1/cards.py` | `cards_outstanding_map` / `card_outstanding_paise` | Response fields `outstanding_paise`, available, util |
| Contacts list/detail | `api/v1/contacts.py` | `contacts_balances_map` / `contact_balance_paise` | Response `outstanding_paise` |
| In-app attention notifications | `notification_service.compute_desired_attention` | `cards_outstanding_map` for util / due copy | Must inherit posted-only via ledger helpers |

**Implementation note:** Prefer a single posted filter inside `ledger_service` expressions/helpers so all consumers stay correct without per-route patches. Future account balances (US-02) should reuse the same rule.

#### Writers that create rows which *will* affect balances once posted

| Writer | Location | Current behavior | R2 expectation |
|--------|----------|------------------|----------------|
| Manual create | `api/v1/transactions.py` `POST /` | Inserts row immediately (implicit live) | Create as `draft` or `posted` per UX (see G2); only posted enter balances |
| Manual update/delete | `PATCH` / `DELETE` same module | Silent mutate/delete allowed | Reject for `posted`; drafts remain editable |
| Card opening balance | `api/v1/cards.py` on create | Inserts `opening_balance` transaction | Must be created as **`posted`** (opening balance is intentional live liability) |
| Statement import confirm | `statement_service.import_statement` | Builds `Transaction(...)` for accepted/edited lines; no posting_status | Must create **`posted`** only (FR-T9 / FR-I confirm path); candidates stay out of ledger until confirm |

#### Must NOT filter by posted (or not balance math)

| Consumer | Location | Why |
|----------|----------|-----|
| Transaction list/filters | `api/v1/transactions.py` `GET /` | Ledger UI must show drafts + posted (optional later filter by status) |
| Dashboard transaction **count** | `dashboard.py` count subquery on `Transaction` | Activity volume metric — include drafts unless product later wants “posted only” (default: count all rows; document if changed) |
| Statement candidates / review | `statement_service` + statements API | Pre-ledger staging; not in `transactions` until confirm |
| Settlements sum | `ledger_service` settlement halves | Settlements table has no posting_status in MVP; leave as-is for US-01 (obligations are US-04) |
| Frontend display | `cards` / `contacts` / `dashboard` pages | Pass-through of API outstanding; no local sum to change |

#### `_CARD_EFFECT` / `_CONTACT_EFFECT` types today

- Card: purchase/fee/interest/opening_balance `+1`; refund/payment_to_issuer `-1`
- Contact: purchase/fee/interest `+1`; refund `-1`; opening_balance & payment_to_issuer `0`
- Missing for R2A: `adjustment`, `reversal` — effect signs to be defined in Plan (P2); both must still respect posted-only inclusion

#### Gap summary for Implement

1. Add `posting_status` + filter in all five ledger helpers above.
2. Opening-balance and import writers → `posted`.
3. Manual create respects draft/post choice; posted update/delete locked.
4. No frontend balance recompute — only badge/actions later (I4).

### US-01.G2 — Draft UX default (2026-08-05)

**Decision: post-by-default + “Save draft” secondary.**

Rationale:
- Matches Ralph/R2A default and `RELEASE-2-TASKS.md` (“post-by-default with save draft secondary”).
- Preserves MVP mental model: today’s form primary CTA is “Add transaction” and immediately affects balances; renaming primary to **Post** / **Add & post** keeps that path one click.
- Drafts remain available for incomplete attribution (e.g. unknown contact) without forcing a two-step Post for the common case.
- Import confirm stays a separate posted path (candidates → posted on confirm); not a “draft transaction” staging UI in R2.

UI / API implications (for Plan / Implement):
| Surface | Behavior |
|---------|----------|
| Create form primary | Submit creates `posting_status=posted` (label: keep “Add transaction” or “Post transaction”) |
| Create form secondary | Outline/ghost **Save draft** → `posting_status=draft`; does not change balances |
| API create | Accept optional `posting_status` (default **`posted`** if omitted) so existing clients stay safe |
| Draft rows | Editable / deletable via existing PATCH/DELETE; optional later “Post draft” action |
| Posted rows | No silent edit/delete; Reverse / Correct only |
| Opening balance / import confirm | Always `posted` (unchanged from G1) |

Rejected alternative: explicit dual-step “Save draft → Post” as primary — higher friction vs current MVP and not required by FR-T8.

### US-01.G3 — Migration strategy (2026-08-05)

**Confirmed approach (additive Alembic; no rewrite of MVP rows).**

#### Enums
1. **New** Postgres enum `posting_status`: `'draft' | 'posted'` (same `_ensure_enum` / `create_type=False` style as initial schema).
2. **Extend** existing `transaction_type` with `'adjustment'`, `'reversal'` via `ALTER TYPE … ADD VALUE IF NOT EXISTS` (do not recreate the type — `statement_line_candidates.proposed_type` shares it).
3. Defer other FR-T1 types (`income`, `expense`, `transfer`, EMI types) to later stories.

#### Columns on `transactions` (this story only — not `account_id` / GST / transfer yet)
| Column | Type | Null / default | Purpose |
|--------|------|----------------|---------|
| `posting_status` | `posting_status` enum | NOT NULL, server_default `'posted'` | Draft vs live ledger |
| `reverses_id` | UUID FK → `transactions.id` | NULL, `ON DELETE RESTRICT` | On a **reversal** row: the original it negates |
| `reversed_by_id` | UUID FK → `transactions.id` | NULL, `ON DELETE SET NULL` | On the **original**: the reversal that closed it (at most one) |
| `correction_reason` | `Text` | NULL | Required by service layer for reverse/adjust; optional at DB |

Use existing `notes` for free-form merchant notes; keep `correction_reason` separate so reverse/adjust audit copy is not mixed with merchant notes.

#### Backfill / balance safety
1. Add `posting_status` with `server_default='posted'` + `nullable=False` so **all existing rows become `posted` in one step** (no separate UPDATE required if default applies on add; still run explicit `UPDATE … SET posting_status = 'posted' WHERE posting_status IS NULL` if any path allows null during rollout).
2. New FKs start **NULL** for all MVP rows (none are corrections yet).
3. **Balance drift check:** after migrate, card/contact outstanding computed with posted-only filter must equal pre-migrate totals (all rows were effectively posted). Capture in I1/T1 via unit or migration smoke if feasible.
4. No data rewrite of amounts, types, or card/contact FKs.

#### Constraints / indexes (for P1 to formalize)
- Partial **unique** on `reversed_by_id` WHERE NOT NULL → original reversed at most once (supports double-reverse block).
- Index `(organization_id, posting_status)` and keep existing card/contact indexes for posted-filtered sums.
- Self-FKs: create columns nullable first, then `ForeignKeyConstraint` to `transactions.id` (same-table OK in Postgres).

#### Out of this migration
- Soft-delete / archive columns — not required; posted rows stay, corrections are new rows.
- Changing statement candidate schema — import still writes new `transactions` as `posted` at confirm time (I5).
- RLS: no new table; existing org RLS on `transactions` unchanged if already present; verify in I1.

#### Downgrade
Drop new columns/indexes; cannot safely remove enum values from Postgres (`adjustment`/`reversal` stay) — document as known Alembic limitation in GOTCHAS if we hit it.

### US-01.P1 — Alembic migration spec (2026-08-05)

**File:** `backend/alembic/versions/20260805_0003_auditable_ledger.py`  
**revision:** `20260805_0003`  
**down_revision:** `20260728_0002`  
**Scope:** schema only (enums + columns + indexes/constraints). ORM/API/UI land in I1–I4.

#### 1. Enum: create `posting_status`

```sql
DO $$ BEGIN
  CREATE TYPE posting_status AS ENUM ('draft', 'posted');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
```

Alembic: mirror initial-schema `_ensure_enum`; bind column with `postgresql.ENUM(..., name="posting_status", create_type=False)`.

Python (`enums.py`):

```python
class PostingStatus(enum.StrEnum):
    DRAFT = "draft"
    POSTED = "posted"
```

#### 2. Enum: extend `transaction_type`

Do **not** recreate the type (shared with `statement_line_candidates.proposed_type`).

```sql
ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'adjustment';
ALTER TYPE transaction_type ADD VALUE IF NOT EXISTS 'reversal';
```

Notes for I1:
- Run each `ADD VALUE` in its own `op.execute(...)`.
- On Postgres, new enum labels added in a transaction are usable after commit; keep migration as one Alembic revision (autocommit_block only if local PG version requires it — prefer plain executes first).
- Python: add `ADJUSTMENT = "adjustment"`, `REVERSAL = "reversal"` to `TransactionType`.

#### 3. Columns on `transactions` (upgrade order)

| Step | DDL | Details |
|------|-----|---------|
| A | `ADD COLUMN posting_status posting_status NOT NULL DEFAULT 'posted'` | Existing rows backfill via default; cast/server_default as enum label `'posted'` |
| B | `ADD COLUMN reverses_id UUID NULL` | No FK yet |
| C | `ADD COLUMN reversed_by_id UUID NULL` | No FK yet |
| D | `ADD COLUMN correction_reason TEXT NULL` | Service-required for reverse/adjust |
| E | `ADD CONSTRAINT fk_transactions_reverses_id FOREIGN KEY (reverses_id) REFERENCES transactions(id) ON DELETE RESTRICT` | Self-FK |
| F | `ADD CONSTRAINT fk_transactions_reversed_by_id FOREIGN KEY (reversed_by_id) REFERENCES transactions(id) ON DELETE SET NULL` | Self-FK |
| G | Indexes / unique (below) | |

Optional after A (belt-and-suspenders):  
`UPDATE transactions SET posting_status = 'posted' WHERE posting_status IS DISTINCT FROM 'posted';` — should be a no-op if default applied.

#### 4. Indexes & uniqueness

```sql
CREATE INDEX ix_transactions_org_posting_status
  ON transactions (organization_id, posting_status);

CREATE UNIQUE INDEX uq_transactions_reversed_by_id
  ON transactions (reversed_by_id)
  WHERE reversed_by_id IS NOT NULL;

CREATE INDEX ix_transactions_reverses_id
  ON transactions (reverses_id)
  WHERE reverses_id IS NOT NULL;
```

Semantics:
- Partial unique on `reversed_by_id` → an original can be linked to at most one reversal (double-reverse blocked at DB + service).
- `reverses_id` indexed for “find reversal for original” / integrity checks; service also enforces `type=reversal` when `reverses_id` set.

#### 5. ORM mapping checklist (I1, not this migration file)

`Transaction` model additions:
- `posting_status: Mapped[PostingStatus]` — `SAEnum(PostingStatus, name="posting_status", values_callable=…)`
- `reverses_id: Mapped[UUID | None]` — `ForeignKey("transactions.id", ondelete="RESTRICT")`
- `reversed_by_id: Mapped[UUID | None]` — `ForeignKey("transactions.id", ondelete="SET NULL")`
- `correction_reason: Mapped[str | None]` — `Text`
- Optional relationships: `reverses` / `reversed_by` (viewonly OK); avoid circular cascade deletes.

#### 6. Downgrade

1. Drop indexes `uq_transactions_reversed_by_id`, `ix_transactions_reverses_id`, `ix_transactions_org_posting_status`.
2. Drop FKs, then columns: `correction_reason`, `reversed_by_id`, `reverses_id`, `posting_status`.
3. `DROP TYPE IF EXISTS posting_status`.
4. **Do not** remove `'adjustment'` / `'reversal'` from `transaction_type` (Postgres cannot drop enum labels safely) — note in `docs/GOTCHAS.md` when implementing.

#### 7. Explicitly not in this revision

- `account_id`, `gst_paise`, `transfer_group_id`, `category_id` (later stories)
- New tables / RLS policies (no new table; app uses service-role + org filters today)
- Data backfill of reverse links (none exist)
- ActivityAction enum values for reverse/adjust (can add in I3 if logging needs them)

#### 8. Verify after migrate (I1 smoke)

- `\dT+ posting_status` / `transaction_type` shows new labels
- `SELECT posting_status, count(*) FROM transactions GROUP BY 1` → all `posted`
- App boot + existing pytest green before service filter changes (I2)

### US-01.P2 — Service / API spec (2026-08-05)

**Module:** `backend/app/services/transaction_service.py` (new). Routes in `api/v1/transactions.py` stay thin and call this service. Org membership via existing `OrgContext`.

**Schema tweak for I1 (amendment to P1):** add nullable `delta_sign SMALLINT NULL CHECK (delta_sign IN (-1, 1))` on `transactions`. Required when `type=adjustment` (card/contact contribution = `delta_sign * amount_paise`); NULL for all other types. Reversal does not use `delta_sign` (join-based negate).

#### Ledger effect rules (integer paise only)

| Type | Card outstanding contribution | Contact contribution (if `contact_id` set) |
|------|-------------------------------|--------------------------------------------|
| Existing MVP types | unchanged `_CARD_EFFECT` × amount | unchanged `_CONTACT_EFFECT` × amount |
| `adjustment` | `delta_sign * amount_paise` | same if contact set, else 0 |
| `reversal` | `−1 * _CARD_EFFECT[original.type] * amount` (join `reverses_id`) | `−1 * _CONTACT_EFFECT[original.type] * amount` |

Only rows with `posting_status=posted` enter any of the above (I2 filters).

#### Service functions

| Function | Behavior |
|----------|----------|
| `create_transaction(..., posting_status=POSTED \| DRAFT)` | Validate card/contact in org. Reject `type in {reversal, adjustment}` on this path (use reverse/adjust). Default **`posted`** (G2). Set `delta_sign=NULL`. Persist + activity log. |
| `create_draft(...)` | Thin wrapper → `create_transaction(..., posting_status=DRAFT)`. |
| `post_draft(tx_id)` | Load org-scoped tx; require `draft`; set `posted`; log. Idempotent if already posted → no-op or 409 — **prefer 409 `already_posted`**. |
| `update_transaction(tx_id, patch)` | Allow only if `draft`. Reject field changes to `posting_status` / reverse links via this path. |
| `delete_transaction(tx_id)` | Allow only if `draft`. Posted → error. |
| `reverse_transaction(tx_id, *, reason, occurred_at?)` | Require original `posted`, `type ≠ reversal`, `reversed_by_id is NULL`. Create new **posted** row: `type=reversal`, same card/contact/amount/currency, `reverses_id=original.id`, `correction_reason=reason` (required, min 1 char), `merchant` e.g. `Reversal of {original.merchant}`, `occurred_at` default now. Set `original.reversed_by_id=new.id`. Single DB transaction. Block double-reverse (`ConflictError`). |
| `adjust_balance(*, credit_card_id, delta_paise, reason, contact_id?, occurred_at?, merchant?)` | Require `delta_paise ≠ 0`. Create **posted** `type=adjustment`, `amount_paise=abs(delta_paise)`, `delta_sign=1 if delta>0 else -1`, `correction_reason=reason`. Merchant default `"Balance adjustment"`. |

#### HTTP surface (`/api/v1/transactions`)

| Method | Path | Maps to |
|--------|------|---------|
| `POST` | `/` | `create_transaction`; body adds optional `posting_status` (default `posted`) |
| `POST` | `/{id}/post` | `post_draft` |
| `POST` | `/{id}/reverse` | body: `{ "reason": str, "occurred_at"?: datetime }` |
| `POST` | `/adjust` | body: `{ credit_card_id, delta_paise, reason, contact_id?, occurred_at?, merchant? }` |
| `PATCH` | `/{id}` | `update_transaction` — **409/400 if posted** |
| `DELETE` | `/{id}` | `delete_transaction` — **409/400 if posted** |
| `GET` | `/` | unchanged list; add optional `posting_status` query filter; response includes new fields |

Do **not** expose silent mutate of posted rows. Opening-balance writer (`cards.py`) and import confirm (`statement_service`) call create with **`posted`** only (or set field explicitly on `Transaction(...)`).

#### Error codes (stable `AppError.code`)

| Code | HTTP | When |
|------|------|------|
| `posted_immutable` | 409 | PATCH/DELETE on posted |
| `already_posted` | 409 | `post` on already posted |
| `not_draft` | 400 | `post` on non-draft (if not already_posted) |
| `already_reversed` | 409 | reverse when `reversed_by_id` set |
| `cannot_reverse` | 400 | reverse a reversal, or non-posted |
| `invalid_delta` | 400 | adjust with `delta_paise == 0` |
| `invalid_posting_type` | 400 | create with type adjustment/reversal |

#### Pydantic (I3)

- `TransactionCreate`: + `posting_status: PostingStatus = POSTED` (exclude adjustment/reversal from `type` via validator or service check)
- `TransactionResponse`: + `posting_status`, `reverses_id`, `reversed_by_id`, `correction_reason`, `delta_sign`
- `TransactionReverseRequest`, `TransactionAdjustRequest` as above
- `TransactionUpdate`: unchanged fields; service enforces draft-only

#### Activity log

Add enum values when implementing I3: `TRANSACTION_POST`, `TRANSACTION_REVERSE`, `TRANSACTION_ADJUST` (or reuse CREATE with metadata). Prefer dedicated actions for audit clarity.

#### Out of P2 / I3 scope

- Correct Balance UI (US-02 accounts) — same `adjust` endpoint reusable later
- Transfer / split posting rules (US-03)
- Soft-delete of posted rows

### US-01.P3 — Frontend shape brief (2026-08-05)

**Impeccable:** `context.mjs` run (Operate; Ledger Shelf / PRODUCT+DESIGN). `shape` for ledger posting UX. **Assumptions** (Ralph autonomous — no human interview): refine existing `/app/transactions` only; post-by-default (G2); Correct = reverse dialog + optional adjust entry later (adjust primary UI can wait for US-02 Correct Balance; US-01 ships Reverse + draft/post + status badge).

#### Job and audience
Owner scanning/adding ledger lines in a dense ops table (Zerodha/Kite-like scan). Need: know draft vs posted at a glance; post incomplete rows; correct mistakes without silent delete.

#### Outcome and proof
1. Create still feels one-step (primary posts). 2. Drafts visible, editable, postable; do not change balances until posted. 3. Posted rows: no Delete; Reverse requires reason. 4. Status badge readable in mono/small type like existing type badges.

#### Selected direction
- **Visual authority:** preserve incumbent transactions page (filter card + dense table + inline form). No new visual world.
- **Thesis:** status as a quiet second badge beside type; row actions swap by status; confirmations via small dialog (reason required) — not a redesign.
- **Focal moment:** Reverse dialog — short plain copy (“This posts a reversing entry. The original stays for audit.”) + required reason + confirm.

#### Scope and boundaries
| In | Out |
|----|-----|
| List: posting status badge + filter | Full transaction detail page |
| Form: primary Post / Add transaction; secondary Save draft | Purple chips, glow, nested card chrome |
| Draft row: Edit (inline or reuse form), Delete, Post | Soft-delete posted |
| Posted row: Reverse (dialog); hide Delete; no silent edit | Heavy Correct Balance wizard (US-02 uses `/adjust`) |
| Optional: link/badge when `reversed_by_id` / type=reversal | Adjust dialog on this page in US-01 (API exists; UI deferred to accounts Correct Balance unless trivial) |

#### States and ranges
- Empty: keep EmptyState; mention drafts optional.
- Loading: keep compact text/skeleton later.
- Mixed list: mostly posted; few drafts — drafts may use slightly muted merchant row or Draft badge only (prefer badge, not whole-row tint).
- Already reversed: show muted “Reversed” cue; Reverse disabled; keep history.
- Error: map `posted_immutable` / `already_reversed` to clarify-friendly toast/inline text.

#### Interaction and layout
1. **Filters:** add Status select (All / Posted / Draft) beside Type; same `h-8` selects.
2. **Table columns:** keep When / Merchant / Card / Who / Type / Amount / actions. Add **Status** (narrow) after Type, or combine Type cell: type outline badge + status badge (`Draft` = `secondary`; `Posted` = `outline` muted). Prefer **Status column** for scanability.
3. **Form actions:** `[ Add transaction ]` primary (posts); `[ Save draft ]` outline secondary; Cancel unchanged.
4. **Draft actions:** `Post` (primary sm) · `Delete` (ghost). Edit: optional — if no edit UI today, Post + Delete only for US-01; PATCH can wait if form lacks edit mode (today only Delete). **Decision:** US-01 ships Post + Delete for drafts; inline edit deferred unless cheap (no edit form today).
5. **Posted actions:** replace Delete with `Reverse` ghost/outline. Opens dialog: reason (required textarea), optional occurred_at default now, Cancel / Reverse entry.
6. **Dialog:** add shadcn/base-ui Dialog if missing; portal overlay; focus trap; Esc cancels. Motion 150–250ms.
7. **Money:** mono/tabular INR; reversal rows may show as reducing (same emerald cue as refund) or neutral with type badge `reversal`.

#### Components to touch (I4)
- `frontend/src/lib/api/transactions.ts` — types + `postTransaction` / `reverseTransaction` / `posting_status` on create
- `features/transactions/transaction-form.tsx` — dual submit
- `app/app/transactions/page.tsx` — badge, filter, actions, dialog
- New: `features/transactions/reverse-transaction-dialog.tsx` (or colocated)
- Reuse `Badge`, `Button`, `Card`; add Dialog primitive if absent

#### Copy (clarify-ready)
- Draft badge: “Draft”
- Posted badge: “Posted” (or omit Posted badge and only show Draft — **prefer show both** for teaching)
- Reverse title: “Reverse transaction”
- Body: “Posts a linked reversing entry for the same amount. The original line stays on the ledger.”
- Reason label: “Reason” / placeholder “Wrong amount, duplicate, …”
- Confirm: “Reverse entry”
- Save draft success: stay on list; Draft badge visible
- `posted_immutable`: “Posted entries can’t be edited or deleted. Reverse instead.”

#### Anti-goals
- No dashboard-style KPI strip on this page
- No pill rainbow status colors; stick to Badge variants already in shell
- Don’t nest the table inside extra decorative panels

#### Open for builder (do not invent contrary)
- Adjust UI deferred to US-02 Correct Balance (P2 API still ships)
- Draft edit-in-place deferred (no edit form today)
- Confirm dialog component: install/adapt from existing UI kit patterns

### US-01.P4 — Test matrix (2026-08-05)

**Approach:** Prefer domain/service unit tests with FakeSession (match `test_org_authz` / `test_statement_guards`). Extract pure **ledger contribution** helpers if SQL `case` aggregates are hard to stub — balance assertions then call helpers over in-memory rows filtered to `posted`. Full DB integration optional later; not required for T1–T4 green.

**New files (suggested):**
| File | Covers |
|------|--------|
| `backend/tests/test_ledger_posting.py` | T1–T3 domain/ledger + reverse/adjust service rules |
| `backend/tests/test_transaction_api_posting.py` | T4 HTTP immutability + reverse/adjust (TestClient + dep overrides **or** service-level if HTTP wiring thin) |

Keep `test_money.py` / parsers unchanged unless regressions.

#### Map to story Test subtasks

| ID | Case | Arrange | Assert |
|----|------|---------|--------|
| **T1** | Draft excluded from card outstanding | Posted purchase 100_00 + draft purchase 50_00 same card | `card_outstanding` / helper sum == 100_00 only |
| **T1** | Draft excluded from contact balance | Posted purchase w/ contact 80_00 + draft 20_00 same contact; no settlements | contact balance == 80_00 |
| **T1** | Draft-only org | Only draft rows | card/contact outstanding == 0 |
| **T1** | Post draft then included | Create draft → `post_draft` → outstanding increases by amount | balances update once |
| **T2** | Reversal negates purchase | Posted purchase 250_00 → reverse | outstanding delta −250_00; reversal `type=reversal`, `reverses_id` set; original `reversed_by_id` set |
| **T2** | Reversal negates refund | Posted refund 40_00 (reduces outstanding) → reverse | outstanding returns +40_00 |
| **T2** | Double-reverse blocked | Reverse once → reverse again | raises `ConflictError` / `already_reversed`; no second row |
| **T2** | Cannot reverse a reversal | Reverse of purchase exists → reverse the reversal row | `cannot_reverse` |
| **T2** | Cannot reverse draft | Draft purchase → reverse | 400 `cannot_reverse` / not posted |
| **T3** | Adjustment +delta | `adjust(delta_paise=+150_00)` | posted adjustment; outstanding +150_00; `delta_sign=1`; `amount_paise=150_00` |
| **T3** | Adjustment −delta | `adjust(delta_paise=-75_00)` | outstanding −75_00; `delta_sign=-1`; `amount_paise=75_00` |
| **T3** | Zero delta rejected | `delta_paise=0` | `invalid_delta` |
| **T3** | Adjustment with contact | delta + contact_id | contact balance moves by signed delta; card too |
| **T4** | PATCH posted → 4xx | Posted tx PATCH amount | 409 `posted_immutable` |
| **T4** | DELETE posted → 4xx | Posted tx DELETE | 409 `posted_immutable` |
| **T4** | PATCH/DELETE draft OK | Draft PATCH merchant / DELETE | 200 / 204 |
| **T4** | POST reverse OK | Authz member + posted + reason | 201; links set |
| **T4** | POST adjust OK | Authz member + card in org | 201 adjustment |
| **T4** | Cross-org denied | Foreign org / wrong card | 403/404 (existing org patterns) |
| **T4** | Create rejects type=reversal\|adjustment | POST `/` with those types | 400 `invalid_posting_type` |
| **T4** | Create default posted | POST without posting_status | response `posted`; balances move |
| **T4** | Create draft | `posting_status=draft` | balances unchanged |
| **I5 / smoke** | Import confirm posts | (extend `test_statement_guards` or service stub) import creates rows with `posted` | no draft from confirm |
| **T5** | DoD commands | After I1–I4 | `uv run pytest`, `ruff`, `mypy app`; frontend `lint` + `typecheck` |

#### Pure helper contract (recommended extract for testability)

```text
posted_rows(rows) -> filter posting_status == posted
card_contribution(tx, original=None) -> int paise
contact_contribution(tx, original=None) -> int paise
```

Reversal uses `original` for effect negate; adjustment uses `delta_sign * amount_paise`.

#### Fixtures / factories (shared in test module)

- `make_tx(**overrides)` → SimpleNamespace or Transaction-like with defaults: purchase, posted, amount 100_00, ids.
- Org/card/contact UUIDs stable per test.
- No float math; all amounts integer paise literals (`100_00` style OK as int 10000).

#### Out of matrix (explicit)

- Frontend component tests (manual V1–V4 + lint/typecheck)
- Migration upgrade in CI DB (manual/smoke in I1; balance-drift equality: “all preexisting rows posted ⇒ posted-filter sum == unfiltered sum”)
- EMI / transfer / income-expense exclusion (later stories)

#### Implementation order for Test phase

1. Helpers + T1/T2/T3 in `test_ledger_posting.py` (can land with I2/I3)
2. T4 immutability + reverse/adjust after I3 routes
3. Import posted assertion with I5
4. T5 full DoD

- Plan phase complete. Implement starts at I1.

### US-01.I2 — Posted balance filters (2026-08-05)

Implemented:
- `app/domain/ledger.py` — pure `card_contribution_paise` / `contact_contribution_paise` (draft→0; adjustment via `delta_sign`; reversal negates original type effects).
- `ledger_service` — all card/contact outstanding queries filter `posting_status=posted`; outer-join original for reversal math; adjustment/reversal included in SQL case expressions.
- Tests: `tests/test_ledger_posting.py` (T1/T2/T3 contribution coverage).

### US-01.I3 — Transaction API (2026-08-05)

Implemented:
- `transaction_service`: create (default posted) / post_draft / update+delete draft-only / reverse / adjust.
- Routes: `POST /adjust`, `POST /{id}/post`, `POST /{id}/reverse`; list filter `posting_status`.
- Schemas: posting fields on response; create/reverse/adjust request models.
- Activity actions + Alembic `20260805_0004`.
- Opening balance + statement import set `posting_status=posted` explicitly.
- Tests: `tests/test_transaction_api_posting.py` (immutability, reverse, adjust).

### US-01.I4 — Ledger UI (2026-08-05)

Implemented (Impeccable Operate / Ledger Shelf craft-floor):
- API client: `PostingStatus`, posting fields, `postTransaction` / `reverseTransaction`.
- Form: primary **Add transaction** (posted) + outline **Save draft**.
- List: Status filter + Status column badges; draft Post/Delete; posted Reverse dialog (reason required).
- `components/ui/dialog.tsx` centered modal; `reverse-transaction-dialog.tsx`.
- Adjust UI deferred to US-02 per P3.

### US-01.I5 — Import confirm posts only (2026-08-05)

- Extracted `_posted_transaction_from_import_line` (always `PostingStatus.POSTED`).
- Docstring on `import_statement`: never creates drafts.
- Tests: `test_import_confirm_creates_posted_transactions_only` + helper unit test.

### US-01.T1 — Draft excluded from outstanding (2026-08-05)

Covered P4 matrix:
- Card mix posted+draft → 100_00 only
- Contact mix posted+draft → 80_00 only
- Draft-only → 0 card/contact
- Post draft → contribution flips 0 → amount (domain + `post_draft` service)

### US-01.T5 — DoD (2026-08-05)

| Check | Result |
|-------|--------|
| `uv run pytest` | 79 passed |
| `uv run ruff check .` | green (fixed pre-existing I001 in `tests/conftest.py`, `tests/test_billing.py`) |
| `uv run mypy app` | 1 pre-existing error: `statement_service.create_statement_from_upload` untyped `period_start`/`period_end` — documented in GOTCHAS; not US-01 |
| frontend `bun run lint` | pass |
| frontend `bun run typecheck` | pass |

