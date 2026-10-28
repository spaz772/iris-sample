from app.integrations.hamburg_planning.service import HamburgPlanningService


class FakeClient:
    def iter_features(self, collection_id, *, limit=100, max_pages=None):
        assert collection_id == "bplaene_imverfahren"
        yield {
            "type": "Feature",
            "id": "plan-1",
            "properties": {"plan": "Hafen Logistik Plan"},
            "geometry": {"type": "Point", "coordinates": [565000, 5935000]},
        }
        yield {
            "type": "Feature",
            "properties": {"title": "Feature without stable id"},
            "geometry": None,
        }


class FakeRepository:
    def __init__(self):
        self.rows = []

    def upsert_many(self, records):
        rows = list(records)
        self.rows.extend(rows)
        return len(rows)


def test_service_normalizes_classifies_skips_missing_identity_and_writes():
    repository = FakeRepository()
    service = HamburgPlanningService(
        session=object(),
        client=FakeClient(),
        repository=repository,
    )

    report = service.run(["bplaene_imverfahren"])

    assert report.collections == 1
    assert report.features_seen == 2
    assert report.rows_written == 1
    assert report.skipped_missing_id == 1
    assert report.classified == 1
    assert report.unclassified == 1
    assert repository.rows[0]["source_id"] == "plan-1"
    assert repository.rows[0]["signal_type"] == "port_logistics"
    assert repository.rows[0]["status"] == "in_procedure"
