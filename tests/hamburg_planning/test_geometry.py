from app.integrations.hamburg_planning.geometry import representative_point_25832


def test_polygon_returns_representative_point() -> None:
    geometry = {
        "type": "Polygon",
        "coordinates": [[[566000, 5933000], [566200, 5933000], [566200, 5933200], [566000, 5933200], [566000, 5933000]]],
    }

    result = representative_point_25832(geometry)

    assert result.point is not None
    assert result.quality_notes == ()
    assert 566000 <= result.point.x <= 566200
    assert 5933000 <= result.point.y <= 5933200


def test_missing_geometry_is_visible() -> None:
    result = representative_point_25832(None)

    assert result.point is None
    assert "missing_geometry" in result.quality_notes


def test_4326_geometry_is_transformed_not_relabelled() -> None:
    result = representative_point_25832(
        {"type": "Point", "coordinates": [10.0, 53.55]},
        source_crs="EPSG:4326",
    )

    assert result.point is not None
    assert result.point.x > 100000
    assert result.point.y > 1000000
