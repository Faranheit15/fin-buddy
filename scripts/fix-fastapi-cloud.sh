#!/usr/bin/env bash
# Regenerate lock + push so FastAPI Cloud can build.
# Run in WSL: bash scripts/fix-fastapi-cloud.sh
set -euo pipefail
cd "$(dirname "$0")/.."

cd backend
echo "== uv lock (required: Cloud uses --locked when uv.lock exists) =="
uv lock
uv sync --group dev
uv run python -c "import fastapi_cli; from app.main import app; print('OK', app.title)"
cd ..

git add backend/pyproject.toml backend/uv.lock backend/.python-version \
  frontend/next.config.ts frontend/Dockerfile frontend/vercel.json docs/DEPLOY.md \
  scripts/fix-fastapi-cloud.sh || true

git status
git commit -m "$(cat <<'EOF'
Fix FastAPI Cloud lockfile for fastapi-cli and Python 3.12

EOF
)" || true

git push origin develop
echo "Redeploy: cd backend && fastapi deploy"
git log -1 --oneline
