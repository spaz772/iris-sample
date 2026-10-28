-- IRIS-SIG-15 validation queries

-- Volume and classification summary.
SELECT
    signal_type,
    quality_status,
    count(*) AS records
FROM iris_staging.signal_ingest
WHERE source = 'hamburg_bebauungsplaene'
GROUP BY signal_type, quality_status
ORDER BY signal_type NULLS LAST, quality_status;

-- Acceptance check: duplicate source identities must never exist.
SELECT source, source_id, count(*) AS duplicate_count
FROM iris_staging.signal_ingest
WHERE source = 'hamburg_bebauungsplaene'
GROUP BY source, source_id
HAVING count(*) > 1;

-- Geometry must be a valid EPSG:25832 point when present.
SELECT
    source_id,
    ST_GeometryType(geometry) AS geometry_type,
    ST_SRID(geometry) AS srid,
    ST_IsValid(geometry) AS is_valid
FROM iris_staging.signal_ingest
WHERE source = 'hamburg_bebauungsplaene'
  AND geometry IS NOT NULL
  AND (
      ST_GeometryType(geometry) <> 'ST_Point'
      OR ST_SRID(geometry) <> 25832
      OR NOT ST_IsValid(geometry)
  );

-- Missing/ambiguous data remains visible for review.
SELECT
    source_id,
    title,
    signal_type,
    quality_status,
    quality_notes
FROM iris_staging.signal_ingest
WHERE source = 'hamburg_bebauungsplaene'
  AND quality_status <> 'ok'
ORDER BY updated_at DESC;

-- Rerun/idempotency check: record count should remain unchanged after
-- running an identical source fixture twice.
SELECT count(*) AS hamburg_signal_count
FROM iris_staging.signal_ingest
WHERE source = 'hamburg_bebauungsplaene';
