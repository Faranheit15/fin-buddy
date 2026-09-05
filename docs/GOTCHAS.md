# Project gotchas and retired claims

Review this document before changing code or release configuration. It records
repository-specific pitfalls that are easy to miss when working from general
framework knowledge. See [`ROUTING.md`](ROUTING.md) for code locations and
[`CONTEXT.md`](CONTEXT.md) for the active release focus.

## Architecture boundaries
- Do NOT share types or models directly between the frontend and backend directories. They must remain decoupled. Rely on the API schema contract instead.

## Supabase quirks
- Service-role keys must NEVER be exposed to the frontend. They are backend-only.
- Always check the allowed redirect URLs in Supabase if authentication flows fail locally.
- Statement PDFs: use `STATEMENT_STORAGE_BACKEND=supabase` on FastAPI Cloud. Local disk is ephemeral there.
- Supabase Free can pause low-activity projects after about a week. A daily
  protected `/ready` request is only a best-effort activity experiment; it must
  not write dummy financial data or be described as a no-sleep guarantee.

## Free-tier and agent tooling
- The $0 target is conditional on current provider terms, quotas, and personal/non-commercial use rules. Never upgrade a plan, attach billing, use paid AI, or add paid infrastructure without explicit owner approval.
- The three agent surfaces use different hook schemas. Use the native manifests in `.agents/hooks.json` and `.claude/settings.json` around the shared local scripts in `tools/agent-hooks/`; do not copy one vendor's JSON into another.
- Human decisions and credential destinations live in `user-input-needed.md`. Never record a credential value there or in an agent transcript.

## Alembic / Postgres enums
- Extending `transaction_type` with `ALTER TYPE … ADD VALUE` is one-way: downgrade of `20260805_0003` drops ledger columns and `posting_status`, but **cannot** remove `'adjustment'` / `'reversal'` labels from `transaction_type`. Do not recreate that enum to “clean” labels — it is shared with `statement_line_candidates.proposed_type`.
- Same for `activity_action` labels added in `20260805_0004` (`transaction_post` / `transaction_reverse` / `transaction_adjust`).
- `accounts` RLS (`20260805_0005`): ENABLE without FORCE; membership policies created only when `auth.uid()` exists (Supabase). Plain Postgres CI skips policies. FastAPI org checks remain the source of truth for the service-role pool.
- Card→account backfill uses Python `uuid4` (no `gen_random_uuid` dependency).

## Settlements and obligations

- Keep the existing `settlements` flow for contact balances derived from
  ad-hoc shared card spend.
- Treat `obligations` and `obligation_payments` as separate first-class debts
  and loans. Do not merge them into settlement rows.
- The dashboard friend-dues KPI excludes obligations so the same repayment is
  not counted twice. Receivable and payable obligations remain visible in the
  debt/loan surfaces and upcoming-dues feed.

## Typing
- `mypy app` reports a pre-existing `no-untyped-def` on `create_statement_from_upload` in `statement_service.py` (`period_start` / `period_end` lack annotations). Not introduced by Release 2 US-01; fix separately when touching statement upload.

## Retired approaches
- *(Add any technical approaches that were tried and failed here, so agents do not attempt them again)*
