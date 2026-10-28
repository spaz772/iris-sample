# IRIS-SIG-15 Hamburg Master Planning Geoportal Harvester

## Purpose

This integration harvests Hamburg Bebauungsplan records for signals relevant to port logistics, grid-heavy industrial modifications and commercial-zone alerts. It writes traceable, idempotent records to `iris_staging.signal_ingest`.

The assignment names `https://geoportal-hamburg.de/b-plaene` as the source. The implementation uses Hamburg's public structured OGC API at `https://api.hamburg.de/datasets/v1/bplaene/` rather than scraping presentation HTML. The API base URL is configurable in `HamburgPlanningClient`, and no credentials are embedded in source.

## Verified live source contract

A live-source check on 28 October 2026 returned two collections:

- `prosin_imverfahren`: plans currently in procedure.
- `hh_hh_festgestellt`: established plans (`Festgestellte Bebauungspläne`).

Live `prosin_imverfahren` features were observed with GeoJSON `MultiPolygon` geometry and properties `plan`, `feststellung` and, when available, `hotlink_iv`. The OGC response geometry was longitude/latitude (EPSG:4326), so the integration transforms it to EPSG:25832 rather than relabelling coordinates.

The OGC response `id` values observed in a ten-feature sample were sequential `0` through `9`; therefore the verified `plan` property is preferred as the stable source identity. Example observed plan identifiers included `Barmbek-Nord44`, `Barmbek-Nord60` and `Jenfeld29`.

No plan-level publication date was present in the verified feature shape. `published_at` therefore remains `NULL`; dataset update time and ingestion time are not substituted.

## Architecture

`HamburgPlanningClient` retrieves OGC collections/features with retries, timeout handling and pagination-loop protection. `normalize_feature` preserves the source feature, validates geometry and derives an EPSG:25832 representative point. `classify_signal` applies transparent keyword rules. `to_staging_row` maps the normalized record to the staging contract. `SignalIngestRepository` performs PostgreSQL `ON CONFLICT DO UPDATE` using `(source, source_id)` as the stable identity.

## Configuration

Database access uses the repository's existing `DATABASE_URL` environment variable. Keep credentials in a local `.env` file that is excluded from Git.

The verified in-procedure collection can be configured as:

```powershell
$env:HAMBURG_PLANNING_COLLECTIONS="prosin_imverfahren"
```

If the variable is absent, the runner queries the source's collections endpoint and reports the available IDs instead of ingesting an assumed collection.

## Database

The assessment table uses PostGIS `POINT` geometry with SRID 25832 and a unique `(source, source_id)` constraint. The implementation was live-tested against PostgreSQL 16.15 and PostGIS 3.4.2.

The supplied repository contains a pre-existing Alembic ancestry gap: migration `020c81850f93` references missing revision `7f2c1d8e4a91`. The assessment code does not invent a replacement historical migration. In the isolated assessment database, migration `c15a4b7e2d91_create_signal_ingest_staging.py` was applied directly through an Alembic operation context, creating `iris_staging.signal_ingest`; `Find_SRID` then returned `25832`.

In a repository with complete migration history, the intended normal deployment path is `alembic upgrade head`. With this supplied sample repository, the missing historical predecessor must first be restored or reconciled by the repository owner.

## Running

The dedicated runner can be invoked from Python after collection IDs are configured:

```powershell
python -c "from app.runners.hamburg_planning_runner import run; run()"
```

A small verified live run can be performed with:

```powershell
python -c "from app.database.session import SessionLocal; from app.integrations.hamburg_planning.service import HamburgPlanningService; s=SessionLocal(); print(HamburgPlanningService(s).run(['prosin_imverfahren'], limit=10, max_pages=1)); s.close()"
```

## Mapping and assumptions

- `source`: constant `hamburg_bebauungsplaene`.
- `source_id`: verified `plan` property is preferred because observed OGC feature IDs were response-sequential; feature `id` remains a fallback.
- `title`: first available textual `plan`/name/title/bezeichnung property.
- `published_at`: intentionally `NULL` because no plan-level publication date was present in the verified live feature shape.
- `source_url`: verified `hotlink_iv` property when present; absence is retained as a quality note.
- `status`: inferred from the verified collection (`prosin_imverfahren` -> `in_procedure`, `hh_hh_festgestellt` -> `established`) with `feststellung` available as supporting source context.
- `geometry`: OGC GeoJSON is treated as EPSG:4326 and transformed to a representative EPSG:25832 point.
- `raw_payload`: complete source feature for auditability.
- `signal_type`: first matching domain category; all matches and matched terms are retained in `matched_terms`.

The business classification taxonomy is not defined by the assignment. The included keyword rules are explicit assessment assumptions and are deliberately deterministic and reviewable.

## Domain filtering behavior

The verified base OGC feature exposes plan identity, lifecycle, link and geometry, but it does not expose detailed zoning intent. In the ten-feature live validation sample, none of the available source text supported a defensible port-logistics, grid-heavy-industry or commercial-zone classification. The run therefore produced `classified=0`, `unclassified=10` rather than fabricating domain labels.

Unclassified source records are retained in staging with `quality_status=warning` and `insufficient_source_text_for_domain_classification`. This makes the extraction auditable and allows a later enrichment step to use linked plan documents or an authoritative zoning source. Consumers seeking only objective-matching alerts should filter to non-null `signal_type`. This is intentionally conservative: absence of source evidence is not treated as evidence of a business category.

## Idempotency

The staging table has `UNIQUE(source, source_id)`. `SignalIngestRepository.upsert_many` uses PostgreSQL `INSERT ... ON CONFLICT DO UPDATE`, so replaying an unchanged feature does not create a second row.

Live validation ingested ten `prosin_imverfahren` features. The first run produced 10 staging rows. Re-running the same ten features again left the table at 10 rows, demonstrating duplicate-safe rerun behavior against PostgreSQL/PostGIS.

## Tests

Tests under `tests/hamburg_planning/` cover client failures and pagination, geometry/CRS behavior, classification, conservative normalization, staging mapping, service orchestration and PostgreSQL conflict-upsert behavior. Network behavior is mocked so the core transformation can be demonstrated without production access.

The local verification run on Python 3.12 collected 17 tests and all 17 passed after aligning fixtures with the verified source contract.

Run locally with:

```powershell
python -m pytest tests/hamburg_planning -v
```

## Validation and quality evidence

`validation.sql` contains duplicate, geometry/SRID and quality-warning checks. `sample_output.json` contains a public-source-derived example from the verified live run. `quality_report.md` documents unresolved fields, classification limitations, spatial handling, live validation results and the pre-existing Alembic history issue.
