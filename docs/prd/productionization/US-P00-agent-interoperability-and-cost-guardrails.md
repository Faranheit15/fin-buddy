# US-P00 — Shared agent workflow and zero-cost guardrails

| Field | Value |
| --- | --- |
| **Status** | `done` |
| **Sequence** | 0 |
| **Depends on** | None |
| **One-loop objective** | Give Codex, Claude Code, and Google Antigravity GUI/CLI one safe project workflow, one user-input handoff, and deterministic cost/security guardrails. |
| **Primary boundaries** | `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/`, `.claude/`, `tools/agent-hooks/`, `docs/` |

## User story

**As** the Fin Buddy owner
**I want** every supported coding agent to follow the same architecture, user-input, and free-tier rules
**So that** switching agents does not cause configuration drift, secret leakage, paid usage, or skipped verification.

## Why this matters

The repository already had Codex/Claude-compatible architecture guidance and an
Impeccable UI hook, but it did not have a Gemini/Antigravity context shim, a
shared production loop skill, a tracked human-input handoff, or a deterministic
cross-agent safety hook. Vendor hooks also use different schemas, so copying one
manifest into another tool would silently fail.

## Scope and non-goals

In scope: thin instruction adapters, workspace rules, shared Agent Skills,
read-only reviewer definitions, deterministic local hooks, human-input tracking,
and free-tier/paid-AI guardrails.

Out of scope: installing global agent configuration, adding a paid plugin,
changing application behavior, deploying services, or authenticating cloud
accounts.

## Acceptance criteria

1. `AGENTS.md` remains the architecture source of truth; `CLAUDE.md` and
   `GEMINI.md` are thin adapters that do not contradict it.
2. Codex and Antigravity discover the shared production loop from
   `.agents/skills/`, while Claude Code has a project skill bridge under
   `.claude/skills/`.
3. Antigravity GUI/CLI has workspace rules, a native hook manifest, and a
   read-only reviewer agent under `.agents/`.
4. Claude Code has project-shared hooks and a read-only reviewer under
   `.claude/`, while the existing local Impeccable hook remains intact.
5. Hooks are deterministic, local-only, fast, secret-aware, and do not invoke
   models, network services, full builds, or paid resources.
6. `docs/user-input-needed.md` gives exact Google OAuth, Supabase, FastAPI
   Cloud, and Vercel destinations without storing credential values.
7. The active plan explicitly targets `$0 billed cost` conditionally on free
   tiers and terms, and calls the Supabase probe best-effort rather than a
   no-sleep guarantee.

## Tasks

### Gather

- [x] **US-P00.G1 — Audit existing adapters.** Inspect `AGENTS.md`, nested
  contexts, `.agents/`, `.claude/`, `.codex/`, and existing UI hooks. Preserve
  the Impeccable behavior and thin Claude shims.
- [x] **US-P00.G2 — Verify native conventions.** Confirm current official
  paths for Claude project skills/hooks and Antigravity rules/skills/hooks.
  Record the source links in `docs/AGENT-TOOLING.md`.
- [x] **US-P00.G3 — Verify free-tier assumptions.** Record Supabase pausing,
  Vercel Hobby/Cron limits, and FastAPI Cloud Hobby caveats without promising
  uptime or unconditional free operation.

### Plan

- [x] **US-P00.P1 — Choose the shared layout.** Use `AGENTS.md` as canonical,
  `.agents/skills/` as the cross-agent skill location, `.claude/skills/` as a
  Claude bridge, and vendor-specific hook manifests around shared scripts.
- [x] **US-P00.P2 — Define secret handling.** Keep OAuth/provider secrets in
  provider dashboards or secret stores; allow only statuses and identifiers in
  the tracked user-input file.
- [x] **US-P00.P3 — Define performance/cost behavior.** Keep hooks under a
  short timeout, avoid model/network work, avoid background keepalive loops,
  and prohibit paid upgrades or AI APIs by default.

### Implement

- [x] **US-P00.I1 — Add context adapters and rules.** Add `GEMINI.md`, the
  documentation context, and links from the global rules without duplicating
  the full architecture manual.
- [x] **US-P00.I2 — Add shared skills and reviewer agents.** Add the one-story
  loop skill and native reviewer definitions for Antigravity and Claude.
- [x] **US-P00.I3 — Add native hooks.** Add `.agents/hooks.json`,
  `.claude/settings.json`, and shared `tools/agent-hooks/` scripts. Keep the
  existing `.codex/hooks.json` Impeccable integration unchanged.
- [x] **US-P00.I4 — Add the user-input handoff.** Create
  `docs/user-input-needed.md` with exact Google OAuth destinations, safe secret
  handling, deployment input locations, and an update log.
- [x] **US-P00.I5 — Add cost guardrails.** Make free-tier caveats, quota stop
  rules, no-paid-AI rules, and the best-effort keepalive language visible in
  the active plan and loop skill.

### Test

- [x] **US-P00.T1 — Validate file contracts.** Parse both JSON hook manifests,
  check skill frontmatter, check executable bits, and verify all new links.
- [x] **US-P00.T2 — Exercise hooks locally.** Run manual preflight/post-task
  checks with clean and intentionally invalid inputs without reading secrets.
- [x] **US-P00.T3 — Check repository safety.** Run `git diff --check`, ensure
  no `.env` or credential value is added, and avoid frontend/backend code
  changes.

### Validate

- [x] **US-P00.V1 — Validate the three surfaces.** Confirm the files map to
  the documented Codex, Claude Code, and Antigravity GUI/CLI conventions.
- [x] **US-P00.V2 — Validate the human handoff.** Confirm the Google OAuth
  instructions distinguish the Supabase callback from the app callback and do
  not require a frontend secret.
- [x] **US-P00.V3 — Close the story.** Record evidence in this file and move
  the loop tracker to the first application-facing story, US-P01.

## Evidence

- Official path research and URLs: [`docs/AGENT-TOOLING.md`](../../AGENT-TOOLING.md).
- Human inputs and current Google OAuth blocker: [`docs/user-input-needed.md`](../../user-input-needed.md).
- Native hook manifests: [`.agents/hooks.json`](../../../.agents/hooks.json) and
  [`.claude/settings.json`](../../../.claude/settings.json).
- Shared hook implementation: [`tools/agent-hooks/`](../../../tools/agent-hooks/).
- No application code, cloud resource, deployment, secret, or paid service was
  changed by this story.

## Story notes

**2026-09-05 — done.** Parallel research tracks audited the repository,
official agent conventions, free-tier limits, and required owner inputs. The
main worktree then integrated the reviewed documentation, skills, native hook
adapters, and safety scripts. Native CLI/GUI discovery still requires the
owner to open each client locally; the exact `/memory`, `/skills`, `/hooks`,
and `/agents` checks are documented.
