#!/usr/bin/env bash
set -euo pipefail

mode="${1:---manual}"
root="${CLAUDE_PROJECT_DIR:-${PWD}}"

if git_root="$(git -C "$root" rev-parse --show-toplevel 2>/dev/null)"; then
  root="$git_root"
elif git_root="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel 2>/dev/null)"; then
  root="$git_root"
fi

if [[ ! -t 0 ]]; then
  cat >/dev/null
fi

failure=""
if command -v git >/dev/null 2>&1 && ! git -C "$root" diff --check >/dev/null; then
  failure="The working-tree diff contains whitespace errors after the agent action."
fi

secret_pattern='-----BEGIN [A-Z ]*PRIVATE KEY-----|GOCSPX-[A-Za-z0-9_-]{20,}|SUPABASE_SERVICE_ROLE_KEY[[:space:]]*[:=][[:space:]]*[A-Za-z0-9._-]{16,}|GOOGLE_CLIENT_SECRET[[:space:]]*[:=][[:space:]]*[A-Za-z0-9._-]{16,}|CRON_SECRET[[:space:]]*[:=][[:space:]]*[A-Za-z0-9._-]{24,}|postgres(ql)?://[^[:space:]]+:[^[:space:]]+@'
if [[ -z "$failure" ]] && command -v git >/dev/null 2>&1; then
  diff_text="$(git -C "$root" diff --no-ext-diff; git -C "$root" diff --cached --no-ext-diff)"
  while IFS= read -r untracked_path; do
    if [[ -f "$root/$untracked_path" ]]; then
      diff_text+=$'\n'"$(sed -n '1,20000p' "$root/$untracked_path")"
    fi
  done < <(git -C "$root" ls-files --others --exclude-standard)
  if grep -Eiq -- "$secret_pattern" <<<"$diff_text"; then
    failure="The working-tree diff appears to contain a secret. Remove the value and use provider secret storage."
  fi
fi

case "$mode" in
  --claude)
    if [[ -n "$failure" ]]; then
      printf '{"decision":"block","reason":"%s"}\n' "$failure"
    else
      printf '{}\n'
    fi
    ;;
  --antigravity|--gemini)
    if [[ -n "$failure" ]]; then
      printf '%s\n' "$failure" >&2
    fi
    printf '{}\n'
    ;;
  --manual)
    if [[ -n "$failure" ]]; then
      printf '%s\n' "$failure" >&2
      exit 1
    fi
    printf '%s\n' "Fin Buddy post-task validation passed." >&2
    ;;
  *)
    if [[ -n "$failure" ]]; then
      printf '%s\n' "$failure" >&2
      exit 1
    fi
    ;;
esac
