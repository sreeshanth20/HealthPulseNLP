# HealthPulse AI — API Reference

Base URL: `http://localhost:8000/api/v1` · Interactive OpenAPI docs: `/docs`

All responses are JSON. Errors use `{"detail": "..."}` with appropriate status codes.
Authentication: `Authorization: Bearer <token>` (JWT HS256, configurable expiry).
Roles in brackets after each endpoint. **SUPER is always allowed everywhere.**

## System (open)

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/health` | liveness + version |
| GET | `/disclaimer` | the platform-wide responsible-AI disclaimer |

## Auth

| Method | Path | Body / notes |
| --- | --- | --- |
| POST | `/auth/register` | `{email, password(min 8), full_name, role=CITIZEN|PATIENT, phone?}` → auto-login token. Staff roles rejected (422). |
| POST | `/auth/login` | `{email, password}` → `{access_token, user}` |
| POST | `/auth/login/form` | OAuth2 password form (Swagger "Authorize" button) |
| GET | `/auth/me` | current user profile |

## Users [SUPER]

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/users?q&role&active&page&page_size` | paginated directory |
| PATCH | `/users/{id}` | `{role?, is_active?}` — refuses to demote/disable the last active SUPER |
| GET | `/users/{id}` | single profile |

## Complaints

| Method | Path | Roles | Notes |
| --- | --- | --- | --- |
| POST | `/complaints` | any | `{title(min 5), text(min 15), address?, lat?, lng?}` → `{complaint, analysis, duplicate_candidates[], duplicate_detected}`. Runs full NLP + dedupe. |
| GET | `/complaints` | any | filters: `status, category, district, urgency, q` + pagination. Non-staff see own rows only. |
| GET | `/complaints/geo` | MUNICIPAL+ | `{points[]}` for mapping, `days` window |
| GET | `/complaints/{id}` | owner or staff | |
| PATCH | `/complaints/{id}/status` | MUNICIPAL+ | `{status, note?}` — transition graph validated (SUBMITTED→ACKNOWLEDGED→IN_PROGRESS→RESOLVED; REJECTED exits) |
| POST | `/complaints/{id}/mark-duplicate` | MUNICIPAL+ | `{original_id}` |
| GET | `/complaints/{id}/similar` | owner or staff | semantic top-k over recent complaints |

`analysis` payload: `category, category_confidence, category_scores{}, classifier_method,
matched_terms[], urgency{label, score, reasons[]}, location{district, lat, lng, confidence,
source}, language, embedding[]`.

## Medical reports

| Method | Path | Roles | Notes |
| --- | --- | --- | --- |
| POST | `/reports` | PATIENT, CLINICIAN, HEALTH, SUPER | `{text(min 15), district?, lat?, lng?}` → full analysis incl. `entities[]`, `symptoms[]`, `symptom_categories[]`, `urgency`, `summary`, `digest`, `patient_alias` |
| GET | `/reports` | PATIENT/CLINICIAN/HEALTH/SUPER | filters `urgency, district, symptom`; patients see own; clinicians get `patient_id: null` (privacy) |
| GET | `/reports/{id}` | same | owner, clinical/health staff |
| POST | `/reports/{id}/summarize` | same | regenerate extractive summary |
| POST | `/reports/from-document` | same | `{document_id}` → creates a report from extracted document text |

Entity shape: `{text, canonical, type: SYMPTOM|MEDICATION|BODY_PART|DURATION|VITAL|AGE, start, end, confidence}`.

## Documents

| Method | Path | Roles | Notes |
| --- | --- | --- | --- |
| POST | `/documents/upload` | PATIENT+ (not CITIZEN) | multipart `file` — pdf/txt/md/doc/docx ≤ 20 MB; PDF text via PyMuPDF; scanned PDFs → `NO_TEXT`; filesystem path never exposed |
| GET | `/documents` | same | own rows (staff see all metadata) |
| GET | `/documents/{id}` | owner or staff | metadata |
| GET | `/documents/{id}/text` | owner or staff | extracted text |
| DELETE | `/documents/{id}` | owner or SUPER | removes file + row |

## Intelligence

| Method | Path | Roles | Notes |
| --- | --- | --- | --- |
| POST | `/intelligence/preview` | any | `{text, lat?, lng?}` → complaint analysis, nothing persisted (live form panel) |
| POST | `/intelligence/preview-report` | PATIENT+ | symptom analysis preview, nothing persisted |
| POST | `/intelligence/scan` | HEALTH, SUPER | `{days: 1..180}` → runs engine over window, persists de-duplicated alerts, returns `{scan stats, alerts_created, alerts[], disclaimer}` |
| GET | `/intelligence/status` | MUNICIPAL+ | engine health + latest alert |
| GET | `/intelligence/related/complaint/{id}` | MUNICIPAL+ | symptom reports near one complaint (semantic + ≤10 km) |
| GET | `/intelligence/related/report/{id}` | HEALTH+ | complaints near one report |

## Alerts & investigations

| Method | Path | Roles | Notes |
| --- | --- | --- | --- |
| GET | `/alerts?type&status&district&min_score&page` | MUNICIPAL+ | |
| GET | `/alerts/{id}` | MUNICIPAL+ | includes full `evidence[]` |
| PATCH | `/alerts/{id}/status` | HEALTH+ | `{status: NEW|REVIEWING|CONFIRMED|DISMISSED, note?}`; CONFIRMED auto-opens an investigation |
| GET | `/investigations?status&alert_id&page` | MUNICIPAL+ | |
| PATCH | `/investigations/{id}` | MUNICIPAL+ | `{status?, notes?, findings?, assigned_to_id?}` |

## Analytics

| Method | Path | Roles | Notes |
| --- | --- | --- | --- |
| GET | `/analytics/public` | open | aggregate counts + category histogram (cached 30 s) |
| GET | `/analytics/overview` | any (role-shaped) | citizens get own stats; staff get operational KPIs |
| GET | `/analytics/trends?days&district` | MUNICIPAL+ | daily complaint+report counts |
| GET | `/analytics/districts` | MUNICIPAL+ | per-district aggregates |
| GET | `/analytics/heatmap?days` | MUNICIPAL+ | weighted geo points (complaints + reports) |
| GET | `/analytics/export?dataset=complaints|reports` | MUNICIPAL+ (reports: HEALTH+) | CSV download; reports export is de-identified |

## Admin [SUPER]

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/audit-logs?actor_id&action&entity_type&q&page` | full mutation trail |
| GET | `/system/health` | DB counts, cache status, NLP backends, storage usage |
