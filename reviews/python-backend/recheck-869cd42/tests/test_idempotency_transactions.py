"""Test state after rollback, transport failure, expiry and concurrent POST."""
from concurrent.futures import ThreadPoolExecutor
from importlib.util import find_spec
import secrets
import sqlite3
from threading import Event

from fastapi.testclient import TestClient
import pytest

from test_idempotent_creations import CASES, counts, creation, expected_counts, post

pytestmark = pytest.mark.skipif(
    find_spec("src.web.idempotency") is None, reason="Idempotency storage and hook are introduced by 06",
)


def stored_results(world):
    with sqlite3.connect(world.path) as connection:
        return connection.execute(
            "SELECT status_code, expires_at FROM creation_results ORDER BY subject_id, idempotency_key"
        ).fetchall()


@pytest.mark.parametrize("case", CASES)
def test_failure_after_result_write_rolls_back_key_and_business_rows(world, case, monkeypatch):
    """500 after saving result rolls back any entity, history and key before retry."""
    from src.adapters.repositories.creation_result_repository import CreationResultRepositorySQLite
    command = creation(world, case)
    before = counts(world, command)
    key = secrets.token_hex(16)
    complete = CreationResultRepositorySQLite.complete

    def write_then_fail(repository, *args, **kwargs):
        complete(repository, *args, **kwargs)
        raise RuntimeError("Synthetic result write failure")

    with monkeypatch.context() as patch:
        patch.setattr(CreationResultRepositorySQLite, "complete", write_then_fail)
        assert post(world, command, key).status_code == 500
    assert counts(world, command) == before
    assert stored_results(world) == []
    assert post(world, command, key).status_code == command.success
    assert counts(world, command) == expected_counts(before, command)


def test_failure_to_prepare_http_response_rolls_back_pair(world, monkeypatch):
    """Failure constructing the response DTO leaves no pair or key."""
    from src.web.models.tikcets_user import TicketUserResponse
    command = creation(world, "user_ticket")
    before = counts(world, command)
    key = secrets.token_hex(16)

    def invalid_response(*args, **kwargs):
        raise RuntimeError("Synthetic API serialization failure")

    with monkeypatch.context() as patch:
        patch.setattr(TicketUserResponse, "from_dto", invalid_response)
        assert post(world, command, key).status_code == 500
    assert counts(world, command) == before
    assert stored_results(world) == []
    assert post(world, command, key).status_code == 201


def test_business_rejection_leaves_key_available(world):
    """A rejected domain command can be corrected with the same unused key."""
    from test_idempotent_creations import Creation
    command = creation(world, "department")
    assert post(world, command).status_code == 201
    key = secrets.token_hex(16)
    before = counts(world, command)
    assert post(world, command, key).status_code == 409
    assert counts(world, command) == before
    assert stored_results(world) == []
    corrected = Creation(
        command.path, command.headers, {"name": command.payload["name"] + " corrected"},
        command.effects, command.identity,
    )
    fixed = post(world, corrected, key)
    assert fixed.status_code == 201
    assert post(world, corrected, key).json() == fixed.json()
    assert counts(world, command) == expected_counts(before, command)


def test_lost_response_is_replayed_after_commit(world):
    """If response delivery breaks, stored status/body survive and avoid a new pair."""
    command = creation(world, "user_ticket")
    before = counts(world, command)
    key = secrets.token_hex(16)
    headers = {**command.headers, "Idempotency-Key": key}

    async def interrupted(scope, receive, send):
        async def disconnect_on_success(message):
            if message["type"] == "http.response.start" and message["status"] == 201:
                raise ConnectionError("Synthetic response delivery interruption")
            await send(message)
        await world.api.app(scope, receive, disconnect_on_success)

    with TestClient(interrupted) as api, pytest.raises(ConnectionError):
        api.post(command.path, headers=headers, json=command.payload)
    assert counts(world, command) == expected_counts(before, command)
    assert stored_results(world)[0][0] == 201
    retried = post(world, command, key)
    assert retried.status_code == 201
    with sqlite3.connect(world.path) as db:
        saved = db.execute("SELECT body FROM creation_results").fetchone()[0]
    assert saved == retried.text
    assert counts(world, command) == expected_counts(before, command)


def test_deadline_is_set_after_commit_and_key_can_be_reused_at_expiry(world, monkeypatch):
    """Replay until 24h after commit, then ordinary creation with the same key."""
    from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
    from src.web import idempotency
    now = [100000.0]
    monkeypatch.setattr(idempotency, "timestamp", lambda: now[0])
    original_commit = SQLiteUnitOfWork.commit
    delayed = []

    def advance_for_business_commit(uow):
        pending = uow.connection.connect.execute(
            "SELECT 1 FROM creation_results WHERE status_code=201 AND expires_at IS NULL"
        ).fetchone()
        if pending and not delayed:
            now[0] += 10
            delayed.append(True)
        return original_commit(uow)

    monkeypatch.setattr(SQLiteUnitOfWork, "commit", advance_for_business_commit)
    command = creation(world, "user_ticket")
    key = secrets.token_hex(16)
    first = post(world, command, key)
    assert first.status_code == 201 and delayed
    deadline = now[0] + 86400
    assert stored_results(world) == [(201, deadline)]
    now[0] = deadline - 1
    assert post(world, command, key).json() == first.json()
    now[0] = deadline
    new = post(world, command, key)
    assert new.status_code == 201
    assert new.json()["ticket_user_id"] != first.json()["ticket_user_id"]
    assert stored_results(world) == [(201, deadline + 86400)]


def test_deadline_maintenance_failure_does_not_lose_success(world, monkeypatch):
    """Committed result survives failed expiry maintenance and is repaired on replay."""
    from src.adapters.repositories.creation_result_repository import CreationResultRepositorySQLite
    from utils.db.exceptions import DBTransientError
    command = creation(world, "user_ticket")
    key = secrets.token_hex(16)

    def busy(*args, **kwargs):
        raise DBTransientError("Synthetic busy during maintenance")

    with monkeypatch.context() as patch:
        patch.setattr(CreationResultRepositorySQLite, "pending_deadlines", busy)
        first = post(world, command, key)
    assert first.status_code == 201
    assert stored_results(world) == [(201, None)]
    assert post(world, command, key).json() == first.json()
    assert stored_results(world)[0][1] is not None


def test_concurrent_replay_returns_one_effect_with_standard_sqlite_busy(world, monkeypatch):
    """503 during actual contention, then client replay returns durable 201."""
    from src.adapters.repositories.creation_result_repository import CreationResultRepositorySQLite
    from utils.db.connect import Connection

    with sqlite3.connect(world.path) as db:
        assert db.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    connect = Connection.create_connection
    complete = CreationResultRepositorySQLite.complete
    entered, release = Event(), Event()

    def short_test_connection(cls, *args, **kwargs):
        connection = connect(*args, **kwargs)
        connection.connect.execute("PRAGMA busy_timeout=25")
        return connection

    def pause_after_writing(repository, *args, **kwargs):
        complete(repository, *args, **kwargs)
        entered.set()
        assert release.wait(10)

    monkeypatch.setattr(Connection, "create_connection", classmethod(short_test_connection))
    monkeypatch.setattr(CreationResultRepositorySQLite, "complete", pause_after_writing)
    command = creation(world, "user_ticket")
    before = counts(world, command)
    key = secrets.token_hex(16)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(post, world, command, key)
        try:
            assert entered.wait(10)
            busy = post(world, command, key)
            assert busy.status_code == 503
        finally:
            release.set()
        response = first.result(timeout=10)
    assert response.status_code == 201
    assert post(world, command, key).json() == response.json()
    assert counts(world, command) == expected_counts(before, command)
    assert len(stored_results(world)) == 1


def test_busy_maintenance_sql_leaves_durable_creation(world, monkeypatch):
    """Ошибка SQL при выставлении TTL оставляет сохранённый ответ доступным."""
    from utils.db.exceptions import DBTransientError
    from utils.db.query import Query

    command = creation(world, "client")
    before = counts(world, command)
    execute_query = Query._execute
    maintenance_attempts = []

    def execute_with_busy_maintenance(query, params=None):
        statement = " ".join(query.sql.split()).lower()
        if statement.startswith("update creation_results set expires_at"):
            maintenance_attempts.append(True)
            raise DBTransientError("Synthetic lock during deadline update")
        return execute_query(query, params)

    with monkeypatch.context() as patch:
        patch.setattr(Query, "_execute", execute_with_busy_maintenance)
        created = post(world, command, "maintenance-busy")
    assert maintenance_attempts == [True]
    assert created.status_code == 201
    assert stored_results(world) == [(201, None)]

    replay = post(world, command, "maintenance-busy")
    assert replay.status_code == 201
    assert replay.text == created.text
    [(status, deadline)] = stored_results(world)
    assert status == 201
    assert deadline is not None
    assert counts(world, command) == expected_counts(before, command)
