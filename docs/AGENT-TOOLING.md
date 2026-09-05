# Fin Buddy — shared agent tooling

This repository supports three agent surfaces without duplicating the
architecture rules:

| Surface | Always-on context | Skills | Hooks / agents |
| --- | --- | --- | --- |
| ChatGPT Codex | `AGENTS.md`, `.agents/rules/global.md` | `.agents/skills/` | Existing `.codex/hooks.json` for Impeccable; the shared safety scripts can be run by the production loop. |
| Claude Code | `CLAUDE.md` → `AGENTS.md` | `.claude/skills/` | `.claude/settings.json`, `.claude/agents/` |
| Google Antigravity GUI and CLI | `GEMINI.md`, `AGENTS.md`, `.agents/rules/` | `.agents/skills/` | `.agents/hooks.json`, `.agents/agents/` |

## Source-of-truth rule

`AGENTS.md` is the canonical architecture, security, testing, and cost
contract. `CLAUDE.md` and `GEMINI.md` are intentionally thin adapters. Do not
copy a second full set of rules into a vendor-specific file; that creates
silent drift and consumes context on every turn.

The project skill [`fin-buddy-production-loop`](../.agents/skills/fin-buddy-production-loop/SKILL.md)
contains the repeatable one-story loop. The Claude skill is a thin bridge to
that same file. Antigravity and Codex discover the shared skill from
`.agents/skills/`.

## User inputs

Before any deployment, authentication, migration, or plan decision, read
[`user-input-needed.md`](user-input-needed.md). Agents may update its statuses,
instructions, and evidence references, but must never write credential values
or ask the user to paste secrets into the repository or chat.

## Hook design

The hooks are deliberately deterministic and local-only:

- They check changed-file whitespace and obvious secret-bearing content.
- They do not call the network, an AI model, a cloud API, a browser, or a
  full test suite.
- They run only around tool calls that can edit files or execute commands.
- They fail closed for a detected secret or malformed diff, but they do not
  block ordinary test/build commands merely because those commands are slow.

The implementation is shared in `tools/agent-hooks/`. Vendor manifests use the
native schemas because Claude and Antigravity use different hook event names,
timeouts, and JSON output contracts. The hooks are not an uptime mechanism and
do not send telemetry anywhere.

To test the scripts without an agent:

```bash
./tools/agent-hooks/preflight.sh --manual
./tools/agent-hooks/post-task.sh --manual
```

To inspect the integrations in the native clients:

- Claude Code: `/memory`, `/skills`, `/hooks`, `/agents`.
- Antigravity GUI/CLI: `/skills`, `/hooks`, `/agents`.
- Codex: confirm the project skill is listed and run the loop's preflight
  commands before committing.

## Antigravity workflow decision

Do not add a new `.agents/workflows/` file. Antigravity documents workflows as
deprecated in favor of Agent Skills, with retirement scheduled for November 1,
2026. New repeatable behavior belongs in `.agents/skills/`.

## Zero-cost guardrail

The target is `$0 billed cost` for personal, non-commercial, low-volume use
while provider free-tier terms and quotas permit it. No agent may upgrade a
plan, attach billing, create a paid integration, call a paid AI API, or add a
paid monitoring/cache/queue/email service without an explicit new user request.
Free tiers can still pause, throttle, or change terms; the plan must never
describe the keepalive as a guarantee of uptime.

## Official references

- [Antigravity rules](https://antigravity.google/docs/rules-workflows)
- [Antigravity skills](https://antigravity.google/docs/skills)
- [Antigravity hooks](https://antigravity.google/docs/hooks)
- [Antigravity workflows to skills](https://antigravity.google/docs/migration/workflows-to-skills)
- [Claude project directory](https://code.claude.com/docs/en/claude-directory)
- [Claude hooks](https://code.claude.com/docs/en/hooks)
- [Claude skills](https://code.claude.com/docs/en/slash-commands)
- [Supabase Free project pausing](https://supabase.com/docs/guides/platform/free-project-pausing)
- [Vercel Hobby plan](https://vercel.com/docs/plans/hobby)
- [Vercel Cron usage and pricing](https://vercel.com/docs/cron-jobs/usage-and-pricing)
- [FastAPI Cloud pricing](https://fastapicloud.com/pricing/)
