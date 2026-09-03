# US-P06 — Durable statement ingestion

| Field | Value |
| --- | --- |
| **Status** | `todo` |
| **Sequence** | 6 |
| **Depends on** | [US-P01](US-P01-production-release-gate.md), [US-P03](US-P03-supabase-security-boundary.md) |
| **One-loop objective** | Upload statements directly to private Supabase Storage and keep ingestion within safe resource limits. |
| **Primary boundaries** | Statement UI/API, signed Supabase Storage upload, private bucket, parser entrypoint |

## User story

**As** a Fin Buddy owner
**I want** my statement files to upload reliably and remain available after a deployment
**So that** statement review is not limited by the Vercel proxy or ephemeral FastAPI disk.

## Why this matters

The backend accepts files up to 15 MB, but the Next.js BFF has a 4.5 MB
function request-body limit. Passing a large file through Vercel can therefore
fail before FastAPI receives it. FastAPI Cloud local disk is also not a durable
statement store.

## Scope and non-goals

In scope: authenticated signed upload URL/session, private object paths,
ownership, content limits, finalize/parse handoff, cleanup, and resource
guards. Out of scope: detailed statement-review UI, covered by US-P12.

## Touchpoints

- [`frontend/src/lib/api/statements.ts`](../../../frontend/src/lib/api/statements.ts)
- [`frontend/src/app/app/statements/page.tsx`](../../../frontend/src/app/app/statements/page.tsx)
- [`backend/app/api/v1/statements.py`](../../../backend/app/api/v1/statements.py)
- [`backend/app/services/storage.py`](../../../backend/app/services/storage.py)
- [`backend/app/services/statement_service.py`](../../../backend/app/services/statement_service.py)
- [`backend/app/core/upload_limits.py`](../../../backend/app/core/upload_limits.py)
- [`backend/.env.example`](../../../backend/.env.example)

## Acceptance criteria

1. Files larger than 4.5 MB no longer pass through the Vercel BFF request body.
2. Uploads use a short-lived, authenticated, organization-scoped signed path
   in the private `statements` bucket; clients cannot choose another user or
   organization path.
3. Server and bucket limits agree on size and allowed MIME/extensions, and
   malformed/mislabelled files are rejected before parsing.
4. The backend records only metadata/object path and uses Supabase Storage on
   FastAPI Cloud; no statement depends on local disk after redeploy.
5. Failed, abandoned, and parse-rejected uploads have a bounded cleanup path.
6. Parser input is bounded by file size, row/sheet count, decompression/resource
   limits, and a timeout or bounded worker mechanism.
7. Existing small-file review/import behavior remains intact and is covered by
   automated tests.

## Tasks

### Gather

- [ ] **US-P06.G1 — Trace the current upload.** Follow file selection → browser
  request → BFF body forwarding → FastAPI multipart parsing → storage write →
  statement row → parse. Record size limits, MIME checks, object paths, and
  cleanup behavior.
- [ ] **US-P06.G2 — Confirm provider capabilities.** Verify the private bucket,
  current bucket restrictions, Storage policies, service-role usage, and the
  actual FastAPI Cloud storage env. Do not expose keys or upload personal data.
- [ ] **US-P06.G3 — Build resource fixtures.** Prepare safe test fixtures for
  valid PDF/CSV/XLSX/TXT, a file just over the BFF limit, a malformed file, an
  oversized row/sheet case, and an abandoned object.

### Plan

- [ ] **US-P06.P1 — Define the upload protocol.** Choose endpoint names and
  sequence: authorize metadata → issue signed upload URL → browser uploads →
  finalize/validate object → create statement/parse. Define expiry, retries,
  checksum/content-length behavior, and cleanup ownership.
- [ ] **US-P06.P2 — Define object isolation.** Use server-generated paths that
  include the organization/user scope and random identity. Define how every
  download, parse, delete, and re-parse verifies ownership.
- [ ] **US-P06.P3 — Define parser budgets.** Set maximum bytes, rows, columns,
  sheets, PDF pages, decompressed size, execution time, and memory strategy.
  Decide how a limit failure appears in the statement state machine.

### Implement

- [ ] **US-P06.I1 — Add signed upload preparation.** Create an authenticated
  backend/BFF contract that validates file metadata and returns a short-lived
  signed upload instruction without exposing the service-role key.
- [ ] **US-P06.I2 — Upload directly from the browser.** Change the statement
  client to send the file to private Supabase Storage, then send only the
  object path/metadata through the BFF. Keep progress, abort, retry, and
  duplicate-submit behavior explicit for the later UI story.
- [ ] **US-P06.I3 — Finalize safely.** Validate object ownership, size, content
  type, and existence before creating or updating the statement record. Make
  failed finalization and parse cancellation clean up unreferenced objects.
- [ ] **US-P06.I4 — Bound parsing.** Enforce the parser budgets and move blocking
  work off the async event loop or into a bounded mechanism appropriate for the
  current free-tier runtime. Return generic resource-limit errors.
- [ ] **US-P06.I5 — Set provider restrictions.** Apply private bucket size/MIME
  restrictions where supported and keep application validation as defense in
  depth. Document the final limits in the env example and deployment runbook.

### Test

- [ ] **US-P06.T1 — Test proxy bypass.** Prove a file above 4.5 MB reaches the
  signed Storage path and no large multipart body reaches the Vercel BFF.
- [ ] **US-P06.T2 — Test ownership.** Attempt cross-user, cross-organization,
  expired-signed-URL, guessed-path, wrong-MIME, and finalize-after-delete
  operations; assert every unsafe path fails.
- [ ] **US-P06.T3 — Test parser limits.** Exercise valid formats, malformed
  inputs, oversized resources, cancellation, timeout, and cleanup. Assert the
  event loop remains responsive for blocking parse work.
- [ ] **US-P06.T4 — Run regression gates.** Run statement API/parser tests,
  backend quality gates, frontend lint/typecheck/build, and a browser upload
  smoke with a non-sensitive fixture.

### Validate

- [ ] **US-P06.V1 — Verify durability.** Upload a safe test fixture, redeploy or
  restart the API, and confirm the statement object and metadata remain
  available from private Storage.
- [ ] **US-P06.V2 — Verify review handoff.** Confirm the new protocol reaches
  the existing human-review/import state machine without auto-posting or
  changing ledger semantics.
- [ ] **US-P06.V3 — Close the story.** Record limits, Storage policy evidence,
  protocol contract, test fixtures, and any provider limitation in this file
  and [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- Current and final size/MIME limits.
- Signed URL expiry and path-isolation rules.
- Large-file request trace proving BFF bypass.
- Storage policy and post-restart durability check.
- Parser resource-limit test results.

## Safety notes

Never put the Supabase service-role key in browser code. Never accept a client
chosen object path without verifying organization ownership. Do not use a real
bank statement as a test fixture.

## Story notes

_(Append dated implementation decisions and evidence here.)_
