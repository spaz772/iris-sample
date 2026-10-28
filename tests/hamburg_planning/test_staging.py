from app.integrations.hamburg_planning.normalizer import normalize_feature
from app.integrations.hamburg_planning.staging import to_staging_row


def test_staging_row_preserves_identity_and_quality_notes():
    feature = {
        "type": "Feature",
        "id": 0,
        "properties": {
            "plan": "HafenCity 1",
            "description": "Logistik Terminal",
            "feststellung": "nein",
            "hotlink_iv": "https://www.hamburg.de/example-plan/",
        },
        "geometry": {"type": "Point", "coordinates": [10.0, 53.55]},
    }

    row = to_staging_row(
        normalize_feature(
            feature,
            collection_id="prosin_imverfahren",
        )
    )

    assert row["source"] == "hamburg_bebauungsplaene"
    assert row["source_id"] == "HafenCity 1"
    assert row["signal_type"] == "port_logistics"
    assert row["status"] == "in_procedure"
    assert row["published_at"] is None
    assert row["source_url"] == "https://www.hamburg.de/example-plan/"
    assert "publication_date_not_available_in_verified_feature" in row["quality_notes"]
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
