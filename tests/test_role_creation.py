"""Role creation always persists a UTC timestamp in the SQLite schema."""

from contextlib import closing
from datetime import datetime, timedelta
import sqlite3

import pytest

from test_creation_and_refresh import application, create_database


@pytest.mark.parametrize(
    "statement",
    [
        pytest.param(
            "INSERT INTO roles (name, permissions, is_admin) VALUES (?, 'ticket.view', 1)",
            id="omitted",
        ),
        pytest.param(
            "INSERT INTO roles (name, permissions, is_admin, date_created) "
            "VALUES (?, 'ticket.view', 1, NULL)",
            id="null",
        ),
    ],
)
def test_schema_rejects_role_without_creation_date(tmp_path, statement):
    database = create_database(tmp_path)
    with closing(sqlite3.connect(database)) as db:
        with pytest.raises(sqlite3.IntegrityError, match=r"roles\.date_created"):
            db.execute(statement, ("Role without date",))


@pytest.mark.parametrize("realm", ["admin", "user"])
def test_created_role_has_a_utc_date_and_can_be_read(application, realm):
    path = f"/admin/roles/{realm}"
    headers = application.admin_headers
    payload = {"name": "Test role with date", "permissions": ["ticket.view"]}
    created = application.api.post(path, headers=headers, json=payload)
    assert created.status_code == 201, created.text
    role = created.json()
    assert role["name"] == payload["name"]
    assert role["permissions"] == payload["permissions"]

    with closing(sqlite3.connect(application.database)) as db:
        row = db.execute(
            "SELECT date_created, is_admin FROM roles WHERE role_id = ?",
            (role["role_id"],),
        ).fetchone()
    assert row is not None
    stored_date, is_admin = row
    assert is_admin == (realm == "admin")
    saved_at = datetime.fromisoformat(stored_date)
    assert saved_at.utcoffset() == timedelta(0)
    if realm == "admin":
        assert datetime.fromisoformat(role["date_created"]) == saved_at

    fetched = application.api.get(f"{path}/{role['role_id']}", headers=headers)
    assert fetched.status_code == 200, fetched.text
    assert fetched.json() == role
