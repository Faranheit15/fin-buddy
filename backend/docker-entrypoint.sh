#!/bin/sh
set -eu

# When started as root (default image entry), fix volume ownership then drop privileges.
# Named volumes are root-owned on first mount; without CAP_CHOWN (cap_drop: ALL) chown fails.
if [ "$(id -u)" = "0" ]; then
  storage="${STATEMENT_STORAGE_DIR:-/data/statements}"
  mkdir -p "$storage"
  if chown -R finbuddy:finbuddy "$storage" 2>/dev/null; then
    :
  elif chmod 1777 "$storage" 2>/dev/null; then
    echo "WARN: could not chown $storage; left world-writable (sticky bit)."
  else
    echo "ERROR: cannot make $storage writable for the app user." >&2
    echo "  Ensure the container has CAP_CHOWN (or remove read-only volume issues)." >&2
    exit 1
  fi
  # Re-exec as app user (same script, non-root path below)
  exec runuser -u finbuddy -- "$0" "$@"
fi

# Fail fast with a clear message if secrets never reached the container.
if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is not set." >&2
  echo "  Provide secrets via backend/.env and/or a root .env (see .env.example)." >&2
  echo "  Compose does not require root .env if backend/.env already has DATABASE_URL." >&2
  exit 1
fi
if [ -z "${SUPABASE_URL:-}" ]; then
  echo "ERROR: SUPABASE_URL is not set." >&2
  echo "  Provide Supabase project URL via backend/.env or environment variables." >&2
  exit 1
fi

# SUPABASE_JWT_SECRET is required only for hybrid/HS256 mode.
# In jwks_only mode, ES256 tokens are verified directly via Supabase JWKS.
if [ "${JWT_VERIFICATION_MODE:-hybrid}" != "jwks_only" ] && [ -z "${SUPABASE_JWT_SECRET:-}" ]; then
  echo "ERROR: SUPABASE_JWT_SECRET is required when JWT_VERIFICATION_MODE is hybrid or HS256." >&2
  echo "  Set SUPABASE_JWT_SECRET or use JWT_VERIFICATION_MODE=jwks_only in production." >&2
  exit 1
fi

# One-shot migrate before multi-worker uvicorn (avoids AUTO_MIGRATE races).
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Running Alembic migrations..."
  alembic upgrade head
fi

if [ "$#" -eq 0 ]; then
  set -- uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" \
    --proxy-headers --forwarded-allow-ips "*"
fi

if [ "$1" = "uvicorn" ]; then
  workers="${WEB_CONCURRENCY:-2}"
  shift
  has_workers=0
  for arg in "$@"; do
    if [ "$arg" = "--workers" ] || [ "$arg" = "-w" ]; then
      has_workers=1
      break
    fi
  done
  if [ "$has_workers" -eq 0 ]; then
    exec uvicorn --workers "$workers" "$@"
  fi
  exec uvicorn "$@"
fi

exec "$@"
