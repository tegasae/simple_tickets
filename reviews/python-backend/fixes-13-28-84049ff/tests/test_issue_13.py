"""Role creation timestamps in fresh SQLite databases."""

from contextlib import closing
from datetime import datetime, timedelta
import sqlite3

import pytest


@pytest.mark.parametrize("is_admin", [True, False], ids=["admin", "user"])
@pytest.mark.parametrize("explicit_null", [True, False], ids=["null", "omitted"])
def test_schema_rejects_role_without_creation_date(world, is_admin, explicit_null):
    name = "Synthetic role missing date"
    if explicit_null:
        statement = """
            INSERT INTO roles (name, permissions, is_admin, date_created)
            VALUES (?, 'ticket.view', ?, NULL)
        """
    else:
        statement = """
            INSERT INTO roles (name, permissions, is_admin)
            VALUES (?, 'ticket.view', ?)
        """

    with closing(sqlite3.connect(world.path)) as db:
        with pytest.raises(sqlite3.IntegrityError, match=r"roles\.date_created"):
            db.execute(statement, (name, is_admin))
        assert db.execute("SELECT role_id FROM roles WHERE name = ?", (name,)).fetchone() is None


@pytest.mark.parametrize("role_type", ["admin", "user"])
def test_api_creates_role_with_utc_date_and_lists_it(world, role_type):
    path = f"/admin/roles/{role_type}"
    created = world.api.post(
        path,
        headers=world.admin_headers,
        json={"name": "Synthetic role with date", "permissions": ["ticket.view"]},
    )
    assert created.status_code == 201, created.text
    role = created.json()

    with closing(sqlite3.connect(world.path)) as db:
        row = db.execute(
            "SELECT date_created, is_admin FROM roles WHERE role_id = ?", (role["role_id"],)
        ).fetchone()
        assert row is not None
        date_created, is_admin = row
        assert is_admin == (role_type == "admin")
        saved_date = datetime.fromisoformat(date_created)
        assert saved_date.utcoffset() == timedelta(0)
        if role_type == "admin":
            assert datetime.fromisoformat(role["date_created"]) == saved_date

    listed = world.api.get(path, headers=world.admin_headers)
    assert listed.status_code == 200, listed.text
    assert role in listed.json()
