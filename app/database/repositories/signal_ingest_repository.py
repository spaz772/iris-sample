from __future__ import annotations

from collections.abc import Iterable, Mapping

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.database.models.signal_ingest import SignalIngest


class SignalIngestRepository:
    """PostgreSQL upsert repository for staging signals."""

    def __init__(self, session: Session):
        self.session = session

    def upsert_many(self, records: Iterable[Mapping]) -> int:
        rows = [dict(record) for record in records]
        if not rows:
            return 0

        statement = insert(SignalIngest).values(rows)
        excluded = statement.excluded
        statement = statement.on_conflict_do_update(
            constraint="uq_signal_ingest_source_source_id",
            set_={
                "signal_type": excluded.signal_type,
                "title": excluded.title,
                "published_at": excluded.published_at,
                "source_url": excluded.source_url,
                "location_text": excluded.location_text,
                "status": excluded.status,
                "geometry": excluded.geometry,
                "raw_payload": excluded.raw_payload,
                "quality_status": excluded.quality_status,
                "quality_notes": excluded.quality_notes,
                "matched_terms": excluded.matched_terms,
                "updated_at": excluded.updated_at,
            },
        )
        self.session.execute(statement)
        self.session.commit()
        return len(rows)
