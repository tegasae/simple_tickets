"""Exercise the SQLite commit boundary using ordinary keyed creations."""
from contextlib import closing
from importlib.util import find_spec
import sqlite3

import pytest

from test_idempotent_creations import counts, creation, expected_counts, post

pytestmark = pytest.mark.skipif(
    find_spec("src.web.idempotency") is None,
    reason="Keyed creation storage is introduced by patch 06",
)


def test_later_keyed_success_marks_pending_result_for_full_window(world, monkeypatch):
    """Восстановление другим ключом помечает ранее зафиксированный результат на полные 24 часа."""
    from src.web import idempotency

    client = creation(world, "client")
    department = creation(world, "department")
    now = [100000.0]
    monkeypatch.setattr(idempotency, "timestamp", lambda: now[0])

    with monkeypatch.context() as patch:
        # Leave the same durable state as stopping after the business COMMIT.
        patch.setattr(idempotency, "_maintain", lambda *args: None)
        initial = post(world, client, "older-command")
    assert initial.status_code == 201

    statement = "SELECT expires_at FROM creation_results WHERE idempotency_key=?"
    with closing(sqlite3.connect(world.path)) as database:
        assert database.execute(statement, ("older-command",)).fetchone() == (None,)
        now[0] += 86400 * 3
        assert post(world, department, "different-command").status_code == 201

        deadline = now[0] + 86400
        assert database.execute(statement, ("older-command",)).fetchone() == (deadline,)
        now[0] = deadline - 1
        replay = post(world, client, "older-command")
        assert replay.status_code == 201
        assert replay.json()["client_id"] == initial.json()["client_id"]
        assert database.execute(statement, ("older-command",)).fetchone() == (deadline,)

        now[0] = deadline
        expired = post(world, client, "older-command")
        assert expired.status_code == 201
        assert expired.json()["client_id"] != initial.json()["client_id"]


def test_sqlite_busy_at_commit_rolls_back_business_data_and_key(world, monkeypatch):
    """SQLite отказывает на COMMIT с 503, ключ и Client откатываются. Новая команда даёт один Client."""
    from utils.db.connect import Connection

    command = creation(world, "client")
    before = counts(world, command)
    transaction_events = []
    create_connection = Connection.create_connection

    def record_boundary(statement):
        if statement in ("COMMIT", "ROLLBACK"):
            transaction_events.append(statement)

    def short_timeout_connection(cls, *args, **kwargs):
        connection = create_connection(*args, **kwargs)
        connection.connect.execute("PRAGMA busy_timeout=25")
        connection.connect.set_trace_callback(record_boundary)
        return connection

    monkeypatch.setattr(Connection, "create_connection", classmethod(short_timeout_connection))
    with closing(sqlite3.connect(world.path)) as reader:
        assert reader.execute("PRAGMA journal_mode").fetchone() == ("delete",)
        reader.execute("BEGIN")
        reader.execute("SELECT COUNT(*) FROM clients").fetchone()

        response = post(world, command, "busy-at-commit")
        assert response.status_code == 503
        assert transaction_events[-2:] == ["COMMIT", "ROLLBACK"]

        reader.rollback()
        assert reader.execute("SELECT COUNT(*) FROM creation_results").fetchone() == (0,)

    assert counts(world, command) == before
    assert post(world, command, "busy-at-commit").status_code == 201
    assert counts(world, command) == expected_counts(before, command)
