#!/usr/bin/env bash
# HealthPulse AI — verify the full stack end-to-end (tests + smoke + build checks)
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Backend test suite"
( cd backend && python -m pytest ../tests -q )

echo "==> API smoke test (43 checks)"
( cd backend && python -m scripts.smoke_test )

echo "==> ML evaluation refresh"
python -m ml.evaluation.evaluate

echo "==> Frontend typecheck + production build"
if [ -d frontend/node_modules ]; then
  ( cd frontend && npx tsc --noEmit && npx next build )
else
  echo "   frontend/node_modules missing — run scripts/setup.sh first (skipped)"
fi

echo
echo "All verifications completed."
