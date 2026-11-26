"""Controlled SQLite WAL ordering of cascade and session publication."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from importlib.util import find_spec
import sqlite3
from threading import Event

import pytest

from conftest import transaction
from src.adapters.repositories.user_repository import UserRepositorySQLite
from test_shared_sessions import login, saved_session, shared_sessions_available


pytestmark = pytest.mark.skipif(
    not shared_sessions_available(), reason="Shared session guard is introduced by 05",
)


@pytest.mark.parametrize("attempt", ["login", "refresh"])
@pytest.mark.parametrize("first_success", ["disable", "session"])
def test_client_disable_and_session_publication_use_one_ordinary_commit(world, monkeypatch, attempt, first_success):
    """Один из двух COMMIT, другой HTTP 503, после отключения пара и сессии закрыты."""
    inner, outer = world.pair(finish=True)
    with closing(sqlite3.connect(world.path)) as database:
        assert database.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    reached, proceed = Event(), Event()

    def disable():
        return world.api.patch(f"/admin/clients/{world.client_id}/disable", headers=world.admin_headers)

    def user_session():
        if attempt == "login":
            return login(world, "user", world.login, world.password)
        return world.api.post("/auth/user/refresh", json={"refresh_token": world.refresh})

    method = "touch" if first_success == "disable" else "save"
    original = getattr(UserRepositorySQLite, method)

    def wait_for_other_commit(repository, user):
        if user.employee_id == world.user_id and not reached.is_set():
            reached.set()
            assert proceed.wait(10)
        return original(repository, user)

    monkeypatch.setattr(UserRepositorySQLite, method, wait_for_other_commit)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(user_session if first_success == "disable" else disable)
        try:
            assert reached.wait(10)
            first = disable() if first_success == "disable" else user_session()
            assert first.status_code == 200
        finally:
            proceed.set()
        assert pending.result(timeout=10).status_code == 503

    if first_success == "session":
        token = first.json()["refresh_token"]
        assert saved_session(world, token)
        with transaction(world.path) as uow:
            assert uow.clients.get(world.client_id).enabled
            assert uow.tickets.get(inner).current_status() == "ready_for_review"
            assert uow.user_tickets.get(outer).current_status() == "waiting_for_confirmation"
        assert disable().status_code == 200
        assert saved_session(world, token) is None
    with transaction(world.path) as uow:
        assert not uow.clients.get(world.client_id).enabled
        assert uow.tickets.get(inner).current_status() == "suspended"
        assert uow.user_tickets.get(outer).current_status() == "suspended"
        assert uow.connection.connect.execute(
            "SELECT count(*) FROM auth_refresh_sessions WHERE subject_type='user' AND subject_id=?",
            (world.user_id,),
        ).fetchone() == (0,)
    assert saved_session(world, world.admin_refresh)
