# HealthPulse AI — Limitations & Honest Caveats

This project was built and verified inside an air-gapped-capable Linux sandbox
(2 vCPU, 4 GB RAM, no GPU). Everything below states exactly what works out of the box,
what needs external resources, and what was deliberately simplified.

## 1. Verified in the build sandbox ✅

- Full backend (FastAPI + SQLAlchemy + Alembic + JWT/RBAC + audit + storage) — 91/91
  pytest cases green, 43/43 smoke checks green, live uvicorn boot verified with curl.
- Classical ML stack: dataset generation, TF-IDF+LogReg training (real metrics written
  to `ml/models/complaint_classifier/metrics.json`), offline evaluation, duplicate
  detection, anomaly detection, cross-domain engine — all executed.
- Frontend: `npm install`, `tsc --noEmit` clean, `next build` compiled all 11 routes.
- SQLite path (dev + tests) fully working; Alembic migration roundtrip verified.
- PDF text extraction with PyMuPDF (upload → extract → create report) — tested with a
  real generated PDF.

## 2. Not executable here — complete but unrun code ⚠️

| Component | Status | What's needed |
| --- | --- | --- |
| Transformer fine-tuning (MuRIL/DeBERTa/BioClinicalBERT/ST) | Scripts complete (`ml/training/`), NOT executed | `pip install -r ml/requirements-ml.txt` (~2.5 GB), GPU recommended, network for backbone downloads |
| PostgreSQL + PostGIS path | Schema SQL written, compose file provided; NOT run in sandbox (no Docker daemon) | `docker compose up --build`; Alembic migration runs on first backend boot |
| Redis cache | Client code written with graceful fallback; not exercised against a live Redis | `REDIS_URL` set (compose provides it) |
| Scanned-PDF OCR | Stubbed: extraction returns `NO_TEXT` status | add `pytesseract` + `tesseract-ocr` in `document_service._extract_pdf` (integration point marked) |

## 3. Deliberate design simplifications

- **Classic metric optimism:** the 1.0000 accuracy/macro-F1 comes from template-generated
  synthetic data (train/eval share templates). Real-world numbers require real labelled
  data; the training/evaluation scripts accept any JSONL.
- **Hashing embedder** is deterministic but not semantically pretrained; cross-domain
  recall relies more on the spatial/temporal/theme signals until the Sentence-Transformers
  fine-tune is run. This is documented, configurable, and the upgrade path is one command.
- **Bearer JWT in localStorage** (XSS-traceable) was chosen over httpOnly cookies for a
  demo-friendly single-origin setup; `docs/SECURITY_PRIVACY.md` lists the production
  hardening steps (cookie transport, CSRF, refresh tokens, rate limiting).
- **No background job queue:** intelligence scans run synchronously (seconds at demo
  scale). For large cities, move scans to a worker (Celery/RQ) — the engine is stateless
  and DB-agnostic, so the refactor is mechanical.
- **PostGIS is optional:** the portable engine uses haversine in Python; init.sql adds
  geometry/triggers/views for production spatial queries.

## 4. Compliance boundaries

- Not a medical device; no diagnosis, triage-for-treatment or causal inference is
  performed or claimed (disclaimer rendered throughout UI and API).
- Demo accounts ship with a public password — rotate/disable before any real deployment.
- The fictional city ("Riverton") must be replaced with a real gazetteer before field use.

## 5. Known minor gaps

- Alerts pagination "Previous/Next" is wired to the backend but the municipal dashboard's
  complaint-ops view intentionally limits geo export to the last 600 points.
- `.doc/.docx` uploads are accepted but return `UNSUPPORTED_FORMAT` (no bundled
  extractor); PDF/txt/md are fully supported.
- Frontend end-to-end browser tests (Playwright) are not included; verification was
  compile/type/build-level plus API-level integration tests.
