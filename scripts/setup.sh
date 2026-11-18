#!/usr/bin/env bash
# HealthPulse AI — one-time host setup (manual/dev path, no Docker)
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Installing backend dependencies"
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-dev.txt

echo "==> Building synthetic datasets + classical model (offline, ~seconds)"
python -m ml.datasets.build_datasets
python -m ml.training.train_classical

echo "==> Running migrations + seeding demo data (SQLite dev DB)"
( cd backend && alembic upgrade head && python -m scripts.seed_demo )

echo "==> Installing frontend dependencies"
( cd frontend && npm install )

cat <<'EOF'

Setup complete. Start the stack in two terminals:

  Terminal 1:  cd backend && uvicorn app.main:app --reload --port 8000
  Terminal 2:  cd frontend && npm run dev

Then open http://localhost:3000 (demo accounts in README.md).
EOF
