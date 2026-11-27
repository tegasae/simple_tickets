"""Exercise the proposed upgrade on synthetic data in the exact prior schema."""
from contextlib import closing
from datetime import UTC, datetime
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest

from conftest import transaction
from src.domain.employee import User
from src.web.auth.storage_sqlite import TokenStorageSQLite
from src.web.auth.tokens import RefreshToken
from src.web.config import Settings

MIGRATION = Path("scripts/migrate_backend_storage.py")
pytestmark = pytest.mark.skipif(not MIGRATION.is_file(), reason="Storage migration is introduced by 05")


@pytest.fixture
def old_database(tmp_path):
    schema = os.environ.get("ACCEPTANCE_LEGACY_SCHEMA")
    if schema is None:
        pytest.skip("Set ACCEPTANCE_LEGACY_SCHEMA to the frozen 869cd42 db/schema.sql")
    path = tmp_path / "legacy-synthetic.sqlite3"
    now = datetime.now(UTC).isoformat()
    with closing(sqlite3.connect(path)) as database, database:
        database.executescript(Path(schema).read_text(encoding="utf-8"))
        database.execute("PRAGMA foreign_keys=ON")
        database.executemany(
            "INSERT INTO departments(department_id, name, version, date_created) VALUES (?, ?, ?, ?)",
            [(1, "Legacy support A", None, now), (2, "Legacy support B", 5, now), (99, "Removed", 2, now)],
        )
        database.execute("DELETE FROM departments WHERE department_id=99")
        database.executemany(
            "INSERT INTO employees(employee_id, first_name, enabled, version, is_admin, date_created) VALUES (?, ?, 1, ?, ?, ?)",
            [(1, "Legacy operator", None, 1, now), (2, "Legacy number", 7, 0, now)],
        )
        database.execute("INSERT INTO admins VALUES (1, '', 1)")
        database.executemany(
            "INSERT INTO clients(client_id, admin_id, name, enabled, version, date_created) VALUES (?, 1, ?, 1, ?, ?)",
            [(1, "Legacy organization A", None, now), (2, "Legacy organization B", 9, now)],
        )
        database.execute("INSERT INTO users VALUES(2, 1)")
    password = "Aa1!" + secrets.token_hex(12)
    name = "legacy" + secrets.token_hex(8)
    # Save a usable User via the application's repository in the old schema.
    with transaction(path) as uow:
        user = uow.users.save(User.create(first_name="Legacy requester", client_id=1, login=name, password=password))
    return path, name, password, user.employee_id


def test_migration_normalizes_versions_and_preserves_relations(old_database):
    """NULL → 0, existing integers unchanged; FK, uniqueness, CAS and sequence hold."""
    from scripts.migrate_backend_storage import migrate
    from src.adapters.repositories.exceptions import OptimisticLockError

    path, _, _, subject_id = old_database
    with closing(sqlite3.connect(path)) as db:
        db.execute("PRAGMA foreign_keys=ON")
        assert migrate(db) == {"departments": 1, "employees": 1, "clients": 1}
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        for table, identity, expected in [
            ("departments", "department_id", [(1, 0), (2, 5)]),
            ("employees", "employee_id", [(1, 0), (2, 7), (subject_id, 0)]),
            ("clients", "client_id", [(1, 0), (2, 9)]),
        ]:
            assert db.execute(f"SELECT {identity}, version FROM {table} ORDER BY {identity}").fetchall() == expected
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(f"UPDATE {table} SET version=NULL WHERE {identity}=1")
            db.rollback()
        with db:
            created = db.execute("INSERT INTO departments(name) VALUES ('New synthetic department')")
            assert created.lastrowid == 100
            assert db.execute("SELECT version FROM departments WHERE department_id=100").fetchone() == (0,)
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO departments(name) VALUES ('Legacy support A')")
        db.rollback()
        assert migrate(db) == {"departments": 0, "employees": 0, "clients": 0}
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    for repository_name, identity, version in [
        ("admins", 1, 0), ("users", 2, 7), ("departments", 1, 0), ("clients", 1, 0),
    ]:
        with transaction(path) as uow:
            repository = getattr(uow, repository_name)
            first = repository.get(identity)
            stale = repository.get(identity)
            assert first.version == stale.version == version
            repository.touch(first)
        with pytest.raises(OptimisticLockError), transaction(path) as uow:
            getattr(uow, repository_name).touch(stale)
        with transaction(path) as uow:
            assert getattr(uow, repository_name).get(identity).version == version + 1


def test_migration_rolls_back_on_fk_failure(old_database):
    """An invalid relation stops the upgrade without a partially normalized schema."""
    from scripts.migrate_backend_storage import migrate

    path, *_ = old_database
    with closing(sqlite3.connect(path)) as db:
        with db:
            db.execute("UPDATE admins SET department_id=999 WHERE employee_id=1")
        db.execute("PRAGMA foreign_keys=ON")
        with pytest.raises(ValueError, match="Foreign key validation"):
            migrate(db)
        assert db.execute("SELECT version FROM departments WHERE department_id=1").fetchone() == (None,)
        assert not db.execute("SELECT 1 FROM sqlite_schema WHERE name='auth_refresh_sessions'").fetchone()
        assert db.execute("PRAGMA foreign_keys").fetchone() == (1,)


@pytest.mark.parametrize("old_location", ["separate-file", "main-file"])
def test_upgrade_requires_login_and_never_uses_old_refresh(old_database, tmp_path, monkeypatch, old_location):
    """Old token gets 401 after upgrade; a new login creates shared valid storage."""
    path, name, password, subject = old_database
    old = path if old_location == "main-file" else tmp_path / "previous-refresh.sqlite3"
    legacy = TokenStorageSQLite(old)
    stale = RefreshToken.create(settings=Settings(), subject_id=subject, subject_type="user", username=name)
    legacy.put(stale)
    assert legacy.get(stale.token_id).is_valid()

    result = subprocess.run([sys.executable, str(MIGRATION), str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    monkeypatch.setenv("DATABASE_URL", str(path))
    monkeypatch.setenv("REFRESH_TOKEN_BACKEND", "sqlite")
    monkeypatch.setenv("REFRESH_TOKEN_SQLITE_PATH", str(old))
    from src.web.main import create_app

    with TestClient(create_app()) as api:
        retired = api.post("/auth/user/refresh", json={"refresh_token": stale.token_id})
        assert retired.status_code == 401
        new = api.post("/auth/user/login", data={"username": name, "password": password})
        assert new.status_code == 200
    with TestClient(create_app()) as another_app:
        rotated = another_app.post("/auth/user/refresh", json={"refresh_token": new.json()["refresh_token"]})
        assert rotated.status_code == 200
    with closing(sqlite3.connect(path)) as db:
        assert db.execute(
            "SELECT COUNT(*) FROM auth_refresh_sessions WHERE subject_id=?", (subject,),
        ).fetchone() == (1,)
        check = db.execute("SELECT name FROM sqlite_schema WHERE name='creation_results'").fetchone()
        # The complete series has both tables; 05 on its own has just sessions.
        if Path("src/web/idempotency.py").is_file():
            assert check == ("creation_results",)
    assert legacy.get(stale.token_id).is_valid()
