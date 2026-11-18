.PHONY: help install-backend install-frontend train seed backend frontend dev test lint zip clean

help:
	@echo "HealthPulse AI"
	@echo "  make install-backend   install backend + ML dependencies"
	@echo "  make install-frontend  install frontend dependencies"
	@echo "  make train             build datasets + train classical models"
	@echo "  make seed              seed the demo dataset (requires running DB)"
	@echo "  make backend           run FastAPI on :8000"
	@echo "  make frontend          run Next.js on :3000"
	@echo "  make test              run the pytest suite"

install-backend:
	cd backend && python -m pip install -r requirements.txt -r requirements-dev.txt

install-frontend:
	cd frontend && npm install

train:
	python -m ml.datasets.build_datasets
	python -m ml.training.train_classical

seed:
	cd backend && python -m scripts.seed_demo

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest ../tests -v --tb=short

lint:
	cd backend && ruff check app ../ml || true

zip:
	cd .. && zip -rq HealthPulse-AI.zip HealthPulse-AI \
	  -x "*/node_modules/*" "*/.next/*" "*__pycache__*" "*.pyc" "*/.venv/*" "*/storage/*"

clean:
	find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/.next frontend/node_modules
