"""Refresh lifecycle acceptance through the real Admin and User APIs."""
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from importlib.util import find_spec
import secrets
import sqlite3
from threading import Event

from fastapi.testclient import TestClient
import pytest

from conftest import transaction
from test_lifetime import refresh
from src.web.auth.exceptions import TokenNotFoundError
from src.web.auth.tokens import hash_token


def shared_sessions_available():
    return find_spec("src.adapters.repositories.refresh_session_repository") is not None


def saved_session(world, token):
    storage = getattr(world.api.app.state, "refresh_token_storage", None)
    if storage is not None:
        try:
            return storage.get(token)
        except TokenNotFoundError:
            return None
    with transaction(world.path) as uow:
        return uow.refresh_sessions.get(hash_token(token))


def session_count(world):
    storage = getattr(world.api.app.state, "refresh_token_storage", None)
    if storage is not None:
        return storage.count()
    with sqlite3.connect(world.path) as connection:
        return connection.execute("SELECT count(*) FROM auth_refresh_sessions").fetchone()[0]


def login(world, realm, name, password):
    return world.api.post(f"/auth/{realm}/login", data={"username": name, "password": password})


def auth_data(world, realm, name, password):
    result = login(world, realm, name, password)
    assert result.status_code == 200
    return result.json()


def staff_member(world):
    login_name = "target" + secrets.token_hex(8)
    password = "Aa1!" + secrets.token_hex(12)
    result = world.api.post("/admin/admins/", headers=world.admin_headers, json={
        "first_name": "Synthetic team member", "login": login_name, "password": password,
    })
    assert result.status_code == 201
    return result.json()["employee_id"], login_name, password


def related_member(world):
    login_name = "member" + secrets.token_hex(8)
    password = "Aa1!" + secrets.token_hex(12)
    result = world.api.post("/admin/users/", headers=world.admin_headers, json={
        "first_name": "Synthetic client member", "login": login_name,
        "password": password, "client_id": world.client_id,
    })
    assert result.status_code == 201
    return result.json()["employee_id"], login_name, password


def account_id(world, realm, subject_id):
    with transaction(world.path) as uow:
        repository = uow.admins if realm == "admin" else uow.users
        return repository.get(subject_id).account.account_id


@pytest.mark.parametrize("realm", ["admin", "user"])
@pytest.mark.parametrize("event", ["password", "employee-enable", "account-enable", "replacement", "delete"])
def test_mutation_permanently_revokes_all_refresh(world, realm, event):
    """Successful mutation permanently rejects every old refresh with 401."""
    subject, name, password = (
        staff_member(world) if realm == "admin" else (world.user_id, world.login, world.password)
    )
    tokens = [auth_data(world, realm, name, password)["refresh_token"] for _ in range(2)]
    url = f"/admin/{realm}s/{subject}"
    headers = world.admin_headers
    original_account = account_id(world, realm, subject)
    assert original_account > 0
    assert all(saved_session(world, token) for token in tokens)
    if event == "password":
        previous, password = password, "Aa1!" + secrets.token_hex(12)
        changed = world.api.patch(url + "/password", headers=headers, json={"password": password})
        assert changed.status_code == 200
        assert login(world, realm, name, previous).status_code == 401
    elif event.endswith("-enable"):
        segment = "/account" if event == "account-enable" else ""
        assert world.api.patch(url + segment + "/disable", headers=headers).status_code == 200
        assert refresh(world, tokens[0], realm).status_code == 401
        assert world.api.patch(url + segment + "/enable", headers=headers).status_code == 200
    elif event == "replacement":
        assert world.api.delete(url + "/account", headers=headers).status_code == 200
        assert world.api.post(url + "/account", headers=headers, json={
            "login": name, "password": password,
        }).status_code == 200
        assert account_id(world, realm, subject) != original_account
    else:
        assert world.api.delete(url, headers=headers).status_code == 204
        with sqlite3.connect(world.path) as db:
            assert db.execute("SELECT 1 FROM accounts WHERE account_id=?", (original_account,)).fetchone() is None
        assert login(world, realm, name, password).status_code == 401

    statuses = [refresh(world, token, realm).status_code for token in tokens]
    assert statuses == [401, 401]
    assert all(saved_session(world, token) is None for token in tokens)
    if event != "delete":
        new_token = auth_data(world, realm, name, password)["refresh_token"]
        item = saved_session(world, new_token)
        assert item.account_id == account_id(world, realm, subject)
    assert refresh(world, world.admin_refresh, "admin").status_code == 200


def test_client_cascade_revokes_sessions_and_preserves_ticket_history(world):
    """Disable Client closes review pair and revokes that Client's refresh sessions."""
    internal_id, external_id = world.pair(finish=True)
    other_user, name, password = related_member(world)
    other_refresh = auth_data(world, "user", name, password)["refresh_token"]
    root = f"/admin/clients/{world.client_id}"
    assert world.api.patch(root + "/disable", headers=world.admin_headers).status_code == 200
    with transaction(world.path) as uow:
        assert not uow.clients.get(world.client_id).enabled
        assert not uow.users.get(world.user_id).enabled
        assert not uow.users.get(other_user).enabled
        assert uow.tickets.get(internal_id).current_status() == "suspended"
        assert uow.user_tickets.get(external_id).current_status() == "suspended"
    assert world.api.patch(root + "/enable", headers=world.admin_headers).status_code == 200
    for subject in (world.user_id, other_user):
        assert world.api.patch(f"/admin/users/{subject}/enable", headers=world.admin_headers).status_code == 200
    assert [refresh(world, token).status_code for token in (world.refresh, other_refresh)] == [401, 401]
    assert saved_session(world, world.refresh) is saved_session(world, other_refresh) is None
    assert refresh(world, world.admin_refresh, "admin").status_code == 200


def test_logout_realm_and_single_session_scope(world):
    """Logout only removes the selected session; wrong realm 401 leaves it usable."""
    other = auth_data(world, "user", world.login, world.password)["refresh_token"]
    wrong = world.api.post("/auth/admin/logout", json={"refresh_token": other})
    assert wrong.status_code == 401
    assert saved_session(world, other)
    response = world.api.post("/auth/user/logout", json={"refresh_token": world.refresh})
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}
    assert saved_session(world, world.refresh) is None
    assert refresh(world, world.refresh).status_code == 401
    assert refresh(world, other).status_code == 200


def test_username_logout_revokes_own_sessions(world):
    """Bearer plus current username revokes only that subject, across app instances."""
    second = auth_data(world, "user", world.login, world.password)["refresh_token"]
    from src.web.main import create_app
    with TestClient(create_app(), raise_server_exceptions=False) as api:
        response = api.post("/auth/user/logout", json={"username": world.login}, headers=world.user_headers)
    assert response.status_code == 200
    assert refresh(world, world.refresh).status_code == 401
    assert refresh(world, second).status_code == 401
    assert refresh(world, world.admin_refresh, "admin").status_code == 200


def test_fresh_app_uses_the_same_durable_session(world):
    """A separate create_app() reads the committed refresh and rotates it once."""
    from src.web.main import create_app
    with TestClient(create_app()) as api:
        result = api.post("/auth/user/refresh", json={"refresh_token": world.refresh})
    assert result.status_code == 200
    assert saved_session(world, world.refresh) is None
    assert saved_session(world, result.json()["refresh_token"])


@pytest.mark.skipif(not shared_sessions_available(), reason="Shared session repository is introduced by 05")
@pytest.mark.parametrize("event", ["password", "client-cascade"])
def test_revoke_write_failure_rolls_back_everything(world, monkeypatch, event):
    """Injected failure after DELETE leaves password, sessions and pair unchanged."""
    from src.adapters.repositories.refresh_session_repository import RefreshSessionRepositorySQLite
    from src.application.assemblers.assembler import ClientAssembler

    before_count = session_count(world)
    token = saved_session(world, world.refresh)
    if event == "client-cascade":
        internal_id, external_id = world.pair(finish=True)
    revoke = RefreshSessionRepositorySQLite.revoke_subject

    def revoke_then_fail(self, **kwargs):
        revoke(self, **kwargs)
        raise RuntimeError("Synthetic error after session removal")

    new_password = "Aa1!" + secrets.token_hex(12)
    with monkeypatch.context() as patch:
        if event == "password":
            patch.setattr(RefreshSessionRepositorySQLite, "revoke_subject", revoke_then_fail)
            response = world.api.patch(f"/admin/users/{world.user_id}/password",
                                       headers=world.admin_headers, json={"password": new_password})
        else:
            def fail_assembly(*args, **kwargs):
                raise RuntimeError("Synthetic error after saving cascade")
            patch.setattr(ClientAssembler, "to_dto", fail_assembly)
            response = world.api.patch(f"/admin/clients/{world.client_id}/disable", headers=world.admin_headers)
        assert response.status_code == 500
    assert session_count(world) == before_count
    assert saved_session(world, world.refresh) == token
    with transaction(world.path) as uow:
        user = uow.users.get(world.user_id)
        assert user.enabled and uow.clients.get(world.client_id).enabled
        assert user.account.verify_password(world.password)
        assert not user.account.verify_password(new_password)
        if event == "client-cascade":
            assert uow.tickets.get(internal_id).current_status() == "ready_for_review"
            assert uow.user_tickets.get(external_id).current_status() == "waiting_for_confirmation"
    assert refresh(world, world.refresh).status_code == 200


@pytest.mark.skipif(not shared_sessions_available(), reason="Shared session repository is introduced by 05")
def test_rotation_insert_failure_rolls_back_guard_and_credentials(world, monkeypatch):
    """A failed successor INSERT leaves old hash and employee version intact."""
    from src.adapters.repositories.refresh_session_repository import RefreshSessionRepositorySQLite
    insert = RefreshSessionRepositorySQLite.add
    metadata = saved_session(world, world.refresh)
    before_count = session_count(world)
    with transaction(world.path) as uow:
        version = uow.users.get(world.user_id).version

    def insert_then_fail(self, *args, **kwargs):
        insert(self, *args, **kwargs)
        raise RuntimeError("Synthetic error after creating successor session")

    with monkeypatch.context() as patch:
        patch.setattr(RefreshSessionRepositorySQLite, "add", insert_then_fail)
        assert refresh(world, world.refresh).status_code == 500
    assert saved_session(world, world.refresh) == metadata
    assert session_count(world) == before_count
    with transaction(world.path) as uow:
        assert uow.users.get(world.user_id).version == version
    assert refresh(world, world.refresh).status_code == 200


@pytest.mark.skipif(not shared_sessions_available(), reason="Transaction guard is introduced by 05")
@pytest.mark.parametrize("attempt", ["login", "refresh"])
def test_password_change_orders_against_session_publication(world, monkeypatch, attempt):
    """A credential request paused before its guard cannot publish after revocation."""
    from src.adapters.repositories.user_repository import UserRepositorySQLite
    with sqlite3.connect(world.path) as db:
        assert db.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    entered, resume = Event(), Event()
    original = UserRepositorySQLite.touch
    new_password = "Aa1!" + secrets.token_hex(12)

    def paused_guard(self, user):
        if user.employee_id == world.user_id and not entered.is_set():
            entered.set()
            assert resume.wait(10)
        return original(self, user)

    monkeypatch.setattr(UserRepositorySQLite, "touch", paused_guard)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(
            login, world, "user", world.login, world.password,
        ) if attempt == "login" else pool.submit(refresh, world, world.refresh)
        try:
            assert entered.wait(10)
            changed = world.api.patch(f"/admin/users/{world.user_id}/password",
                                      headers=world.admin_headers, json={"password": new_password})
            assert changed.status_code == 200
        finally:
            resume.set()
        assert pending.result(timeout=10).status_code == 503
    assert saved_session(world, world.refresh) is None
    assert login(world, "user", world.login, world.password).status_code == 401
    assert auth_data(world, "user", world.login, new_password)
