"""Test durable result constraints and read-only unique-claim fallback."""
from contextlib import closing
from importlib.util import find_spec
import os
from pathlib import Path
import sqlite3

import pytest

from test_idempotent_creations import counts, creation, expected_counts, post

pytestmark = pytest.mark.skipif(
    find_spec("src.web.idempotency") is None,
    reason="Keyed creation storage is introduced by patch 06",
)


@pytest.mark.parametrize("schema_kind", ["fresh", "migrated"])
def test_creation_results_check_requires_paired_status_and_body(tmp_path, schema_kind):
    """При свежей установке и миграции CHECK принимает полную запись и исключает частичную."""
    statement = """INSERT INTO creation_results
        (subject_type, subject_id, command, idempotency_key, fingerprint, status_code, body, expires_at)
        VALUES ('admin', ?, 'client.create', ?, 'fixture', ?, ?, ?)"""
    with closing(sqlite3.connect(tmp_path / "synthetic.sqlite3")) as db:
        schema = Path("db/schema.sql") if schema_kind == "fresh" else Path(os.environ["ACCEPTANCE_LEGACY_SCHEMA"])
        db.executescript(schema.read_text())
        if schema_kind == "migrated":
            from scripts.migrate_backend_storage import migrate

            migrate(db)
        for entry in [
            ("pending", None, None, None),
            ("done", 201, "{}", None),
            ("done-marked", 201, "{}", 1000.0),
        ]:
            db.execute(statement, (1, *entry))
        for entry in [
            ("only-body", None, "{}", None),
            ("only-code", 201, None, None),
            ("only-expiry", None, None, 1000.0),
            ("body-with-expiry", None, "{}", 1000.0),
            ("error-code", 409, "{}", None),
        ]:
            with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
                db.execute(statement, (1, *entry))
        assert db.execute("SELECT COUNT(*) FROM creation_results").fetchone() == (3,)


@pytest.mark.parametrize(("visible_on_reread", "expected_status"), [(True, 201), (False, 503)])
def test_unique_claim_fallback_reads_committed_result_once(world, monkeypatch, visible_on_reread, expected_status):
    """После реального UNIQUE происходит одно новое чтение. Ответ 201 с исходным ID либо 503."""
    from src.adapters.repositories.creation_result_repository import CreationResultRepositorySQLite
    from utils.db.connect import Connection

    command = creation(world, "department")
    before_counts = counts(world, command)
    key = "claim-reread"
    initial = post(world, command, key)
    assert initial.status_code == 201
    calls = []
    boundary = []
    original_get = CreationResultRepositorySQLite.get
    original_connection = Connection.create_connection

    def trace(statement):
        if statement in ("COMMIT", "ROLLBACK"):
            boundary.append(statement)

    def connected(cls, *args, **kwargs):
        connection = original_connection(*args, **kwargs)
        connection.connect.set_trace_callback(trace)
        return connection

    def miss_initial_get(repository, result_key):
        result = original_get(repository, result_key)
        calls.append(result_key.key)
        assert result is not None
        if len(calls) == 1 or not visible_on_reread:
            return None
        return result

    monkeypatch.setattr(Connection, "create_connection", classmethod(connected))
    monkeypatch.setattr(CreationResultRepositorySQLite, "get", miss_initial_get)
    retry = post(world, command, key)
    assert retry.status_code == expected_status
    if visible_on_reread:
        assert retry.json()["department_id"] == initial.json()["department_id"]
    assert calls == [key, key]
    assert "ROLLBACK" in boundary
    assert counts(world, command) == expected_counts(before_counts, command)
