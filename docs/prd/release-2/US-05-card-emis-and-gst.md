# US-05 — Card EMIs & GST tracking

| Field | Value |
|--------|--------|
| **Status** | Todo |
| **Priority** | P1 |
| **Maps to** | R2E |
| **PRD** | FR-E1–FR-E7, FR-C9, FR-C10, FR-T11, UC22, UC23, G6, G7, §8.1–§8.2 |
| **Depends on** | US-01, US-02 |

## User story

**As** a Fin Buddy owner with Indian credit cards  
**I want** EMI plans that block only principal on my limit, plus optional GST amounts on spends  
**So that** available credit and billing match how issuers actually work.

## Current architecture touchpoints

- Card utilization today = outstanding vs limit (no EMI block)
- [`backend/app/api/v1/cards.py`](../../../../backend/app/api/v1/cards.py), dashboard card summaries
- Card detail UI: [`frontend/src/app/app/cards/[id]/page.tsx`](../../../../frontend/src/app/app/cards/[id]/page.tsx)

## Acceptance criteria

1. Create EMI plan + installment schedule (principal/interest/fees/GST breakdown).
2. `available_credit = limit − spend_outstanding − emi_principal_blocked`.
3. Utilization UI splits spend vs EMI block; plain-language explanation payload.
4. Optional `gst_paise` on transactions (tracking only, no filing).
5. Domain tests for schedule, block math, and utilization API fields.

---

## Subtasks

### Gather

- [ ] **US-05.G1** Define rounding rules for installment principal (last installment absorbs remainder).
- [ ] **US-05.G2** Decide whether EMI interest/GST auto-posts on due date or creates review drafts — **default: scheduled posted typed lines with clear `emi_*` types, reversible via US-01**.
- [ ] **US-05.G3** Confirm Should-scope: contact-paid installment / advance allocation — include if time allows after Must.

### Plan

- [ ] **US-05.P1** Spec `emi_plans` / `emi_installments` + transaction type extensions.
- [ ] **US-05.P2** Spec utilization service fields on card + dashboard APIs.
- [ ] **US-05.P3** Spec explanation payload shape for UI.
- [ ] **US-05.P4** Spec card detail EMI UI + optional `/app/emis` — **impeccable `shape`** (utilization split + explainer must stay scannable).

### Implement

- [ ] **US-05.I1** Models + migration + schedule generator in `domain`/`services`.
- [ ] **US-05.I2** Utilization service update (spend vs EMI block).
- [ ] **US-05.I3** EMI APIs + `gst_paise` on transactions.
- [ ] **US-05.I4** Frontend: EMI section, utilization split, GST field, explainer — **impeccable craft-floor**; prefer `clarify` for calc copy.
- [ ] **US-05.I5** Installment payment posting path.

### Test

- [ ] **US-05.T1** Unit: principal block vs interest/GST billing effect.
- [ ] **US-05.T2** Unit: available credit after create and after principal reduction.
- [ ] **US-05.T3** Unit: schedule length; sum(principal) ≈ plan principal.
- [ ] **US-05.T4** API: create plan updates utilization fields.
- [ ] **US-05.T5** Backend + frontend DoD.

### Validate

- [ ] **US-05.V1** Manual: create a 3–6 month EMI; verify block and schedule.
- [ ] **US-05.V2** Manual: pay one installment; block decreases correctly.
- [ ] **US-05.V3** Manual: store GST on a purchase; export later still has it (when US-06 lands).
- [ ] **US-05.V4** **Impeccable:** `polish` + `harden` + `clarify` on EMI/utilization explainer; `audit` card detail.
- [ ] **US-05.V5** Mark Done; update PROGRESS + R2E.

## Story notes

- Rounding:
- Interest posting policy:
