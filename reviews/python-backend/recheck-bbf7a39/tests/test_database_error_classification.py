"""Distinguish rejected transactions, unique constraints and unknown failures."""
import sqlite3

import pytest

from conftest import database_uow
from utils.db.connect import Connection


def no_busy_wait(monkeypatch):
    """Use actual SQLite errors without a five-second wait in each request."""
    original = Connection.create_connection.__func__

    def connect(cls, *args, **kwargs):
        connection = original(cls, *args, **kwargs)
        connection.connect.execute("PRAGMA busy_timeout=0")
        return connection

    monkeypatch.setattr(Connection, "create_connection", classmethod(connect))


@pytest.mark.parametrize("resource", ["departments", "roles/admin", "users"])
def test_locked_insert_returns_temporary_error_without_duplicate_or_partial_data(
    world, monkeypatch, resource,
):
    no_busy_wait(monkeypatch)
    payload = {"name": "Synthetic blocked department"}
    if resource == "roles/admin":
        payload = {"name": "Synthetic blocked role", "permissions": ["admin.view"]}
    elif resource == "users":
        payload = {"first_name": "Synthetic blocked requester", "client_id": world.client_id}
    with sqlite3.connect(world.path) as holder:
        holder.execute("BEGIN IMMEDIATE")
        try:
            response = world.client.post(
                f"/admin/{resource}/" if resource != "roles/admin" else "/admin/roles/admin",
                headers=world.admin_headers, json=payload,
            )
        finally:
            holder.rollback()
    assert response.status_code == 503
    assert response.json() == {"detail": "Database temporarily unavailable"}
    # A new HTTP command with fresh reads succeeds after releasing the lock.
    repeated = world.client.post(
        f"/admin/{resource}/" if resource != "roles/admin" else "/admin/roles/admin",
        headers=world.admin_headers, json=payload,
    )
    assert repeated.status_code == 201


def test_commit_lock_is_rolled_back_before_503_and_new_request_can_succeed(world, monkeypatch):
    no_busy_wait(monkeypatch)
    name = "Synthetic commit lock"
    with sqlite3.connect(world.path) as reader:
        reader.execute("BEGIN")
        reader.execute("SELECT name FROM departments").fetchall()
        try:
            response = world.client.post(
                "/admin/departments/", headers=world.admin_headers, json={"name": name},
            )
        finally:
            reader.rollback()
    assert response.status_code == 503
    with database_uow(world.path) as uow:
        assert uow.connection.connect.execute(
            "SELECT COUNT(*) FROM departments WHERE name = ?", (name,),
        ).fetchone()[0] == 0
    repeated = world.client.post(
        "/admin/departments/", headers=world.admin_headers, json={"name": name},
    )
    assert repeated.status_code == 201


def test_duplicate_department_is_still_conflict(world):
    response = world.client.post(
        "/admin/departments/", headers=world.admin_headers, json={"name": "Synthetic support"},
    )
    assert response.status_code == 409


def test_unknown_department_failure_is_not_reported_as_duplicate(world):
    # Fault injection is confined to a synthetic database. The shipped schema
    # has no such trigger; this verifies preservation of an unknown failure.
    with database_uow(world.path) as uow:
        uow.connection.connect.execute(
            "CREATE TRIGGER synthetic_department_failure BEFORE INSERT ON departments "
            "BEGIN SELECT RAISE(ABORT, 'Synthetic unexpected failure'); END"
        )
    response = world.client.post(
        "/admin/departments/", headers=world.admin_headers, json={"name": "Synthetic failed department"},
    )
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
