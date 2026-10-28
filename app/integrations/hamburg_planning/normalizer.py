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
    source_crs: str = "EPSG:4326",
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

    # The verified OGC feature exposes plan/feststellung/hotlink_iv but no
    # plan-level publication date. Do not substitute ingestion or catalogue time.
    published_at = None
    notes.append("publication_date_not_available_in_verified_feature")

    source_url = _first_text(properties, "hotlink_iv")
    if source_url is None:
        notes.append("missing_source_url")

    geometry_result: GeometryResult = representative_point_25832(
        feature.get("geometry"),
        source_crs=source_crs,
    )
    notes.extend(geometry_result.quality_notes)

    classification = classify_signal(properties)
    if classification.status == "unclassified":
        notes.append("insufficient_source_text_for_domain_classification")

    lifecycle = _lifecycle(collection_id, properties)

    return NormalizedPlan(
        source=SOURCE_NAME,
        source_id=source_id,
        title=title,
        published_at=published_at,
        source_url=source_url,
        lifecycle=lifecycle,
        geometry=geometry_result.point,
        classification=classification,
        raw_payload=feature,
        quality_notes=tuple(notes),
    )


def _source_id(feature: dict[str, Any], properties: dict[str, Any]) -> str | None:
    # Live inspection showed OGC ids 0,1,2,... while `plan` contains the actual
    # planning identifier (for example Barmbek-Nord44). Prefer the semantic plan
    # identifier so idempotency does not depend on response ordering.
    plan = properties.get("plan")
    if plan is not None and str(plan).strip():
        return str(plan).strip()

    feature_id = feature.get("id")
    if feature_id is not None and str(feature_id).strip():
        return str(feature_id).strip()
    return None


def _first_text(properties: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = properties.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _lifecycle(collection_id: str | None, properties: dict[str, Any]) -> str | None:
    if collection_id:
        lowered = collection_id.lower()
        if "imverfahren" in lowered or "im_verfahren" in lowered:
            return "in_procedure"
        if "festgestellt" in lowered:
            return "established"

    feststellung = properties.get("feststellung")
    if isinstance(feststellung, str):
        value = feststellung.strip().lower()
        if value == "nein":
            return "in_procedure"
        if value in {"ja", "yes"}:
            return "established"
    return None
