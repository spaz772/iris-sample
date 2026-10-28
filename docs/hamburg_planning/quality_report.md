# IRIS-SIG-15 Data Quality Report

## Quality policy

The harvester keeps uncertainty visible instead of inventing source values. A staging record receives `quality_status = warning` whenever normalization emits one or more quality notes. The original public feature is retained in `raw_payload` for traceability.

## Current known quality conditions

- `missing_source_id`: feature cannot be safely staged because rerun identity would be unstable. The service counts and skips it.
- `missing_title`: source identity may still be usable, but the missing human-readable title remains visible.
- `publication_date_not_mapped`: no plan-level publication-date property has yet been verified strongly enough to map. Dataset update time and ingestion time are deliberately not substituted.
- geometry notes from the geometry normalizer: absent, malformed or invalid geometry is reported rather than silently accepted.
- `insufficient_source_text_for_domain_classification`: the feature is retained but not falsely assigned to port logistics, grid-heavy industry or commercial-zone categories.

## Classification limitations

Classification is deterministic and explainable. It searches source property text using documented German domain terms. Matching terms and all matching signal categories are stored in `matched_terms`. The staging table's `signal_type` contains the first matching category for compatibility with the single-value staging field.

The assignment does not define an authoritative taxonomy for the three business objectives. The rule set is therefore an explicit assessment assumption and should be tuned with domain-owner feedback rather than treated as ground truth.

## Spatial assumptions

The destination geometry is a point in EPSG:25832. Polygonal source geometries are reduced to a Shapely representative point, which is chosen to remain within the source geometry. Coordinates are transformed when the source CRS differs; coordinates are never merely relabelled as EPSG:25832.

## Source limitations

The implementation uses Hamburg's public structured planning interface rather than scraping presentation HTML. The source URL is configurable and the client can be demonstrated with mocks/fixtures if the public service is unavailable.

The repository's existing Alembic history references revision `7f2c1d8e4a91` from `020c81850f93`, but that predecessor migration is absent from the supplied repository. This is a pre-existing repository condition and was not repaired by inventing historical DDL. The assessment migration is based on the latest visible revision.
