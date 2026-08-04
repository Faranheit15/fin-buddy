#!/usr/bin/env bash
# Post-deploy / local smoke helper for Fin Buddy personal production.
# Usage:
#   export API_URL=https://your-api.example.com
#   export APP_URL=https://your-app.vercel.app
#   ./scripts/smoke-prod.sh

set -euo pipefail

API_URL="${API_URL:-http://127.0.0.1:8000}"
APP_URL="${APP_URL:-http://127.0.0.1:3000}"

echo "== Health =="
curl -fsS "${API_URL%/}/api/v1/health" | tee /tmp/finbuddy-health.json
echo

echo "== Demo login should be disabled in production =="
demo="$(curl -fsS "${API_URL%/}/api/v1/auth/demo-available" || true)"
echo "$demo"
if echo "$demo" | grep -qi 'demo_available'; then
  echo "WARNING: demo login reports available — ensure ENVIRONMENT=production and DEMO_AUTH_ENABLED is not true"
else
  echo "OK: demo not available (or endpoint returned disabled)"
fi
echo

echo "== Frontend reachable =="
code="$(curl -s -o /dev/null -w '%{http_code}' "${APP_URL%/}/" || echo fail)"
echo "GET ${APP_URL%/}/ → HTTP ${code}"
echo

cat <<'EOF'
Manual smoke (complete in the browser):
  1. Sign in (email and/or Google) — demo must be off
  2. Add a card → dashboard KPIs populate
  3. Add contact + purchase → contact outstanding updates
  4. Upload FinBuddy sample .txt → review → import
  5. Redeploy/restart API → statement file still opens (Supabase Storage)
  6. Notifications + Settings thresholds
EOF
