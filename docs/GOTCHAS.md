# Project Gotchas & Retired Claims

Agents must review this document to avoid common pitfalls in this specific repository.

## Architecture Boundaries
- Do NOT share types or models directly between the frontend and backend directories. They must remain decoupled. Rely on the API schema contract instead.

## Supabase Quirks
- Service-role keys must NEVER be exposed to the frontend. They are backend-only.
- Always check the allowed redirect URLs in Supabase if authentication flows fail locally.
- Statement PDFs: use `STATEMENT_STORAGE_BACKEND=supabase` on FastAPI Cloud. Local disk is ephemeral there.

## Alembic / Postgres enums
- Extending `transaction_type` with `ALTER TYPE … ADD VALUE` is one-way: downgrade of `20260805_0003` drops ledger columns and `posting_status`, but **cannot** remove `'adjustment'` / `'reversal'` labels from `transaction_type`. Do not recreate that enum to “clean” labels — it is shared with `statement_line_candidates.proposed_type`.
- Same for `activity_action` labels added in `20260805_0004` (`transaction_post` / `transaction_reverse` / `transaction_adjust`).
- `accounts` RLS (`20260805_0005`): ENABLE without FORCE; membership policies created only when `auth.uid()` exists (Supabase). Plain Postgres CI skips policies. FastAPI org checks remain the source of truth for the service-role pool.
- Card→account backfill uses Python `uuid4` (no `gen_random_uuid` dependency).

## Typing
- `mypy app` reports a pre-existing `no-untyped-def` on `create_statement_from_upload` in `statement_service.py` (`period_start` / `period_end` lack annotations). Not introduced by Release 2 US-01; fix separately when touching statement upload.

## Retired Approaches
- *(Add any technical approaches that were tried and failed here, so agents do not attempt them again)*
