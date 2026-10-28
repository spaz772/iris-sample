# IRIS-SIG-15 Hamburg Master Planning Geoportal Harvester

## Purpose

This integration harvests Hamburg Bebauungsplan records for signals relevant to port logistics, grid-heavy industrial modifications and commercial-zone alerts. It writes traceable, idempotent records to `iris_staging.signal_ingest`.

The assignment names `https://geoportal-hamburg.de/b-plaene` as the source. The implementation prefers Hamburg's public structured OGC API at `https://api.hamburg.de/datasets/v1/bplaene/` rather than scraping presentation HTML. The API base URL is configurable in `HamburgPlanningClient`, and no credentials are embedded in source.

## Architecture

`HamburgPlanningClient` retrieves OGC collections/features with retries, timeout handling and pagination-loop protection. `normalize_feature` preserves the source feature, validates geometry and derives an EPSG:25832 representative point. `classify_signal` applies transparent keyword rules. `to_staging_row` maps the normalized record to the staging contract. `SignalIngestRepository` performs PostgreSQL `ON CONFLICT DO UPDATE` using `(source, source_id)` as the stable identity.

## Configuration

Database access uses the repository's existing `DATABASE_URL` environment variable. Configure one or more verified Hamburg collection IDs as a comma-separated environment variable:

```powershell
$env:HAMBURG_PLANNING_COLLECTIONS="<collection-id-1>,<collection-id-2>"
```

Do not guess collection IDs. If the variable is absent, the runner queries the source's collections endpoint and reports the available IDs instead of ingesting an assumed collection.

## Database

Apply migrations using the repository's normal Alembic workflow:

```powershell
alembic upgrade head
```

The new table uses a PostGIS `POINT` geometry with SRID 25832 and a unique `(source, source_id)` constraint. The implementation is written against standard SQLAlchemy/PostGIS functionality compatible with the assignment target of PostgreSQL 16 / PostGIS 3.4.

Important: the supplied repository already contains an Alembic ancestry gap. Migration `020c81850f93` references missing revision `7f2c1d8e4a91`. The assessment code does not invent a replacement historical migration. If `alembic upgrade head` fails because of that missing predecessor, the repository owner needs to provide or reconcile the original migration history.

## Running

The dedicated runner can be invoked from Python after collection IDs are configured:

```powershell
python -c "from app.runners.hamburg_planning_runner import run; run()"
```

For a small source demonstration, pass a collection and page cap directly:

```powershell
python -c "from app.runners.hamburg_planning_runner import run; run(collection_ids=['<verified-collection-id>'], limit=10, max_pages=1)"
```

## Mapping and assumptions

- `source`: constant `hamburg_bebauungsplaene`.
- `source_id`: OGC feature `id`; verified `plan` property is used as deterministic fallback.
- `title`: first available textual plan/name/title/bezeichnung property.
- `published_at`: intentionally `NULL` until a plan-level publication date field is verified. Dataset update time and ingestion time are not substituted.
- `status`: inferred only from a collection ID that clearly identifies established or in-procedure plans.
- `geometry`: validated source geometry converted to a representative EPSG:25832 point.
- `raw_payload`: complete source feature for auditability.
- `signal_type`: first matching domain category; all matches and matched terms are retained in `matched_terms`.

The business classification taxonomy is not defined by the assignment. The included keyword rules are explicit assessment assumptions and are deliberately deterministic and reviewable.

## Idempotency

The staging table has `UNIQUE(source, source_id)`. `SignalIngestRepository.upsert_many` uses PostgreSQL `INSERT ... ON CONFLICT DO UPDATE`, so replaying an unchanged feature does not create a second row. `first_seen_at` remains unchanged while `last_seen_at` and the normalized fields are refreshed.

## Tests

Tests under `tests/hamburg_planning/` cover client failures and pagination, geometry/CRS behavior, classification, conservative normalization, staging mapping, service orchestration and PostgreSQL conflict-upsert behavior. Network behavior is mocked so the core transformation can be demonstrated without production access.

Run locally with the repository's test runner, for example:

```powershell
pytest tests/hamburg_planning -q
```

## Validation and quality evidence

`validation.sql` contains duplicate, geometry/SRID and quality-warning checks. `sample_output.json` is explicitly illustrative rather than presented as a verbatim live record. `quality_report.md` documents unresolved fields, classification assumptions, spatial assumptions and the pre-existing Alembic history issue.

A final submission should include the local test output and, when the public source is reachable, a small live-source run showing the verified collection IDs and observed source fields. Do not claim a live publication-date mapping until the source actually supplies and verifies one.
