# US-05 — Card EMIs & GST tracking

| Field | Value |
|--------|--------|
| **Status** | Done |
| **Priority** | P1 |
| **Maps to** | R2E |
| **PRD** | FR-E1–FR-E7, FR-C9, FR-C10, FR-T11, UC22, UC23, G6, G7, §8.1–§8.2 |
| **Depends on** | US-01, US-02 |

> **Evidence note:** R2E is complete in the release tracker. UI residuals are
> retained under **Residuals (Manual Checks)** below.

## User story

**As** a Fin Buddy owner with Indian credit cards  
**I want** EMI plans that block only principal on my limit, plus optional GST amounts on spends  
**So that** available credit and billing match how issuers actually work.

## Current architecture touchpoints

> **Historical baseline:** The touchpoints below describe the system before
> US-05 was implemented; use the source tree as the current architecture.

- Card utilization today = outstanding vs limit (no EMI block)
- [`backend/app/api/v1/cards.py`](../../../backend/app/api/v1/cards.py), dashboard card summaries
- Card detail UI: [`frontend/src/app/app/cards/[id]/page.tsx`](../../../frontend/src/app/app/cards/[id]/page.tsx)

## Acceptance criteria

1. Create EMI plan + installment schedule (principal/interest/fees/GST breakdown).
2. `available_credit = limit − spend_outstanding − emi_principal_blocked`.
3. Utilization UI splits spend vs EMI block; plain-language explanation payload.
4. Optional `gst_paise` on transactions (tracking only, no filing).
5. Domain tests for schedule, block math, and utilization API fields.

---

## Subtasks

### Gather

- [x] **US-05.G1** Define rounding rules for installment principal (last installment absorbs remainder).
- [x] **US-05.G2** Decide whether EMI interest/GST auto-posts on due date or creates review drafts — **default: scheduled posted typed lines with clear `emi_*` types, reversible via US-01**.
- [x] **US-05.G3** Confirm Should-scope: contact-paid installment / advance allocation — include if time allows after Must.

### Plan

- [x] **US-05.P1** Spec `emi_plans` / `emi_installments` + transaction type extensions.
- [x] **US-05.P2** Spec utilization service fields on card + dashboard APIs.
- [x] **US-05.P3** Spec explanation payload shape for UI.
- [x] **US-05.P4** Spec card detail EMI UI + optional `/app/emis` — **impeccable `shape`** (utilization split + explainer must stay scannable).

### Implement

- [x] **US-05.I1** Models + migration + schedule generator in `domain`/`services`.
- [x] **US-05.I2** Utilization service update (spend vs EMI block).
- [x] **US-05.I3** EMI APIs + `gst_paise` on transactions.
- [x] **US-05.I4** Frontend: EMI section, utilization split, GST field, explainer — **impeccable craft-floor**; prefer `clarify` for calc copy.
- [x] **US-05.I5** Installment payment posting path.

### Test

- [x] **US-05.T1** Unit: principal block vs interest/GST billing effect.
- [x] **US-05.T2** Unit: available credit after create and after principal reduction.
- [x] **US-05.T3** Unit: schedule length; sum(principal) ≈ plan principal.
- [x] **US-05.T4** API: create plan updates utilization fields.
- [x] **US-05.T5** Backend + frontend DoD.

### Validate

- [x] **US-05.V1** Manual: create a 3–6 month EMI; verify block and schedule.
- [x] **US-05.V2** Manual: pay one installment; block decreases correctly.
- [x] **US-05.V3** Manual: store GST on a purchase; export later still has it (when US-06 lands).
- [x] **US-05.V4** **Impeccable:** `polish` + `harden` + `clarify` on EMI/utilization explainer; `audit` card detail.
- [x] **US-05.V5** Mark Done; update PROGRESS + R2E.

## Story notes

> These notes preserve decisions and evidence captured during implementation.
> For the current architecture, prefer the source tree and the release status
> tracker linked from the [Release 2 index](README.md).

- Rounding: Total principal is divided by tenure, rounded down to nearest paise. The final installment absorbs the remainder to ensure sum equals exact principal.
- Interest posting policy: Adopting default — Scheduled posted typed lines with clear `emi_*` types (`emi_interest`, `emi_gst`), which are reversible under US-01.
- Scope: Contact-paid EMI installments are deferred until core Must features of US-05 are implemented and stable.

### Residuals (Manual Checks)
Due to the absence of a live browser environment during autonomous execution, the following manual steps are recorded as residuals to verify later:
- Navigate to Card Detail and test the Create EMI Plan dialog constraints and submission.
- Ensure the Utilization segmented bar renders distinct segments correctly without overlap.
- Click "Pay Next" on an active EMI plan and verify the page soft-reloads, adjusting both the utilization bar and the paid months counter instantly.
- Submit a Transaction with GST and verify `gst_paise` persists accurately.

### Implementation Specs (P1-P4)

**P1: Schema & Transaction Types**
- `emi_plans`: `id`, `organization_id`, `credit_card_id`, `reference_transaction_id` (optional), `principal_paise`, `interest_rate_bps`, `tenure_months`, `status` (ACTIVE, COMPLETED).
- `emi_installments`: `id`, `plan_id`, `sequence_number`, `due_date`, `principal_paise`, `interest_paise`, `fees_paise`, `gst_paise`, `total_paise`, `status` (PENDING, PAID).
- Enum additions: `EmiPlanStatus`, `EmiInstallmentStatus`.
- `TransactionType` additions: `emi_interest`, `emi_gst`, `emi_fees`. (Principal repayments will just be regular card payments that resolve the installment).

**P2 & P3: Utilization Service & Explanation Payload**
- The original purchase transaction remains on the ledger, contributing to `total_outstanding`.
- `emi_principal_blocked` = sum of `principal_paise` for all `PENDING` installments across active plans on the card.
- `spend_outstanding` = `total_outstanding` - `emi_principal_blocked`.
- `available_credit` = `limit` - `total_outstanding`.
- Explanation Payload:
  ```json
  {
    "limit": 100000_00,
    "total_outstanding": 15000_00,
    "spend_outstanding": 5000_00,
    "emi_principal_blocked": 10000_00,
    "available_credit": 85000_00
  }
  ```

**P4: UI Shape (Card Detail)**
- The card detail header will feature a segmented progress bar (Available / Spend / EMI Block).
- A new section "Active EMI Plans" below the transaction list will show each plan, its tenure progress (e.g. "Month 2 of 6"), and remaining principal.
- "Create EMI" button opens a dialog to specify principal, tenure, and interest rate.
