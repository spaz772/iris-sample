"""Geometry validation and point derivation for Hamburg planning features."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyproj import CRS, Transformer
from shapely.geometry import Point, shape
from shapely.ops import transform
from shapely.validation import explain_validity

TARGET_CRS = "EPSG:25832"


@dataclass(frozen=True)
class GeometryResult:
    point: Point | None
    quality_notes: tuple[str, ...]


def representative_point_25832(
    geometry: dict[str, Any] | None,
    *,
    source_crs: str = TARGET_CRS,
) -> GeometryResult:
    """Validate a GeoJSON geometry and return an interior/representative point.

    Coordinates are transformed, never merely relabelled. Invalid or missing
    geometry remains visible through quality notes rather than being silently
    accepted.
    """
    if not geometry:
        return GeometryResult(None, ("missing_geometry",))

    try:
        geom = shape(geometry)
    except (TypeError, ValueError, KeyError) as exc:
        return GeometryResult(None, (f"malformed_geometry:{exc}",))

    if geom.is_empty:
        return GeometryResult(None, ("empty_geometry",))
    if not geom.is_valid:
        return GeometryResult(None, (f"invalid_geometry:{explain_validity(geom)}",))

    try:
        source = CRS.from_user_input(source_crs)
        target = CRS.from_user_input(TARGET_CRS)
    except Exception as exc:  # pyproj raises several CRS-specific subclasses
        return GeometryResult(None, (f"invalid_source_crs:{exc}",))

    if source != target:
        try:
            transformer = Transformer.from_crs(source, target, always_xy=True)
            geom = transform(transformer.transform, geom)
        except Exception as exc:
            return GeometryResult(None, (f"crs_transform_failed:{exc}",))

    if isinstance(geom, Point):
        point = geom
    else:
        point = geom.representative_point()

    if point.is_empty or not point.is_valid:
        return GeometryResult(None, ("invalid_representative_point",))

    return GeometryResult(point, ())
