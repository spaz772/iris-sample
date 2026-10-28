from app.integrations.hamburg_planning.normalizer import normalize_feature
from app.integrations.hamburg_planning.staging import to_staging_row


def test_staging_row_preserves_identity_and_quality_notes():
    feature = {
        "type": "Feature",
        "id": "plan-1",
        "properties": {"plan": "HafenCity 1", "description": "Logistik Terminal"},
        "geometry": {"type": "Point", "coordinates": [565000, 5934000]},
    }

    row = to_staging_row(
        normalize_feature(
            feature,
            collection_id="app:prosin_imverfahren",
            source_crs="EPSG:25832",
        )
    )

    assert row["source"] == "hamburg_bebauungsplaene"
    assert row["source_id"] == "plan-1"
    assert row["signal_type"] == "port_logistics"
    assert row["status"] == "in_procedure"
    assert row["published_at"] is None
    assert "publication_date_not_mapped" in row["quality_notes"]
    assert row["geometry"] is not None


def test_staging_row_rejects_record_without_stable_identity():
    feature = {
        "type": "Feature",
        "properties": {},
        "geometry": None,
    }
    plan = normalize_feature(feature)

    try:
        to_staging_row(plan)
    except ValueError as exc:
        assert "source_id" in str(exc)
    else:
        raise AssertionError("missing source identity must not be silently staged")
