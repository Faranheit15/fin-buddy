#!/usr/bin/env bash
# Fix FastAPI Cloud deps + push. Run in WSL:
#   bash scripts/fix-fastapi-cloud.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Backend: refresh lock with fastapi[standard] =="
cd backend
uv lock
uv sync --group dev
uv run python -c "import fastapi_cli; print('fastapi-cli OK')"
cd ..

echo "== Commit & push =="
git add \
  backend/pyproject.toml \
  backend/uv.lock \
  backend/.python-version \
  frontend/next.config.ts \
  frontend/Dockerfile \
  frontend/vercel.json \
  docs/DEPLOY.md

git status
git commit -m "$(cat <<'EOF'
Fix FastAPI Cloud and Vercel deploy packaging

Install fastapi-cli[standard], pin Python 3.12, and disable Next standalone on Vercel.
EOF
)" || echo "(nothing new to commit or commit failed)"

git push origin develop
git status -sb
git log -1 --oneline
echo "Done. Redeploy backend on FastAPI Cloud after push."
