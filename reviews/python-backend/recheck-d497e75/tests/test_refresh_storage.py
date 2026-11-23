import sqlite3

import pytest
from fastapi.testclient import TestClient

from old_review_tests.conftest import sample  # noqa: F401
from src.web.auth.services.services import TokenService
from src.web.auth.storage import TokenStorageMemory
from src.web.auth.tokens import JWTToken
from src.web.config import Settings


def test_new_app_instances_share_refresh_storage(sample, tmp_path, monkeypatch):
    from src.web.main import create_app

    path = tmp_path / "refresh.sqlite3"
    monkeypatch.setenv("REFRESH_TOKEN_BACKEND", "sqlite")
    monkeypatch.setenv("REFRESH_TOKEN_SQLITE_PATH", str(path))
    first, second = create_app(), create_app()
    for app in (first, second):
        app.state.settings.DATABASE_URL = str(sample.path)
    with TestClient(first) as client:
        login = client.post("/auth/user/login", data={
            "username": sample.user_login, "password": sample.user_password,
        })
    assert login.status_code == 200
    old = login.json()["refresh_token"]
    assert path.is_file()
    with sqlite3.connect(path) as db:
        record_hash, payload = db.execute("SELECT token_hash, payload FROM refresh_sessions").fetchone()
        assert len(record_hash) == 64
        if old in payload:
            pytest.fail("SQLite recorded a raw refresh token")
    with TestClient(second) as client:
        refresh = client.post("/auth/user/refresh", json={"refresh_token": old})
        assert refresh.status_code == 200
        logout = client.post("/auth/user/logout", json={
            "refresh_token": refresh.json()["refresh_token"],
        })
        assert logout.status_code == 200
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT count(*) FROM refresh_sessions").fetchone() == (0,)


def test_failed_encoding_keeps_previous_session_in_memory(monkeypatch):
    store = TokenStorageMemory()
    service = TokenService(token_storage=store, settings=Settings())
    old = service.create_token_pair(
        subject_id=1, subject_type="user", username="fixture",
    )["refresh_token"]

    def fail_encoding(self, *, settings):
        raise ValueError("Synthetic encoding failure")

    monkeypatch.setattr(JWTToken, "encode", fail_encoding)
    with pytest.raises(ValueError, match="Synthetic encoding failure"):
        service.renew_tokens(old)
    assert store.get(old).is_valid()


def test_sqlite_rotation_rolls_back_if_insert_fails(tmp_path, monkeypatch):
    from src.web.auth.storage_sqlite import TokenStorageSQLite

    path = tmp_path / "refresh.sqlite3"
    service = TokenService(token_storage=TokenStorageSQLite(path), settings=Settings())
    old = service.create_token_pair(
        subject_id=1, subject_type="user", username="fixture",
    )["refresh_token"]

    def fail_insert(db, token):
        raise sqlite3.OperationalError("Synthetic insertion failure")

    monkeypatch.setattr(service.token_storage, "_insert", fail_insert)
    with pytest.raises(sqlite3.OperationalError, match="Synthetic insertion failure"):
        service.renew_tokens(old)
    reopened = TokenStorageSQLite(path)
    assert reopened.count() == 1
    assert reopened.get(old).is_valid()


def test_memory_stores_belong_to_their_app_instance():
    first, second = TokenStorageMemory(), TokenStorageMemory()
    first.clear()
    second.clear()
    service = TokenService(token_storage=first, settings=Settings())
    service.create_token_pair(subject_id=1, subject_type="user", username="fixture")
    assert first.count() == 1
    assert second.count() == 0
