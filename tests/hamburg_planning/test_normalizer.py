from app.integrations.hamburg_planning.normalizer import normalize_feature


def test_normalizer_preserves_raw_payload_and_does_not_invent_date() -> None:
    feature = {
        "type": "Feature",
        # Live OGC ids are page-local/sequential; the verified `plan` property
        # is the meaningful stable source identity.
        "id": 0,
        "properties": {
            "plan": "HafenCity Test",
            "description": "Logistik",
            "feststellung": "nein",
            "hotlink_iv": "https://www.hamburg.de/example-plan/",
        },
        # The verified OGC API returns longitude/latitude coordinates.
        "geometry": {"type": "Point", "coordinates": [10.0, 53.55]},
    }

    result = normalize_feature(feature, collection_id="prosin_imverfahren")

    assert result.source_id == "HafenCity Test"
    assert result.title == "HafenCity Test"
    assert result.source_url == "https://www.hamburg.de/example-plan/"
    assert result.published_at is None
    assert result.lifecycle == "in_procedure"
    assert result.raw_payload == feature
    assert "publication_date_not_available_in_verified_feature" in result.quality_notes
    assert "port_logistics" in result.classification.signal_types
    assert result.geometry is not None
    assert result.geometry.x > 100000
    assert result.geometry.y > 1000000


def test_normalizer_surfaces_missing_fields() -> None:
    result = normalize_feature({"type": "Feature", "properties": {}, "geometry": None})

    assert result.source_id is None
    assert result.title is None
    assert result.geometry is None
    assert "missing_source_id" in result.quality_notes
    assert "missing_title" in result.quality_notes
    assert "missing_source_url" in result.quality_notes
    assert "missing_geometry" in result.quality_notes
