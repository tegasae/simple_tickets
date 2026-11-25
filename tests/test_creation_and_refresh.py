"""Regression checks through FastAPI on an isolated SQLite database."""

from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
import secrets
import sqlite3

from fastapi.testclient import TestClient
import pytest

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role_new import Role
from utils.db.connect import Connection


SCHEMA = Path(__file__).resolve().parents[1] / "db" / "schema.sql"


@dataclass(frozen=True)
class Application:
    api: TestClient
    database: Path
    user_id: int
    admin_headers: dict[str, str] = field(repr=False)
    user_login: str = field(repr=False)
    user_password: str = field(repr=False)
    user_refresh: str = field(repr=False)


@pytest.fixture
def application(tmp_path, monkeypatch):
    database = tmp_path / "test.sqlite3"
    with closing(sqlite3.connect(database)) as db:
        db.executescript(SCHEMA.read_text(encoding="utf-8"))

    admin_login = "operator" + secrets.token_hex(5)
    user_login = "requester" + secrets.token_hex(5)
    admin_password = "Aa1!" + secrets.token_hex(12)
    user_password = "Aa1!" + secrets.token_hex(12)
    with closing(Connection.create_connection(str(database), engine=sqlite3)) as connection:
        with SQLiteUnitOfWork(connection) as uow:
            admin_role = uow.roles_admin.save(
                Role.create(name="Test operator role", permissions=set(AdminPermission)),
            )
            admin = Admin.create(
                first_name="Test operator", login=admin_login, password=admin_password,
            )
            admin.grant_role(admin_role.role_id)
            admin = uow.admins.save(admin)
            client = uow.clients.save(
                Client.create(name="Test client", created_by_admin_id=admin.employee_id),
            )
            user = uow.users.save(
                User.create(
                    first_name="Test requester",
                    client_id=client.client_id,
                    login=user_login,
                    password=user_password,
                ),
            )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", str(database))
    monkeypatch.setenv("SECRET_KEY", secrets.token_hex(32))
    from src.web.main import create_app

    with TestClient(create_app(), raise_server_exceptions=False) as api:
        admin_auth = api.post(
            "/auth/admin/login", data={"username": admin_login, "password": admin_password},
        )
        user_auth = api.post(
            "/auth/user/login", data={"username": user_login, "password": user_password},
        )
        assert admin_auth.status_code == user_auth.status_code == 200
        yield Application(
            api=api,
            database=database,
            user_id=user.employee_id,
            admin_headers={"Authorization": "Bearer " + admin_auth.json()["access_token"]},
            user_login=user_login,
            user_password=user_password,
            user_refresh=user_auth.json()["refresh_token"],
        )


def test_one_employee_key_cannot_create_two_types_of_role(application):
    api = application.api
    key = secrets.token_hex(16)
    headers = {**application.admin_headers, "Idempotency-Key": key}
    body = {"name": "Test new role", "permissions": ["ticket.view"]}

    first = api.post("/admin/roles/admin", headers=headers, json=body)
    conflict = api.post("/admin/roles/user", headers=headers, json=body)
    replay = api.post("/admin/roles/admin", headers=headers, json=body)

    assert first.status_code == replay.status_code == 201
    assert replay.content == first.content
    assert conflict.status_code == 409
    with closing(sqlite3.connect(application.database)) as db:
        assert db.execute(
            "SELECT is_admin FROM roles WHERE name=?", (body["name"],),
        ).fetchall() == [(1,)]
        assert db.execute("SELECT count(*) FROM creation_results").fetchone() == (1,)

    fresh_headers = {**application.admin_headers, "Idempotency-Key": secrets.token_hex(16)}
    second = api.post("/admin/roles/user", headers=fresh_headers, json=body)
    assert second.status_code == 201
    assert second.json()["role_id"] != first.json()["role_id"]
    with closing(sqlite3.connect(application.database)) as db:
        assert db.execute(
            "SELECT is_admin FROM roles WHERE name=? ORDER BY is_admin", (body["name"],),
        ).fetchall() == [(0,), (1,)]


def test_password_change_and_refresh_revoke_share_one_commit(application):
    api = application.api
    path = f"/admin/users/{application.user_id}/password"
    new_password = "Aa1!" + secrets.token_hex(12)
    body = {"password": new_password}
    with closing(sqlite3.connect(application.database)) as db:
        db.execute("""CREATE TRIGGER simulated_revoke_failure
                      BEFORE DELETE ON auth_refresh_sessions
                      BEGIN SELECT RAISE(ABORT, 'Synthetic revoke failure'); END""")

    rejected = api.patch(path, headers=application.admin_headers, json=body)
    assert rejected.status_code == 500
    with closing(sqlite3.connect(application.database)) as db:
        db.execute("DROP TRIGGER simulated_revoke_failure")

    still_valid = api.post(
        "/auth/user/refresh", json={"refresh_token": application.user_refresh},
    )
    assert still_valid.status_code == 200
    old_login = api.post(
        "/auth/user/login",
        data={"username": application.user_login, "password": application.user_password},
    )
    assert old_login.status_code == 200

    changed = api.patch(path, headers=application.admin_headers, json=body)
    assert changed.status_code == 200
    for previous in (still_valid, old_login):
        revoked = api.post(
            "/auth/user/refresh", json={"refresh_token": previous.json()["refresh_token"]},
        )
        assert revoked.status_code == 401
    new_login = api.post(
        "/auth/user/login", data={"username": application.user_login, "password": new_password},
    )
    assert new_login.status_code == 200


def test_replay_starts_expiry_for_result_left_pending(application, monkeypatch):
    from src.web import idempotency

    now = 100_000.0
    monkeypatch.setattr(idempotency, "timestamp", lambda: now)
    api = application.api
    path = "/admin/roles/admin"
    body = {"name": "Test confirmed role", "permissions": ["ticket.view"]}
    confirmed_headers = {**application.admin_headers, "Idempotency-Key": secrets.token_hex(16)}
    confirmed = api.post(path, headers=confirmed_headers, json=body)
    assert confirmed.status_code == 201

    pending_key = secrets.token_hex(16)
    pending_headers = {**application.admin_headers, "Idempotency-Key": pending_key}
    pending_body = {**body, "name": "Test pending role"}
    with monkeypatch.context() as stopped_after_commit:
        stopped_after_commit.setattr(idempotency, "_maintain", lambda uow: None)
        pending = api.post(path, headers=pending_headers, json=pending_body)
    assert pending.status_code == 201

    query = "SELECT expires_at FROM creation_results WHERE idempotency_key=?"
    with closing(sqlite3.connect(application.database)) as db:
        assert db.execute(query, (pending_key,)).fetchone() == (None,)

    now += 60
    assert api.post(path, headers=confirmed_headers, json=body).content == confirmed.content

    with closing(sqlite3.connect(application.database)) as db:
        assert db.execute(query, (pending_key,)).fetchone() == (now + 86_400,)
        assert db.execute(
            query, (confirmed_headers["Idempotency-Key"],),
        ).fetchone() == (100_000 + 86_400,)


@pytest.mark.parametrize("has_results", [False, True])
def test_migration_from_pre_activation_key_table(tmp_path, has_results):
    from scripts.migrate_backend_storage import LEGACY_CREATION_RESULTS, migrate

    with closing(sqlite3.connect(tmp_path / "pre-activation.sqlite3")) as db:
        db.executescript(SCHEMA.read_text(encoding="utf-8"))
        db.execute("DROP TABLE creation_results")
        db.execute(LEGACY_CREATION_RESULTS)
        if has_results:
            with db:
                db.execute(
                    """INSERT INTO creation_results
                       (subject_type, subject_id, command, idempotency_key, fingerprint, status_code, body)
                       VALUES ('admin', 1, 'role.admin.create', 'legacy-key', 'test-fingerprint', 201, '{}')""",
                )
            with pytest.raises(ValueError, match="populated legacy creation_results"):
                migrate(db)
            assert db.execute(
                "SELECT subject_id, idempotency_key FROM creation_results",
            ).fetchall() == [(1, "legacy-key")]
        else:
            assert migrate(db) == {"departments": 0, "employees": 0, "clients": 0}
            columns = db.execute("PRAGMA table_info(creation_results)").fetchall()
            assert [(row[1], row[5]) for row in columns if row[5]] == [
                ("employee_id", 1), ("idempotency_key", 2),
            ]
