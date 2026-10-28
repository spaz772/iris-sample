"""Normalize Hamburg OGC features without guessing absent source fields."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from shapely.geometry import Point

from .classifier import ClassificationResult, classify_signal
from .geometry import GeometryResult, representative_point_25832

SOURCE_NAME = "hamburg_bebauungsplaene"


@dataclass(frozen=True)
class NormalizedPlan:
    source: str
    source_id: str | None
    title: str | None
    published_at: datetime | None
    source_url: str | None
    lifecycle: str | None
    geometry: Point | None
    classification: ClassificationResult
    raw_payload: dict[str, Any]
    quality_notes: tuple[str, ...]


def normalize_feature(
    feature: dict[str, Any],
    *,
    collection_id: str | None = None,
    source_crs: str = "EPSG:25832",
) -> NormalizedPlan:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        properties = {}

    notes: list[str] = []
    source_id = _source_id(feature, properties)
    if source_id is None:
        notes.append("missing_source_id")

    title = _first_text(properties, "plan", "name", "title", "bezeichnung")
    if title is None:
        notes.append("missing_title")

    # We intentionally do not substitute ingestion time or dataset publication
    # time for a plan-level publication date. Add mappings only after a live
    # source field is verified.
    published_at = None
    notes.append("publication_date_not_mapped")

    geometry_result: GeometryResult = representative_point_25832(
        feature.get("geometry"),
        source_crs=source_crs,
    )
    notes.extend(geometry_result.quality_notes)

    classification = classify_signal(properties)
    if classification.status == "unclassified":
        notes.append("insufficient_source_text_for_domain_classification")

    lifecycle = _lifecycle(collection_id)

    return NormalizedPlan(
        source=SOURCE_NAME,
        source_id=source_id,
        title=title,
        published_at=published_at,
        source_url=None,
        lifecycle=lifecycle,
        geometry=geometry_result.point,
        classification=classification,
        raw_payload=feature,
        quality_notes=tuple(notes),
    )


def _source_id(feature: dict[str, Any], properties: dict[str, Any]) -> str | None:
    feature_id = feature.get("id")
    if feature_id is not None and str(feature_id).strip():
        return str(feature_id).strip()

    # 'plan' is a verified Hamburg attribute and is a useful deterministic
    # fallback, but remains visibly distinct from a true OGC feature id.
    plan = properties.get("plan")
    if plan is not None and str(plan).strip():
        return str(plan).strip()
    return None


def _first_text(properties: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = properties.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _lifecycle(collection_id: str | None) -> str | None:
    if not collection_id:
        return None
    lowered = collection_id.lower()
    if "imverfahren" in lowered or "im_verfahren" in lowered:
        return "in_procedure"
    if "festgestellt" in lowered:
        return "established"
    return None
