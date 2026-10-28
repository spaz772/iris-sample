"""Runner for IRIS-SIG-15 Hamburg planning ingestion."""

from __future__ import annotations

import os

from app.database.session import SessionLocal
from app.integrations.hamburg_planning.client import HamburgPlanningClient
from app.integrations.hamburg_planning.service import HamburgPlanningService, IngestionReport


def _configured_collections() -> list[str]:
    raw = os.getenv("HAMBURG_PLANNING_COLLECTIONS", "")
    return [value.strip() for value in raw.split(",") if value.strip()]


def run(
    *,
    collection_ids: list[str] | None = None,
    limit: int = 100,
    max_pages: int | None = None,
) -> IngestionReport:
    collections = collection_ids or _configured_collections()
    if not collections:
        client = HamburgPlanningClient()
        available = [
            str(item.get("id"))
            for item in client.list_collections()
            if item.get("id")
        ]
        raise RuntimeError(
            "No Hamburg planning collections configured. Set "
            "HAMBURG_PLANNING_COLLECTIONS to a comma-separated list. "
            f"Source currently reports these collection ids: {available}"
        )

    with SessionLocal() as session:
        report = HamburgPlanningService(session).run(
            collections,
            limit=limit,
            max_pages=max_pages,
        )

    print("Hamburg planning ingestion complete")
    print(f"Collections       : {report.collections}")
    print(f"Features seen     : {report.features_seen}")
    print(f"Rows written      : {report.rows_written}")
    print(f"Missing IDs       : {report.skipped_missing_id}")
    print(f"Classified        : {report.classified}")
    print(f"Unclassified      : {report.unclassified}")
    return report
