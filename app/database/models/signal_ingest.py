from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.entity import BaseEntity


class SignalIngest(BaseEntity):
    """Staging record for externally harvested planning signals."""

    __tablename__ = "signal_ingest"
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_signal_ingest_source_source_id"),
        Index("idx_signal_ingest_signal_type", "signal_type"),
        Index("idx_signal_ingest_status", "status"),
        Index("idx_signal_ingest_geometry", "geometry", postgresql_using="gist"),
        {"schema": "iris_staging"},
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    signal_type: Mapped[str | None] = mapped_column(String(100))
    title: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_url: Mapped[str | None] = mapped_column(Text)
    location_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(100))
    geometry: Mapped[str | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=25832, spatial_index=False)
    )
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    quality_status: Mapped[str] = mapped_column(String(50), nullable=False)
    quality_notes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    matched_terms: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
