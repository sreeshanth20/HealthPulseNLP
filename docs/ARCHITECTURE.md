# HealthPulse AI — Architecture

## 1. System overview

```
┌──────────────────────────── Browser ─────────────────────────────┐
│ Next.js 14 App Router · TypeScript strict · Tailwind 3.4         │
│ shadcn-style UI kit · Recharts · react-leaflet (dynamic import)  │
│ AuthContext (JWT in localStorage, 401 → /login?expired=1)        │
└───────────────────────────────┬──────────────────────────────────┘
                                │ REST /api/v1 (JWT bearer)
┌───────────────────────────────▼──────────────────────────────────┐
│ FastAPI (backend/app)                                            │
│  routers → services → SQLAlchemy 2 models                        │
│  cross-cutting: RBAC deps, audit logger, cache, error handlers   │
└──────────────┬─────────────────────────────┬─────────────────────┘
               │ in-process import            │ SQLAlchemy
┌──────────────▼───────────────┐   ┌─────────▼──────────────────────┐
│ ml/ NLP package (14 modules)  │   │ PostgreSQL 16 + PostGIS        │
│ classifier·NER·embeddings·    │   │ (SQLite for dev/tests)         │
│ dedupe·anomaly·clustering·    │   │ Redis 7 optional (cache only)  │
│ summarizer·crossdomain engine │   └────────────────────────────────┘
└───────────────────────────────┘
```

### Why in-process ML?

The ML package is imported directly by the backend service layer. This removes an
entire model-serving tier from deployment, keeps latency low (small artifacts), and
matches the scale of a district-level deployment. The interface
(`ml/inference/pipeline.py`) is a single facade — if scale ever demands it, the same
API can be served out-of-process without touching business code.

## 2. Data flow: from complaint to alert

```
Citizen submits complaint (form)
  → POST /complaints
    → ml pipeline: normalize → language ID → classify → urgency → location → embed
    → duplicate detection vs last 30 days (district-scoped)
    → persist (complaint + analysis + embedding)
Patient submits symptom report
  → POST /reports
    → ml pipeline: NER → symptom categories → urgency → summary → embed
    → persist (identity stored, never exposed to civic staff)
Health admin runs scan
  → POST /intelligence/scan
    → engine: pair filter (3 km / 21 d) → weighted association → clusters (components)
    → anomaly scan per district → alert de-duplication (7-day window) → persist alerts
  → admin reviews evidence → CONFIRMED → investigation auto-opened
  → field workflow: FIELD_VISIT_SCHEDULED → SAMPLING → CLOSED_*
```

## 3. Database schema (7 tables)

| Table | Purpose | Notable columns |
| --- | --- | --- |
| `users` | accounts + RBAC | email (unique), password_hash, role, is_active |
| `complaints` | civic reports | category(+confidence), urgency(+score+reasons), district, lat/lng, embedding JSON, status, duplicate_of_id(+score) |
| `medical_reports` | voluntary symptom reports | entities/symptoms/categories JSON, urgency, summary/digest, district, lat/lng, embedding JSON |
| `documents` | uploads metadata | sha256, storage_path (never exposed), pages, extracted_text, extraction_status |
| `alerts` | engine output | type, score, districts, evidence JSON, status, disclaimer |
| `investigations` | follow-up workflow | alert_id FK, status, notes, findings, closed_at |
| `audit_logs` | privileged mutation trail | actor, action, entity, detail JSON, ip |

Indexes on all filter columns (category, status, urgency, district, created_at) plus
unique email. PostGIS layer (`database/init.sql`) adds `geom` points + GIST indexes +
sync triggers + `v_district_summary` view.

### State machines

- Complaint: `SUBMITTED → ACKNOWLEDGED → IN_PROGRESS → RESOLVED` with early `REJECTED`
  exits; transitions validated server-side (`COMPLAINT_TRANSITIONS`); terminal states final.
- Alert: `NEW → REVIEWING → CONFIRMED | DISMISSED`; CONFIRMED auto-opens an investigation.
- Investigation: `OPEN → FIELD_VISIT_SCHEDULED → SAMPLING → CLOSED_RESOLVED | CLOSED_NO_ACTION`.

## 4. RBAC matrix

| Endpoint group | CITIZEN | PATIENT | CLINICIAN | MUNICIPAL | HEALTH | SUPER |
| --- | --- | --- | --- | --- | --- | --- |
| Complaints (own) | ✅ | ✅ | — | — | — | — |
| Complaints (all + geo + status) | — | — | — | ✅ | ✅ | ✅ |
| Reports (own) | — | ✅ | — | — | — | ✅ |
| Reports (all, alias-only) | — | — | ✅ | — | ✅ | ✅ |
| Documents (own upload) | — | ✅ | ✅ | — | ✅ | ✅ |
| Intelligence preview | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Intelligence scan / related / alerts / investigations | — | — | — | read | ✅ | ✅ |
| Analytics overview/trends/heatmap/export | — | — | — | ✅ | ✅ | ✅ |
| Users admin / audit logs / system health | — | — | — | — | — | ✅ |

Privacy invariants (enforced + tested):

1. Civic (municipal) staff get **403** on any `/reports` access.
2. Clinicians receive reports with `patient_id: null` and an alias only.
3. Patients see only rows where `patient_id == self`.
4. Report CSV export is de-identified (no ids, no text).
5. Every privileged mutation writes an audit row (actor, action, entity, detail, IP).

## 5. Key design decisions

- **PBKDF2-SHA256 (200k iters)** instead of bcrypt/argon2: zero native deps, constant-time
  compare, swappable single module.
- **Embeddings as JSON columns**: portable across SQLite/Postgres at demo scale
  (384 floats); PostGIS handles the spatial joins in production geometry queries.
- **Alert de-duplication** (same type+title within 7 days unless DISMISSED): scans are
  idempotent and repeatable.
- **Disclaimer constants** rendered from `ml.config.DISCLAIMER` so the wording is
  identical in API responses, alerts, UI and docs.
- **Frontend**: no `next/font` network fetches (system stack), dynamic import for
  Leaflet (SSR-safe), divIcon-free CircleMarkers (no missing-asset issues), server
  component fetches with graceful fallbacks on the landing page.
