from app.integrations.hamburg_planning.normalizer import normalize_feature


def test_normalizer_preserves_raw_payload_and_does_not_invent_date() -> None:
    feature = {
        "type": "Feature",
        "id": "plan-1",
        "properties": {"plan": "HafenCity Test", "description": "Logistik"},
        "geometry": {"type": "Point", "coordinates": [566100, 5933100]},
    }

    result = normalize_feature(feature, collection_id="prosin_imverfahren")

    assert result.source_id == "plan-1"
    assert result.title == "HafenCity Test"
    assert result.published_at is None
    assert result.lifecycle == "in_procedure"
    assert result.raw_payload == feature
    assert "publication_date_not_mapped" in result.quality_notes
    assert "port_logistics" in result.classification.signal_types


def test_normalizer_surfaces_missing_fields() -> None:
    result = normalize_feature({"type": "Feature", "properties": {}, "geometry": None})

    assert result.source_id is None
    assert result.title is None
    assert result.geometry is None
    assert "missing_source_id" in result.quality_notes
    assert "missing_title" in result.quality_notes
    assert "missing_geometry" in result.quality_notes
