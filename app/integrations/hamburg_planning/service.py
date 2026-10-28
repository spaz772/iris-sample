"""Orchestrate Hamburg planning extraction, normalization and staging."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from app.database.repositories.signal_ingest_repository import SignalIngestRepository

from .client import HamburgPlanningClient
from .normalizer import normalize_feature
from .staging import to_staging_row


@dataclass(frozen=True)
class IngestionReport:
    collections: int = 0
    features_seen: int = 0
    rows_written: int = 0
    skipped_missing_id: int = 0
    classified: int = 0
    unclassified: int = 0


class HamburgPlanningService:
    """Harvest selected public Hamburg planning collections into staging."""

    def __init__(
        self,
        session: Session,
        *,
        client: HamburgPlanningClient | None = None,
        repository: SignalIngestRepository | None = None,
    ) -> None:
        self.client = client or HamburgPlanningClient()
        self.repository = repository or SignalIngestRepository(session)

    def run(
        self,
        collection_ids: Iterable[str],
        *,
        limit: int = 100,
        max_pages: int | None = None,
        source_crs: str = "EPSG:4326",
    ) -> IngestionReport:
        ids = [collection_id.strip() for collection_id in collection_ids if collection_id.strip()]
        if not ids:
            raise ValueError("at least one Hamburg collection_id is required")

        seen = written = skipped = classified = unclassified = 0

        for collection_id in ids:
            rows = []
            for feature in self.client.iter_features(
                collection_id,
                limit=limit,
                max_pages=max_pages,
            ):
                seen += 1
                plan = normalize_feature(
                    feature,
                    collection_id=collection_id,
                    source_crs=source_crs,
                )
                if plan.classification.status == "classified":
                    classified += 1
                else:
                    unclassified += 1

                if not plan.source_id:
                    skipped += 1
                    continue
                rows.append(to_staging_row(plan))

            written += self.repository.upsert_many(rows)

        return IngestionReport(
            collections=len(ids),
            features_seen=seen,
            rows_written=written,
            skipped_missing_id=skipped,
            classified=classified,
            unclassified=unclassified,
        )
