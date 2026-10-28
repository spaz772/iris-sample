"""Map normalized Hamburg plans into the IRIS staging contract."""

from __future__ import annotations

from typing import Any

from geoalchemy2.shape import from_shape

from .normalizer import NormalizedPlan


def to_staging_row(plan: NormalizedPlan) -> dict[str, Any]:
    """Create a database-ready row without hiding missing/ambiguous data."""
    if not plan.source_id:
        raise ValueError("source_id is required for idempotent staging")

    signal_type = (
        plan.classification.signal_types[0]
        if plan.classification.signal_types
        else None
    )
    quality_notes = list(plan.quality_notes)
    quality_status = "warning" if quality_notes else "ok"

    return {
        "source": plan.source,
        "source_id": plan.source_id,
        "signal_type": signal_type,
        "title": plan.title,
        "published_at": plan.published_at,
        "source_url": plan.source_url,
        "location_text": None,
        "status": plan.lifecycle,
        "geometry": (
            from_shape(plan.geometry, srid=25832)
            if plan.geometry is not None
            else None
        ),
        "raw_payload": plan.raw_payload,
        "quality_status": quality_status,
        "quality_notes": quality_notes,
        "matched_terms": {
            "signal_types": list(plan.classification.signal_types),
            "terms": list(plan.classification.matched_terms),
            "classification_status": plan.classification.status,
        },
    }
