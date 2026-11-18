# HealthPulse AI — Project Progress Log

This file records what was **actually built and verified** during the build, phase by
phase, including the real commands executed and their outcomes. Nothing here is
aspirational: unchecked items are listed honestly in [docs/LIMITATIONS.md](docs/LIMITATIONS.md).

Build environment: Linux sandbox, Python 3.12.16, Node v24.22.3 / npm 11.19.1,
2 vCPU / 4 GB RAM, network available (PyPI + npm). No GPU available.

---

## Phase 1 — Environment inspection ✅

- Verified runtimes: Python 3.12.16 (venv), Node 24.22.3, npm 11.19.1, git 2.47.3, zip/unzip.
- Verified network access to PyPI and npm registry.
- Pre-installed: fastapi 0.128, pydantic 2.12.5, PyJWT, pytest 9.0.2, scikit-learn 1.5.2,
  numpy, pandas, PyMuPDF 1.26.7, httpx, uvicorn, redis client.
- Installed additionally: sqlalchemy 2.1.9, alembic 1.20.1, email-validator, rapidfuzz.
- Not installed (deliberately): torch/transformers/sentence-transformers (~2.5 GB, no GPU) —
  handled via guarded optional extras with working offline fallbacks.

## Phase 2 — Project scaffold ✅

- Created the full directory tree (backend, ml with 14 subpackages, frontend, database,
  tests, docs, docker, scripts).
- Root configs: `.gitignore` (excludes caches/node_modules/secrets/db files),
  `.env.example` (documented knobs), MIT `LICENSE`, `Makefile`, `docker-compose.yml`
  (postgres+PostGIS 16, redis 7, backend, frontend), `docker/backend.Dockerfile`,
  `docker/frontend.Dockerfile` (standalone output).

## Phase 3 — ML/NLP package ✅ (trained + smoke-tested)

- `ml/preprocessing`: normalization, language detection (6 Indic scripts + romanized-Hindi
  mapping), symptom/medication/body-part/severity lexicons, complaint keyword lexicon,
  fictional demo-city gazetteer (8 districts).
- `ml/embeddings`: Sentence-Transformers backend + deterministic hashing embedder (384-dim,
  md5-bucketed, tf-weighted, L2-normalized).
- `ml/classification`: complaint classifier facade (HF checkpoint → committed TF-IDF+LogReg
  joblib → keyword-rule fallback) and explainable urgency scorer with evidence reasons.
- `ml/extraction`: lexicon medical NER with char spans (SYMPTOM/MEDICATION/BODY_PART/
  DURATION/VITAL/AGE) + location extractor (gazetteer, phrase patterns, pincodes, coords).
- `ml/similarity`: duplicate detector (0.60 semantic + 0.20 Jaccard + 0.10 category +
  0.10 geo blend, cross-category cosine gate) and semantic search.
- `ml/anomaly`: z-score + EWMA + Poisson-CUSUM with 2-detector agreement rule.
- `ml/clustering`: HDBSCAN with sklearn DBSCAN adaptive-eps fallback.
- `ml/summarization`: extractive summarizer + structured medical digest (explicit
  "not a diagnosis" wording).
- `ml/crossdomain`: the intelligence engine (pair scoring with per-signal evidence,
  connected-component clustering, temporal anomaly series, disclaimers).
- `ml/inference`: `HealthPulseNLP` facade + process-wide singleton.
- **Executed**: `python -m ml.datasets.build_datasets` → 1,494 train / 315 eval complaints,
  420 NER-annotated symptom reports, 1,350 sentence pairs (seed 42, deterministic).
- **Executed**: `python -m ml.training.train_classical` → trained in 0.4 s; eval
  accuracy 1.0000 / macro-F1 1.0000 (synthetic data — optimistic by construction);
  artifact committed to `ml/models/complaint_classifier/tfidf_lr.joblib` + `metrics.json`.
- **Executed**: `python -m ml.evaluation.evaluate` → `ml/evaluation/reports/latest.json`.
- **Executed**: full pipeline smoke run — complaint analysis (water_contamination 0.98,
  urgency MEDIUM with reasons, location Millbrook 0.85), symptom analysis (symptoms +
  categories + summary), duplicate detection (near-duplicate 114 flagged at 0.80 ≥ 0.75;
  paraphrase 115 correctly below), cross-domain scan (25 candidate pairs, 3 cluster alerts
  with 4–16 supporting pairs each).

## Phase 4 — Backend (FastAPI) ✅

- Core: settings (pydantic-settings), SQLAlchemy 2.1 engine/session, PBKDF2-SHA256
  password hashing (200k iterations), JWT (PyJWT HS256), RBAC dependency factory with
  SUPER_ADMIN always-allowed rule, audit logger, optional Redis cache with in-process
  fallback.
- Models: users, complaints (state machine + embedding + duplicate link), medical_reports
  (entities, symptoms, urgency, summary, embedding), documents (content-addressed store
  metadata), alerts (evidence JSON), investigations, audit_logs.
- Schemas: pydantic v2 with validation (roles restricted at self-registration, lengths,
  geo ranges).
- Services: complaint service (analyze → dedupe → persist), report service, document
  service (PyMuPDF extraction, sanitized content-addressed storage, 0o640 perms),
  intelligence service (scan orchestration + alert de-duplication + related-item views),
  analytics service (role-shaped aggregates with caching).
- API v1: auth (JSON + OAuth2 form login), users admin (last-super-admin guard),
  complaints (lifecycle transitions validated, geo, similar), reports (privacy-stripped
  outputs), documents, alerts + investigations (auto-open investigation on CONFIRMED),
  intelligence (scan/preview/related/status), analytics (public/overview/trends/districts/
  heatmap/CSV export), admin (audit logs, system health).
- Fixed during review: circular FK documents↔reports (denormalized `report_id`), missing
  imports, back_populates mismatch.

## Phase 5 — Database ✅

- Alembic migration autogenerated from models and verified: `upgrade head` → `downgrade
  base` → `upgrade head` clean on SQLite.
- `database/init.sql`: PostGIS extension, geometry columns + GIST indexes, lat/lng→geom
  sync triggers, `v_district_summary` view; documented PostGIS `ST_DWithin` query path.
- `backend/pytest.ini` configured with pythonpath for root-level `tests/`.

## Phase 6 — Demo data ✅

- `ml/datasets/demo_corpus.py`: 19 hand-tuned synthetic complaints (two cross-domain
  clusters: Millbrook water/drainage/mosquito + Riverside sewage; one Southbay mosquito
  cluster; infrastructure filler; two explicit duplicate groups), 10 synthetic symptom
  reports aligned to those clusters, `DEMO_NOW` fixed for reproducibility.
- `backend/scripts/seed_demo.py`: creates 6 role accounts, NLP-analyzes and persists the
  corpus, links duplicate ground truth, runs a real intelligence scan (3 alerts),
  demonstrates the workflow (alert REVIEWING + investigation + acknowledged complaint).
  **Executed** successfully: 6 users, 19 complaints, 10 reports, 3 alerts, 1 investigation.

## Phase 7 — Tests ✅ (91 passing)

- `tests/conftest.py`: isolated temp SQLite DB + seeded role users + JWT token fixtures.
- 10 test modules: auth/RBAC (13), complaints API (12), reports API + privacy (5),
  documents + upload security (9), NLP pipelines (18), duplicates + search (6),
  anomaly (5), cross-domain engine (5), intelligence/alerts/investigations API (5),
  analytics (6), audit/users/system (7).
- `backend/scripts/smoke_test.py`: 43-check end-to-end API walk (idempotent, re-runnable).
- **Final results: pytest 91 passed / 0 failed; smoke test 43 passed / 0 failed.**
- Bugs caught by tests and fixed: theme-match denominator, urgency threshold tuning
  (HIGH 0.50→0.45 + dehydration/children signals), patient identity stripping for
  clinicians, ReportOut.document_id, complaints router import hygiene, audit-log import.

## Phase 8 — Frontend ✅ (built successfully)

- Next.js 14.2.35 (patched version after npm security advisory on 14.2.15), TypeScript
  strict, Tailwind 3.4 + shadcn-style component library (hand-rolled, Radix dialog/tabs),
  custom toast system, light/dark theme provider (localStorage + class strategy),
  system font stack (no network-dependent next/font).
- Landing page: hero, live public stats (server-fetched, graceful fallback), 4 feature
  cards, how-it-works, roles grid, responsible-AI notice, CTA, footer.
- Auth: login (demo pre-fill buttons), registration (role limited to CITIZEN/PATIENT).
- Dashboard shell: role-filtered sidebar, auth guard with redirect, mobile drawer,
  theme toggle, sign-out.
- 6 dashboards: citizen (complaint form with **live NLP preview** via
  `/intelligence/preview`, duplicate warnings, history with filters/pagination), patient
  (symptom report with live extraction preview, document upload → create report, report
  cards), clinician (report review with entities/triage reasons, summarize button,
  alias-only identity), municipal (KPIs, trend chart, Leaflet map, status breakdown,
  complaint table with filters, status-transition dialog), health admin (overview charts,
  heatmap, top symptoms, intelligence scan button, alerts with evidence panel +
  confirm→investigation workflow, investigations tracker, CSV export), super admin
  (users with role change/activation guards, audit log viewer with filters, system
  health including NLP backends).
- **Executed**: `npm install` (194 packages), `npx tsc --noEmit` clean,
  `npx next build` ✓ compiled 11 routes, static prerender OK.

## Phase 9 — Integration verification ✅

- `python -m uvicorn app.main:app` launched; verified via curl:
  `/api/v1/health` 200, `/api/v1/analytics/public` returning seeded aggregates,
  seeded super-admin login 200, `/docs` (Swagger) 200. Server then stopped.
- Re-seeded SQLite DB reflects combined demo + smoke-test data (35 complaints).

## Phase 10 — Packaging ✅

- Cleaned caches, produced `HealthPulse-AI.zip` (excluding node_modules, .next,
  __pycache__, storage, DB files); archive integrity verified with `unzip -t`,
  contents verified (frontend/backend/ml/docs/database/tests all present),
  spot-extracted and re-verified.
