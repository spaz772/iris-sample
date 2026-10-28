# IRIS-SIG-15 Data Quality Report

## Quality policy

The harvester keeps uncertainty visible instead of inventing source values. A staging record receives `quality_status = warning` whenever normalization emits one or more quality notes. The original public feature is retained in `raw_payload` for traceability.

## Verified live-source findings

Live validation on 28 October 2026 confirmed the Hamburg OGC API collections `prosin_imverfahren` and `hh_hh_festgestellt`. A ten-feature sample from `prosin_imverfahren` exposed `plan`, `feststellung`, optional `hotlink_iv`, and GeoJSON polygonal geometry.

The sample's OGC feature IDs were sequential `0` through `9`, so `plan` is used as the preferred stable source identifier. The live geometry was longitude/latitude and is transformed from EPSG:4326 to the required EPSG:25832 point. A verified example, `Barmbek-Nord44`, normalized to approximately `POINT (569893.00 5938400.00)` in EPSG:25832.

No plan-level publication-date field was present in the verified feature shape. The integration therefore leaves `published_at` null.

## Current known quality conditions

- `missing_source_id`: feature cannot be safely staged because rerun identity would be unstable. The service counts and skips it.
- `missing_title`: source identity may still be usable, but the missing human-readable title remains visible.
- `publication_date_not_available_in_verified_feature`: no plan-level publication-date property was present in the verified live feature shape. Dataset update time and ingestion time are deliberately not substituted.
- `missing_source_url`: `hotlink_iv` is absent for some live plans; this remains visible rather than being synthesized.
- geometry notes from the geometry normalizer: absent, malformed or invalid geometry is reported rather than silently accepted.
- `insufficient_source_text_for_domain_classification`: the feature is retained but not falsely assigned to port logistics, grid-heavy industry or commercial-zone categories.

## Classification limitations

Classification is deterministic and explainable. It searches source property text using documented German domain terms. Matching terms and all matching signal categories are stored in `matched_terms`. The staging table's `signal_type` contains the first matching category for compatibility with the single-value staging field.

The assignment does not define an authoritative taxonomy for the three business objectives, and the verified base feature does not expose detailed zoning intent. In the ten-feature live validation sample the result was `classified=0`, `unclassified=10`. Those records remain staged with warnings rather than receiving unsupported labels.

For alert consumption, non-null `signal_type` can be used as the domain filter. A production-strength next step would enrich the base plan record from authoritative linked plan documents or a structured zoning source before classification.

## Spatial validation

The destination geometry is a point in EPSG:25832. Polygonal source geometries are reduced to a Shapely representative point, which is chosen to remain within the transformed source geometry. Coordinates are transformed, never merely relabelled.

Database validation against PostgreSQL 16.15 / PostGIS 3.4.2 confirmed `Find_SRID('iris_staging','signal_ingest','geometry') = 25832`. Ten live records stored UTM-like easting/northing coordinates rather than longitude/latitude values.

## Idempotency validation

A first live run of ten `prosin_imverfahren` features created 10 rows in `iris_staging.signal_ingest`. The exact same ingestion was executed again. The repository reported ten upsert operations, while the database row count remained 10. This validates the `(source, source_id)` conflict key and duplicate-safe rerun behavior.

## Source and repository limitations

The implementation uses Hamburg's public structured planning interface rather than scraping presentation HTML. The source URL is configurable and the client can also be demonstrated with mocks/fixtures if the public service is unavailable.

The repository's existing Alembic history references revision `7f2c1d8e4a91` from `020c81850f93`, but that predecessor migration is absent from the supplied repository. This is a pre-existing repository condition and was not repaired by inventing historical DDL. For isolated validation, the assessment migration was applied directly through an Alembic operation context to a clean `iris_assessment` database.
