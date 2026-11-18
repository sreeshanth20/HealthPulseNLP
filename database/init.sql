-- =============================================================================
-- HealthPulse AI - canonical PostgreSQL / PostGIS schema
--
-- This file is the reference schema for production deployments with PostGIS.
-- The application's Alembic migration (backend/alembic/versions/) creates the
-- same portable schema; this file ADDS the PostGIS-specific extension, geometry
-- columns, spatial indexes and reporting views on top.
--
-- Mounted automatically by docker-compose (postgres initdb.d).
-- =============================================================================

-- Extensions -----------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core tables are created by Alembic on backend startup (see Docker CMD):
--   users, complaints, medical_reports, documents, alerts,
--   investigations, audit_logs
-- The statements below only enhance an Alembic-migrated database.
-- Idempotent guards keep the file safe to re-run.

-- PostGIS geometry columns ----------------------------------------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'complaints') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'complaints' AND column_name = 'geom') THEN
            ALTER TABLE complaints ADD COLUMN geom geometry(Point, 4326);
        END IF;
        UPDATE complaints
        SET geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        WHERE lat IS NOT NULL AND lng IS NOT NULL AND geom IS NULL;
        CREATE INDEX IF NOT EXISTS ix_complaints_geom ON complaints USING GIST (geom);
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'medical_reports') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_name = 'medical_reports' AND column_name = 'geom') THEN
            ALTER TABLE medical_reports ADD COLUMN geom geometry(Point, 4326);
        END IF;
        UPDATE medical_reports
        SET geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        WHERE lat IS NOT NULL AND lng IS NOT NULL AND geom IS NULL;
        CREATE INDEX IF NOT EXISTS ix_medical_reports_geom ON medical_reports USING GIST (geom);
    END IF;
END $$;

-- Keep geometry in sync with lat/lng ------------------------------------------
CREATE OR REPLACE FUNCTION sync_point_geom() RETURNS trigger AS $$
BEGIN
    IF NEW.lat IS NOT NULL AND NEW.lng IS NOT NULL THEN
        NEW.geom := ST_SetSRID(ST_MakePoint(NEW.lng, NEW.lat), 4326);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'complaints') THEN
        DROP TRIGGER IF EXISTS trg_complaints_geom ON complaints;
        CREATE TRIGGER trg_complaints_geom BEFORE INSERT OR UPDATE OF lat, lng ON complaints
        FOR EACH ROW EXECUTE FUNCTION sync_point_geom();
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'medical_reports') THEN
        DROP TRIGGER IF EXISTS trg_medical_reports_geom ON medical_reports;
        CREATE TRIGGER trg_medical_reports_geom BEFORE INSERT OR UPDATE OF lat, lng ON medical_reports
        FOR EACH ROW EXECUTE FUNCTION sync_point_geom();
    END IF;
END $$;

-- Reporting views ---------------------------------------------------------------
DROP VIEW IF EXISTS v_district_summary;
CREATE VIEW v_district_summary AS
SELECT d.name AS district,
       COALESCE(c.n_complaints, 0)  AS n_complaints,
       COALESCE(c.n_open, 0)        AS n_open_complaints,
       COALESCE(r.n_reports, 0)     AS n_reports,
       COALESCE(r.n_high_urgency,0) AS n_high_urgency_reports
FROM (VALUES
    ('Harbourview'), ('Millbrook'), ('Eastfields'), ('Old Town'),
    ('Northgate'), ('Riverside'), ('Greenhills'), ('Southbay')
) AS d(name)
LEFT JOIN (
    SELECT district, COUNT(*) AS n_complaints,
           COUNT(*) FILTER (WHERE status IN ('SUBMITTED','ACKNOWLEDGED','IN_PROGRESS')) AS n_open
    FROM complaints GROUP BY district
) c ON c.district = d.name
LEFT JOIN (
    SELECT district, COUNT(*) AS n_reports,
           COUNT(*) FILTER (WHERE urgency IN ('HIGH','CRITICAL')) AS n_high_urgency
    FROM medical_reports GROUP BY district
) r ON r.district = d.name;

-- Example spatial query used by the intelligence engine (PostGIS path):
--   SELECT c.id, r.id
--   FROM complaints c JOIN medical_reports r
--     ON ST_DWithin(c.geom, r.geom, 3000)          -- 3 km radius
--    AND c.created_at BETWEEN r.created_at - INTERVAL '21 days'
--                          AND r.created_at + INTERVAL '21 days';
-- (The portable Python engine in ml/crossdomain uses haversine so the whole
--  stack also runs on SQLite for tests and CI.)
