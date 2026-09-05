#!/usr/bin/env bash
set -euo pipefail

# This script is intentionally local-only and dependency-light. It accepts the
# provider mode as its first argument so native Claude and Antigravity adapters
# can share the same checks while returning their own JSON contract.
mode="${1:---manual}"
root="${CLAUDE_PROJECT_DIR:-${PWD}}"

if git_root="$(git -C "$root" rev-parse --show-toplevel 2>/dev/null)"; then
  root="$git_root"
fi

hook_input=""
if [[ ! -t 0 ]]; then
  hook_input="$(cat)"
fi

fail_reason=""

if command -v git >/dev/null 2>&1 && ! git -C "$root" diff --check >/dev/null; then
  fail_reason="The working-tree diff contains whitespace errors. Fix them before the next agent action."
fi

changed_paths=""
if command -v git >/dev/null 2>&1; then
  changed_paths="$(
    git -C "$root" diff --name-only
    git -C "$root" diff --cached --name-only
  )"
fi

if [[ -z "$fail_reason" ]] && grep -Eq '(^|/)(\.env|\.env\.[^e])($|/)' <<<"$changed_paths"; then
  fail_reason="A non-example environment file is in the change set. Keep secrets in provider secret storage or gitignored local files."
fi

secret_pattern='-----BEGIN [A-Z ]*PRIVATE KEY-----|GOCSPX-[A-Za-z0-9_-]{20,}|SUPABASE_SERVICE_ROLE_KEY[[:space:]]*[:=][[:space:]]*[A-Za-z0-9._-]{16,}|GOOGLE_CLIENT_SECRET[[:space:]]*[:=][[:space:]]*[A-Za-z0-9._-]{16,}|CRON_SECRET[[:space:]]*[:=][[:space:]]*[A-Za-z0-9._-]{24,}|postgres(ql)?://[^[:space:]]+:[^[:space:]]+@'
diff_text=""
if command -v git >/dev/null 2>&1; then
  diff_text="$(git -C "$root" diff --no-ext-diff; git -C "$root" diff --cached --no-ext-diff)"
  while IFS= read -r untracked_path; do
    if [[ -f "$root/$untracked_path" ]]; then
      diff_text+=$'\n'"$(sed -n '1,20000p' "$root/$untracked_path")"
    fi
  done < <(git -C "$root" ls-files --others --exclude-standard)
fi

if [[ -z "$fail_reason" ]] && {
  grep -Eiq -- "$secret_pattern" <<<"$diff_text" || grep -Eiq -- "$secret_pattern" <<<"$hook_input";
}; then
  fail_reason="The proposed change appears to contain a secret. Remove the value and use the provider secret store."
fi

emit_block() {
  local reason="$1"
  case "$mode" in
    --antigravity)
      printf '{"decision":"deny","reason":"%s"}\n' "$reason"
      ;;
    --claude)
      printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
      ;;
    --gemini)
      printf '{"decision":"deny","reason":"%s"}\n' "$reason"
      ;;
    --manual)
      printf '%s\n' "$reason" >&2
      ;;
    *)
      printf '%s\n' "$reason" >&2
      ;;
  esac
}

if [[ -n "$fail_reason" ]]; then
  emit_block "$fail_reason"
  [[ "$mode" == "--manual" ]] && exit 1
  exit 0
fi

case "$mode" in
  --antigravity|--gemini)
    printf '{"decision":"allow"}\n'
    ;;
  --manual)
    printf '%s\n' "Fin Buddy agent preflight passed." >&2
    ;;
  *)
    # Claude continues when a PreToolUse hook exits 0 without JSON.
    ;;
esac
