# HealthPulse AI

**An Integrated Healthcare & Civic Intelligence Platform**

HealthPulse AI connects environmental/civic complaints with voluntary symptom reports,
analyzes both with on-device NLP, and surfaces statistically-linked clusters as
**evidence-backed investigation alerts** for public-health officials — with a dedicated
dashboard for every stakeholder role.

> ⚠️ **Responsible-AI notice (enforced across the product):** HealthPulse never claims
> that correlation proves causation and never diagnoses disease. Association scores are
> statistical co-occurrence indicators with full evidence breakdowns. Every alert, report
> summary and dashboard ships with this disclaimer. It is not a medical device.

---

## Table of contents

1. [What it does](#what-it-does)
2. [Verified build & test status](#verified-build--test-status)
3. [Architecture](#architecture)
4. [Quick start (Docker)](#quick-start-docker)
5. [Quick start (manual, without Docker)](#quick-start-manual-without-docker)
6. [Demo accounts](#demo-accounts)
7. [Project structure](#project-structure)
8. [The NLP/ML stack](#the-nlpml-stack)
9. [Cross-domain intelligence engine](#cross-domain-intelligence-engine)
10. [API overview](#api-overview)
11. [Testing](#testing)
12. [Documentation map](#documentation-map)
13. [Limitations & honest caveats](#limitations--honest-caveats)
14. [License](#license)

---

## What it does

| Domain | Capabilities |
| --- | --- |
| **Healthcare intelligence** | Natural-language symptom reporting · medical PDF upload & text extraction (PyMuPDF) · symptom/medication/body-part entity recognition · urgency triage · extractive (non-diagnostic) summarization |
| **Civic intelligence** | Complaint submission in English or romanized Hindi · classification across 10 categories · location extraction + geocoding · duplicate detection on re-reporting · complaint lifecycle management |
| **Cross-domain intelligence** | Semantic similarity (embeddings) · spatial proximity (haversine / PostGIS) · temporal windows · environmental→symptom theme priors · explainable association scores · volume anomaly detection (z-score + EWMA + Poisson-CUSUM) · investigation alerts with per-pair evidence |
| **Administrative intelligence** | 6 role-based dashboards · district heatmap (Leaflet) · trend/category/urgency charts (Recharts) · complaint workflow (state machine) · alert → investigation pipeline · audit log viewer · CSV exports (de-identified) |

**Roles:** Citizen, Patient, Clinician, Municipal Administrator, Public Health
Administrator, Super Administrator — with strict RBAC on every endpoint and
privacy boundaries (civic staff never see patient identities; clinicians never see
patient IDs; patients see only their own data).

## Verified build & test status

Everything below was **actually executed** in the build sandbox (Linux, Python 3.12,
Node 24):

| Check | Command | Result |
| --- | --- | --- |
| Synthetic dataset build | `python -m ml.datasets.build_datasets` | 1,494 train / 315 eval complaints; 420 NER-annotated reports; 1,350 sentence pairs |
| Classical model training | `python -m ml.training.train_classical` | Trained in 0.4 s — **accuracy 1.0000, macro-F1 1.0000** on the synthetic eval split (see ML guide: template data makes this optimistic) |
| Offline evaluation | `python -m ml.evaluation.evaluate` | `latest.json` written to `ml/evaluation/reports/` |
| Backend test suite | `python -m pytest ../tests` (from `backend/`) | **91 passed** |
| End-to-end API smoke test | `python -m scripts.smoke_test` (from `backend/`) | **43 passed, 0 failed** |
| Alembic migration roundtrip | `alembic upgrade head` → `downgrade base` → `upgrade head` | clean |
| Demo data seeding | `python -m scripts.seed_demo` | 6 accounts, 19 complaints, 10 reports, 3 alerts, 1 investigation |
| Live server check | `uvicorn app.main:app` + `curl` | health, analytics, login, `/docs` all 200 |
| Frontend typecheck | `npx tsc --noEmit` | clean |
| Frontend production build | `npx next build` | ✓ 11 routes compiled (Next.js 14.2.35) |

## Architecture

```
┌─────────────────────────── Browser ────────────────────────────┐
│  Next.js 14 (App Router, TypeScript, Tailwind, shadcn-style UI)│
│  Landing · Auth · 6 role dashboards · Recharts · Leaflet map   │
└──────────────────────────────┬─────────────────────────────────┘
                               │ REST (JWT bearer)
┌──────────────────────────────▼─────────────────────────────────┐
│  FastAPI backend (backend/app)                                 │
│  auth/RBAC · complaints · reports · documents · alerts         │
│  investigations · intelligence · analytics · audit · admin     │
│  SQLAlchemy 2 models · Pydantic v2 schemas · Alembic           │
└───────────────┬───────────────────────────┬────────────────────┘
                │ imports (in-process)      │ optional
┌───────────────▼──────────────┐   ┌────────▼─────────────────┐
│  ml/ package                  │   │ PostgreSQL 16 + PostGIS  │
│  classifier · NER · embeddings│   │ Redis (optional cache)   │
│  dedupe · anomaly · engine    │   └──────────────────────────┘
│  sklearn TF-IDF+LogReg        │
│  (transformers optional)      │
└───────────────────────────────┘
```

Key design decisions:

- The ML package runs **in-process** (no model server to operate) and **offline-capable**:
  TF-IDF+LogReg classifier, lexicon NER, deterministic hashing embedder. Transformer
  fine-tuning pipelines (MuRIL / DeBERTa / BioClinicalBERT / Sentence-Transformers) are
  fully implemented in `ml/training/` and load transparently if checkpoints exist — but
  nothing depends on paid LLM APIs.
- `database/init.sql` adds PostGIS geometry columns, GIST indexes, sync triggers and a
  reporting view on top of the Alembic-managed schema; the Python engine uses haversine
  so the whole stack also runs on SQLite (tests/CI).

## Quick start (Docker)

```bash
cp .env.example .env          # adjust SECRET_KEY for anything beyond a demo
docker compose up --build
# frontend  -> http://localhost:3000
# backend   -> http://localhost:8000/docs
```

Then seed demo data (one-shot):

```bash
docker compose exec backend python -m scripts.seed_demo
```

## Quick start (manual, without Docker)

Prerequisites: Python 3.11+, Node 18.17+. SQLite works out of the box for a local run;
PostgreSQL/PostGIS/Redis are used when `DATABASE_URL`/`REDIS_URL` point at them.

```bash
# 1. backend + ML dependencies
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-dev.txt      # tests

# 2. build the datasets + classical model artifact (seconds, offline)
python -m ml.datasets.build_datasets
python -m ml.training.train_classical

# 3. migrate + seed demo data (SQLite dev DB is created automatically)
cd backend
alembic upgrade head            # or skip: dev mode auto-creates tables
python -m scripts.seed_demo

# 4. run the API
uvicorn app.main:app --reload --port 8000        # http://localhost:8000/docs

# 5. frontend (second terminal)
cd ../frontend
npm install
npm run dev                                      # http://localhost:3000
```

To run the test suite:

```bash
cd backend
python -m pytest ../tests -v
python -m scripts.smoke_test
```

## Demo accounts

Created by `python -m scripts.seed_demo` (password for all: **`HealthPulse!2026`**):

| Role | Email |
| --- | --- |
| Citizen | `citizen@healthpulse.demo` |
| Patient | `patient@healthpulse.demo` |
| Clinician | `clinician@healthpulse.demo` |
| Municipal Administrator | `municipal@healthpulse.demo` |
| Public Health Administrator | `health@healthpulse.demo` |
| Super Administrator | `super@healthpulse.demo` |

The login page also has one-click pre-fill buttons for each demo account.

## Project structure

```
HealthPulse-AI/
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── core/             # config, database, security (PBKDF2+JWT), RBAC, audit, cache
│   │   ├── models/           # SQLAlchemy 2 models + enums + state machines
│   │   ├── schemas/          # Pydantic v2 request/response schemas
│   │   ├── services/         # business logic (NLP, complaints, reports, docs, engine, analytics)
│   │   ├── api/v1/           # REST routers
│   │   └── main.py
│   ├── alembic/              # migrations (verified upgrade/downgrade)
│   ├── scripts/              # seed_demo.py · smoke_test.py
│   ├── requirements.txt
│   └── requirements-dev.txt
├── ml/                       # independent NLP/ML package
│   ├── preprocessing/        # normalization, language ID, lexicons, gazetteer
│   ├── embeddings/           # sentence-transformers + deterministic hashing fallback
│   ├── classification/       # complaint classifier (TF-IDF/LogReg or HF) + urgency scorer
│   ├── extraction/           # medical NER + location extractor
│   ├── similarity/           # duplicate detection + semantic search
│   ├── anomaly/              # temporal anomaly detection (z-score/EWMA/CUSUM)
│   ├── clustering/           # HDBSCAN (DBSCAN fallback)
│   ├── summarization/        # extractive summarizer
│   ├── crossdomain/          # THE cross-domain intelligence engine
│   ├── inference/            # unified pipeline facade
│   ├── datasets/             # synthetic dataset builder + curated demo corpus
│   ├── training/             # classical trainer + HF fine-tuning scripts
│   ├── evaluation/           # offline evaluation harness
│   └── models/               # saved checkpoints (classifier artifact committed)
├── frontend/                 # Next.js 14 app (App Router)
│   ├── app/                  # landing, login, register, dashboard/* (6 role dashboards)
│   ├── components/           # ui/ (shadcn-style), charts, map, dashboard widgets
│   └── lib/                  # api client, auth context, types
├── database/                 # init.sql (PostGIS extension schema, views, triggers)
├── tests/                    # 91 pytest cases (API + NLP unit + engine + anomaly)
├── docs/                     # ARCHITECTURE · API · ML_GUIDE · DEMO_DATA · LIMITATIONS · SECURITY_PRIVACY
├── docker/                   # backend & frontend Dockerfiles
├── docker-compose.yml        # postgres+postgis, redis, backend, frontend
├── scripts/                  # setup.sh, verify.sh (host-side helpers)
├── .env.example              # all configuration knobs documented
└── README.md · PROJECT_PROGRESS.md · LICENSE · Makefile
```

## The NLP/ML stack

All pipelines are modular and independently testable. See **[docs/ML_GUIDE.md](docs/ML_GUIDE.md)**
for the full guide, model choices and real evaluation numbers. Summary:

| Pipeline | Offline default | Optional upgrade |
| --- | --- | --- |
| Complaint classification | TF-IDF (1-2 g) + LogisticRegression, artifact committed | `google/muril-base-cased` or `microsoft/deberta-v3-base` fine-tune (`ml/training/train_complaint_classifier_hf.py`) |
| Medical NER | Curated lexicon longest-match with char spans | BioClinicalBERT token classification (`ml/training/train_medical_ner_hf.py`) |
| Embeddings | Deterministic hashing embedder (384-dim) | Sentence-Transformers + cross-domain pair fine-tune (`ml/training/train_embedding_model.py`) |
| Urgency | Explainable weighted feature scorer with evidence terms | — (deliberately rule-based & auditable) |
| Duplicates | cosine + Jaccard + category/geo/temporal blend with gates | — |
| Anomaly | z-score + EWMA + Poisson-CUSUM (2-detector agreement) | — |
| Clustering | sklearn DBSCAN (adaptive eps) | HDBSCAN |

**No paid LLM APIs anywhere.** Every analysis runs locally.

## Cross-domain intelligence engine

`ml/crossdomain/engine.py` — the heart of the platform:

1. Embed all complaints + reports in the scan window.
2. Filter candidate pairs: ≤ `MAX_ASSOCIATION_KM` (3 km) and ≤ `MAX_ASSOCIATION_DAYS` (21 d).
3. Score each pair with an auditable weighted blend:
   `association = 0.45·semantic + 0.20·spatial + 0.20·temporal + 0.15·theme`
   (theme = environmental category ↔ symptom category co-occurrence prior).
4. Pairs ≥ threshold (0.55) are grouped into clusters (connected components).
5. Temporal anomaly detection runs per district series.
6. Alerts (cross-domain clusters + anomalies) are persisted with **full per-pair evidence**:
   semantic/spatial/temporal/theme contributions, excerpts, symptom lists, detector methods.

Weights, thresholds and windows are configurable via `.env` (see `.env.example`).

## API overview

Interactive docs at `http://localhost:8000/docs` (OpenAPI). Full endpoint table in
**[docs/API.md](docs/API.md)**. Highlights:

- `POST /api/v1/auth/register|login|login/form` · `GET /auth/me`
- `POST/GET /complaints` · `PATCH /complaints/{id}/status` · `POST /complaints/{id}/mark-duplicate`
- `GET /complaints/{id}/similar` · `GET /complaints/geo`
- `POST/GET /reports` · `POST /reports/{id}/summarize` · `POST /reports/from-document`
- `POST /documents/upload` · `GET /documents/{id}/text` · `DELETE /documents/{id}`
- `POST /intelligence/scan` · `GET /intelligence/related/{complaint|report}/{id}` · `POST /intelligence/preview[-report]`
- `GET/PATCH /alerts` · `GET/PATCH /investigations`
- `GET /analytics/public|overview|trends|districts|heatmap|export`
- `GET /audit-logs` · `GET /system/health` (super admin)

## Testing

- **91 pytest cases** in `tests/`: auth/RBAC, complaint lifecycle & state machine,
  duplicate detection, medical report privacy (identity stripping verified), document
  upload security (extension/empty/path-traversal), NLP pipelines (classifier, NER,
  urgency, language, locations, summarizer), duplicate + semantic search, temporal
  anomaly detection, cross-domain engine (positive + negative scenarios, temporal windows,
  disclaimer presence), analytics roles, audit trail, user management guards
  (last-super-admin protection), system health.
- **43-check API smoke test** (`backend/scripts/smoke_test.py`) walking the real user
  journeys end-to-end.

## Documentation map

| Doc | Contents |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | system design, data flow, schema, RBAC matrix, design decisions |
| [docs/API.md](docs/API.md) | full endpoint reference with roles & payloads |
| [docs/ML_GUIDE.md](docs/ML_GUIDE.md) | every pipeline, model choices, real metrics, fine-tuning instructions |
| [docs/DEMO_DATA.md](docs/DEMO_DATA.md) | what the synthetic demo data contains and how it was generated |
| [docs/LIMITATIONS.md](docs/LIMITATIONS.md) | honest list of what works here vs what needs external resources |
| [docs/SECURITY_PRIVACY.md](docs/SECURITY_PRIVACY.md) | auth, RBAC, privacy boundaries, document storage, audit design |
| [PROJECT_PROGRESS.md](PROJECT_PROGRESS.md) | build log: what was implemented and verified, phase by phase |

## Limitations & honest caveats

- **Demo city is fictional** ("Riverton"): gazetteer, coordinates, pincodes and every
  seeded complaint/report are synthetic. Do not present them as real-world evidence.
- **Transformer training was not executed** in the build sandbox (no GPU / heavy optional
  deps); the scripts are complete and documented. Classical model training WAS executed.
- Real metrics (accuracy 1.0 / macro-F1 1.0) are computed on template-generated synthetic
  data — they demonstrate pipeline correctness, not real-world performance.
- OCR for scanned PDFs is stubbed (`NO_TEXT` status + guidance); PyMuPDF text-layer
  extraction is fully working.
- PostGIS/PostgreSQL path is exercised through `docker-compose` + `database/init.sql`
  (not run in this sandbox); SQLite is the verified local path and test path.

## License

MIT — see [LICENSE](LICENSE).
