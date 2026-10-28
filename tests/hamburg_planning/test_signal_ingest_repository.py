from sqlalchemy.dialects import postgresql

from app.database.repositories.signal_ingest_repository import SignalIngestRepository


class RecordingSession:
    def __init__(self):
        self.statements = []
        self.commits = 0

    def execute(self, statement):
        self.statements.append(statement)

    def commit(self):
        self.commits += 1


def _row(title="Test plan"):
    return {
        "source": "hamburg_bebauungsplaene",
        "source_id": "plan-1",
        "signal_type": "commercial_zone",
        "title": title,
        "published_at": None,
        "source_url": None,
        "location_text": None,
        "status": "in_procedure",
        "geometry": None,
        "raw_payload": {"id": "plan-1"},
        "quality_status": "warning",
        "quality_notes": ["publication_date_not_mapped"],
        "matched_terms": {"terms": ["gewerbe"]},
    }


def test_upsert_uses_source_identity_conflict_constraint():
    session = RecordingSession()
    repository = SignalIngestRepository(session)

    assert repository.upsert_many([_row()]) == 1

    sql = str(
        session.statements[0].compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    )
    assert "ON CONFLICT ON CONSTRAINT uq_signal_ingest_source_source_id DO UPDATE" in sql
    assert session.commits == 1


def test_rerun_uses_same_upsert_path_instead_of_blind_insert():
    session = RecordingSession()
    repository = SignalIngestRepository(session)

    repository.upsert_many([_row("First title")])
    repository.upsert_many([_row("Updated title")])

    assert len(session.statements) == 2
    for statement in session.statements:
        sql = str(statement.compile(dialect=postgresql.dialect()))
        assert "ON CONFLICT" in sql
    assert session.commits == 2


def test_empty_batch_does_not_touch_database():
    session = RecordingSession()
    repository = SignalIngestRepository(session)

    assert repository.upsert_many([]) == 0
    assert session.statements == []
    assert session.commits == 0
