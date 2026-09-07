# US-P02 — Google OAuth that completes

| Field | Value |
| --- | --- |
| **Status** | `in_progress` |
| **Sequence** | 2 |
| **Depends on** | [US-P01](US-P01-production-release-gate.md) |
| **One-loop objective** | Make Google sign-in complete a secure browser-to-Supabase-to-Fin-Buddy session flow. |
| **Primary boundaries** | Login UI, OAuth URL builder, callback page, Supabase Auth, Google Cloud OAuth |

## User story

**As** a Fin Buddy user
**I want** to sign in with my Google account and return to the page I intended to open
**So that** authentication is as reliable as email login and never becomes an open redirect.

## Why this matters

The live Supabase Auth configuration reports Google disabled. Independently, the
frontend sends a callback containing `?next=...`, while the backend rejects
callback query strings. The live failure is therefore a code contract bug and a
provider-configuration gap, not only a missing environment variable.

## Scope and non-goals

In scope: fixed callback contract, safe destination state, provider setup,
PKCE/code exchange decision, callback session establishment, and regression
tests. Out of scope: replacing Supabase Auth or adding other social providers.

## Touchpoints

- [`frontend/src/features/auth/login-form.tsx`](../../../frontend/src/features/auth/login-form.tsx)
- [`frontend/src/app/auth/callback/page.tsx`](../../../frontend/src/app/auth/callback/page.tsx)
- [`frontend/src/lib/api/auth.ts`](../../../frontend/src/lib/api/auth.ts)
- [`frontend/src/lib/auth/oauth.ts`](../../../frontend/src/lib/auth/oauth.ts)
- [`frontend/src/lib/auth/oauth.test.ts`](../../../frontend/src/lib/auth/oauth.test.ts)
- [`backend/app/api/v1/auth.py`](../../../backend/app/api/v1/auth.py)
- [`backend/app/services/auth_service.py`](../../../backend/app/services/auth_service.py)
- [`backend/tests/test_auth_redirects.py`](../../../backend/tests/test_auth_redirects.py)
- [`docs/DEPLOY.md`](../../DEPLOY.md)

## Acceptance criteria

1. Clicking Google no longer sends a callback URL that the backend rejects.
2. Only the exact configured callback origin/path is accepted; arbitrary
   domains, fragments, and unsafe destinations are rejected.
3. The chosen OAuth flow is documented and implemented consistently. If PKCE is
   chosen, authorization codes are exchanged securely; if implicit flow is
   retained temporarily, the accepted token surface and risk are explicit.
4. Supabase Google provider configuration and Google Cloud redirect/origin
   configuration are complete without putting Google secrets in frontend env.
5. A real browser sign-in establishes the BFF session and returns to the
   allowlisted relative destination.
6. Provider-disabled, callback-error, expired-state, and session-refresh paths
   show recoverable, non-secret errors.

## Tasks

### Gather

- [x] **US-P02.G1 — Reproduce the current failure.** Capture the request shape
  from the deployed login button and the backend response for both the bare
  callback and the current `?next=/app` callback. Record the exact configured
  app callback URL without recording OAuth secrets or tokens.
- [x] **US-P02.G2 — Map the full flow.** Trace login button → BFF → FastAPI
  OAuth URL → Supabase authorize endpoint → provider → Supabase callback → app
  callback page → backend session endpoint → BFF cookie. Identify where state,
  code, hash tokens, refresh tokens, and `next` are handled.
- [x] **US-P02.G3 — Inspect provider settings safely.** Confirm the active
  Supabase project, provider enabled/disabled status, Site URL, app redirect
  allow-list, and the required Google Cloud Web OAuth client fields. Never print
  client secrets or access tokens.

### Plan

- [x] **US-P02.P1 — Choose the callback contract.** Prefer one fixed app
  callback URL such as `/auth/callback`. Carry `next` through a short-lived,
  origin-bound state mechanism or validated same-origin storage; allow only
  relative paths in an explicit route allow-list. Document how state expires,
  is single-use, and behaves in a second tab.
- [x] **US-P02.P2 — Choose the token flow.** Decide between a PKCE/code
  exchange and a deliberately retained implicit flow based on the current
  backend-mediated architecture. Document the security tradeoff and ensure the
  callback page and backend endpoint implement the same choice rather than
  accepting both accidentally.
- [x] **US-P02.P3 — Define failure copy and telemetry.** Map provider disabled,
  state mismatch, callback rejection, expired code, session exchange failure,
  and refresh failure to safe user-facing recovery actions and internal request
  IDs.

### Implement

- [x] **US-P02.I1 — Fix redirect validation.** Change the frontend/backend
  contract so the OAuth request uses the exact configured callback. Preserve the
  intended post-login destination without concatenating unvalidated query text
  into the callback URL.
- [x] **US-P02.I2 — Implement the chosen flow.** Add the minimal state/PKCE/code
  handling required by the decision. Bind state to the browser/session and
  reject reuse, external redirects, malformed codes, and unexpected providers.
- [x] **US-P02.I3 — Configure Supabase and Google Cloud.** Enter the Google Web
  OAuth client in Supabase Auth, set the authorized JavaScript origin to the
  intended frontend origin, set the Google redirect URI to the Supabase Auth
  callback, and update the Supabase app URL/allow-list. Keep values aligned
  with the hostname decision from US-P01.
- [x] **US-P02.I4 — Make callback recovery explicit.** Add loading, success,
  provider-error, state-error, and expired-session states. Ensure the callback
  cannot render access tokens or codes in visible copy or persistent logs.

### Test

- [x] **US-P02.T1 — Test URL safety.** Cover bare callback success, current
  query-string regression, external callback rejection, protocol/host/port
  mismatch, encoded traversal, unsafe `next`, missing `next`, and duplicate
  state use.
- [x] **US-P02.T2 — Test session establishment.** Cover the callback exchange,
  cookie creation, refresh, logout, expired token, and a user opening `/app`
  before authentication. Use fake provider responses; do not use a real user
  token in fixtures.
- [ ] **US-P02.T3 — Run a real browser flow.** With a test Google account,
  complete login through the deployed frontend and confirm the final URL,
  session endpoint, profile bootstrap, and logout. Record the provider and
  hostname used.

### Validate

- [x] **US-P02.V1 — Verify the provider.** Supabase Auth reports Google enabled,
  Google Cloud uses the exact Supabase callback, and the app allow-list contains
  only intended callback URLs.
- [ ] **US-P02.V2 — Verify the browser.** Google login completes from `/login`,
  returns to `/app`, survives a refresh, and does not expose tokens in the URL
  after callback processing.
- [x] **US-P02.V3 — Verify recovery.** Disablement/provider errors and invalid
  destinations produce a useful retry path without leaking upstream details.
- [ ] **US-P02.V4 — Close the story.** Record the flow decision, URLs (not
  secrets), test commands, browser evidence, and any provider residual in this
  file and [`PROGRESS.md`](PROGRESS.md).

## Evidence to record

- Exact callback and redirect allow-list values.
- Chosen PKCE/implicit flow and threat-model note.
- Backend and frontend regression-test results.
- Browser result using a non-production test identity.
- Confirmation that no Google secret exists in the repository or public env.

## Safety notes

Never paste client secrets, access tokens, refresh tokens, authorization codes,
or JWTs into logs, commits, screenshots, or progress notes. Do not loosen
redirect validation to make the current error disappear.

## Story notes

### 2026-09-07 — Architecture and Flow Decisions
1. **Callback Contract**:
   - Fixed application callback: `https://fin-buddy-dev.vercel.app/auth/callback` (and `http://localhost:3000/auth/callback` for local development).
   - Removed query parameter concatenation (`?next=...`) from OAuth authorization URLs. Both backend and Supabase strictly reject query strings on callback URLs.
2. **Token Flow Decision (PKCE S256)**:
   - Standardized strictly on **PKCE flow** (RFC 7636).
   - `code_challenge` generated using SHA-256 over a 43-character base64url random verifier and sent with `code_challenge_method=s256`.
   - Frontend callback receives `?code=...` and `&state=...`.
   - Implicit tokens in URL hash (`#access_token=...`) are explicitly rejected by the callback handler.
   - Code exchange occurs server-side via `POST /api/v1/auth/session` calling Supabase Auth `POST /auth/v1/token?grant_type=pkce`.
   - Next.js BFF sets HttpOnly `SameSite=Strict` cookies (`fb_access_token`, `fb_refresh_token`, `fb_expires_at`).
   - No access tokens or authorization codes leak into browser history, URL, address bar, or logs. `window.history.replaceState` clears parameters immediately upon mount.
3. **State Management & Multi-tab Safety**:
   - Cryptographic state generated via `crypto.getRandomValues`.
   - Flow record `{ state, codeVerifier, next, createdAt }` stored keyed by state in `sessionStorage` and SameSite=Lax cookie (`fb_oauth_${state}`).
   - Concurrent tabs do not collide or overwrite each other because keys are state-specific.
   - Single-use: state is immediately deleted from storage upon consumption. Replays return `null` and are rejected.
   - Lifetime: 10 minutes maximum age.
4. **Safe Destination Validation**:
   - `sanitizeAppPath` (frontend) and `validate_safe_destination` (backend) enforce same-origin relative app paths starting with `/app`.
   - Rejects external schemes/origins, protocol-relative (`//`), backslashes (`\`), URL fragments (`#`), path traversal (`/../`, `/./`, `%2e%2e`), control characters, and non-app paths, safely falling back to `/app`.
5. **Provider Status Verification**:
   - Active Supabase project ref `jklurueadteccrdycyiz` verified.
   - Live probe to `https://jklurueadteccrdycyiz.supabase.co/auth/v1/authorize?provider=google&redirect_to=https%3A%2F%2Ffin-buddy-dev.vercel.app%2Fauth%2Fcallback` returned HTTP 302 redirecting to `https://accounts.google.com/o/oauth2/v2/auth` with active Google client ID `1017490367160-eja7fk6vt7m9fioh0lj9rhfoha46b2uv.apps.googleusercontent.com` and `response_type=code`. UI-02 marked `verified`.
6. **Automated Verification Evidence**:
   - Backend pytest: 206 passed (`uv run pytest -q`).
   - Backend typing & lint: passed (`uv run ruff check .`, `uv run mypy app`).
   - Frontend tests: 16 passed (`bun test`).
   - Frontend lint, typecheck, build: passed (`bun run lint`, `bun run typecheck`, `bun run build`).
   - Agent hooks: `preflight.sh` and `post-task.sh` passed.
   - Whitespace: `git diff --check` passed cleanly.
7. **Remaining Blocker**:
   - Live interactive sign-in through a real browser using a disposable test Google account (UI-09) to confirm final profile bootstrap on production before marking story `done`.
