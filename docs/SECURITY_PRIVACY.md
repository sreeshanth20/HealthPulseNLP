# HealthPulse AI — Security & Privacy Design

## 1. Authentication

- **Password storage:** PBKDF2-HMAC-SHA256, 200,000 iterations, 16-byte random salt per
  user, constant-time comparison (`app/core/security.py`). Zero native dependencies;
  swap point for argon2id documented in the module.
- **Sessions:** JWT (HS256, `iss`/`iat`/`exp` claims) issued by
  `/auth/login|register|login/form`; expiry configurable (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Self-service registration is limited** to CITIZEN/PATIENT by schema validation —
  staff roles (CLINICIAN, MUNICIPAL_ADMIN, HEALTH_ADMIN, SUPER_ADMIN) can only be
  provisioned by a super administrator (or the seed script), and this is tested.
- Account disabling takes effect immediately (401 on inactive users).

## 2. Authorization (RBAC)

- Single dependency factory (`require_roles`) guards every privileged route; SUPER_ADMIN
  is always permitted.
- Ownership checks are separate from role checks (complaint/report/document access).
- Server-side transition graphs prevent illegal workflow jumps regardless of client UI.

## 3. Privacy boundaries (tested invariants)

1. **Civic staff never see medical data** — `GET /reports` returns 403 for
   MUNICIPAL_ADMIN.
2. **Clinicians see content, not identity** — report serializers null out `patient_id`
   for anyone except the owning patient; display uses `Patient #NNNNN` aliases.
3. **Patients see only their own rows** — enforced in query scope.
4. **Report CSV export is de-identified** — no ids, no free text, only
   urgency/district/category aggregates.
5. **Document bytes are stored outside the DB** in a content-addressed store
   (`sha256/...`), permissions 0o640, filenames sanitized (path traversal neutralized —
   tested), and filesystem paths are **never** returned by the API.

## 4. Input validation & upload safety

- Pydantic schemas bound every field (lengths, geo ranges, role patterns, numeric ranges).
- Uploads: extension allowlist (pdf/txt/md/doc/docx), 20 MB cap, empty-file rejection,
  MIME recorded, extension/size tests included.
- Search/filter inputs are parameterized via SQLAlchemy (no string interpolation).

## 5. Audit trail

- Every privileged mutation writes `audit_logs`: actor id/role, action, entity type/id,
  JSON detail (truncated), client IP (X-Forwarded-For aware), timestamp.
- Audit writes are best-effort — they never break business flow — but all critical
  paths (auth events, complaint lifecycle, report creation, document upload/delete,
  alert decisions, investigations, role changes, exports, scans) are covered.
- Super admins get a filterable log viewer (action/entity/free-text in details).

## 6. Data protection posture

- Disclaimer/invariant: association scores ≠ clinical risk; no diagnosis anywhere.
- All bundled data is synthetic; nothing resembles real patient records.
- `.gitignore` excludes DBs, storage, env files and model binaries from version control;
  `.env.example` documents every knob without real secrets.

## 7. Production hardening checklist (not in demo scope)

- Serve JWT via httpOnly Secure cookies + CSRF tokens; add refresh-token rotation.
- Move to argon2id; add per-IP and per-account rate limiting (e.g. slowapi/Redis).
- Enforce HTTPS/HSTS at the edge; set `CORS_ORIGINS` to exact frontend origins.
- Encrypt document storage at rest (LUKS/cloud-KMS); virus-scan uploads (ClamAV).
- Rotate `SECRET_KEY` per environment; never commit `.env`.
- Add retention policies: audit log WORM archive, document TTLs, report anonymization.
