"""Role boundary between cancellation and physical deletion of tickets."""

from contextlib import closing
import secrets
import sqlite3

import pytest

from test_creation_and_refresh import Application, application


def admin_headers_with_permission(app: Application, permission: str) -> dict[str, str]:
    role = app.api.post(
        "/admin/roles/admin",
        headers=app.admin_headers,
        json={"name": f"Role {permission}", "permissions": [permission]},
    )
    assert role.status_code == 201, role.text
    assert role.json()["permissions"] == [permission]

    login = "operator" + secrets.token_hex(5)
    password = "Aa1!" + secrets.token_hex(12)
    admin = app.api.post(
        "/admin/admins/",
        headers=app.admin_headers,
        json={
            "first_name": "Test operator",
            "roles": [role.json()["role_id"]],
            "login": login,
            "password": password,
        },
    )
    assert admin.status_code == 201, admin.text
    auth = app.api.post("/auth/admin/login", data={"username": login, "password": password})
    assert auth.status_code == 200
    return {"Authorization": "Bearer " + auth.json()["access_token"]}


def create_linked_ticket(app: Application) -> tuple[int, int]:
    user = app.api.get(f"/admin/users/{app.user_id}", headers=app.admin_headers)
    assert user.status_code == 200, user.text
    ticket = app.api.post(
        "/admin/tickets/",
        headers=app.admin_headers,
        json={
            "client_id": user.json()["client_id"],
            "user_id": app.user_id,
            "contact_user_id": app.user_id,
            "text_of_ticket": "Test linked ticket",
            "comment": "Original comment",
        },
    )
    assert ticket.status_code == 201, ticket.text
    created = ticket.json()
    assert created["statuses"][-1]["status"] == "accepted"
    return created["ticket_id"], created["user_ticket_id"]


def persisted_ticket_records(app: Application, ticket_id: int, user_ticket_id: int) -> dict[str, list[tuple]]:
    tables = (
        ("tickets", "ticket_id", ticket_id),
        ("user_tickets", "user_ticket_id", user_ticket_id),
        ("ticket_status_records", "ticket_id", ticket_id),
        ("user_tickets_status_record", "user_ticket_id", user_ticket_id),
        ("ticket_comments", "ticket_id", ticket_id),
        ("user_tickets_comment", "user_ticket_id", user_ticket_id),
    )
    with closing(sqlite3.connect(app.database)) as db:
        return {
            table: db.execute(f"SELECT * FROM {table} WHERE {column} = ? ORDER BY 1", (identifier,)).fetchall()
            for table, column, identifier in tables
        }


def test_cancel_permission_preserves_ticket_and_does_not_grant_deletion(application: Application):
    headers = admin_headers_with_permission(application, "ticket.canceled")
    ticket_id, user_ticket_id = create_linked_ticket(application)
    path = f"/admin/tickets/{ticket_id}"
    previous = persisted_ticket_records(application, ticket_id, user_ticket_id)
    assert all(previous.values())

    denied = application.api.delete(path, headers=headers)
    assert denied.status_code == 403, denied.text
    assert persisted_ticket_records(application, ticket_id, user_ticket_id) == previous

    cancelled = application.api.patch(f"{path}/cancel", headers=headers, json={"comment": "Test cancellation"})
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["statuses"][-1]["status"] == "cancelled"
    current = persisted_ticket_records(application, ticket_id, user_ticket_id)
    for table in ("ticket_status_records", "user_tickets_status_record"):
        assert current[table][:-1] == previous[table]
    for table in ("ticket_comments", "user_tickets_comment"):
        assert current[table] == previous[table]

    denied = application.api.delete(path, headers=headers)
    assert denied.status_code == 403, denied.text
    assert persisted_ticket_records(application, ticket_id, user_ticket_id) == current


@pytest.mark.parametrize("cancel_first", [False, True], ids=["active", "terminal"])
def test_delete_permission_removes_both_tickets_and_histories(application: Application, cancel_first: bool):
    permissions = application.api.get("/admin/roles/admin/permissions", headers=application.admin_headers)
    assert permissions.status_code == 200, permissions.text
    assert "ticket.delete" in permissions.json()
    headers = admin_headers_with_permission(application, "ticket.delete")
    ticket_id, user_ticket_id = create_linked_ticket(application)
    path = f"/admin/tickets/{ticket_id}"
    cancellation = {"comment": "Test cancellation"}

    denied = application.api.patch(f"{path}/cancel", headers=headers, json=cancellation)
    assert denied.status_code == 403, denied.text
    if cancel_first:
        cancelled = application.api.patch(f"{path}/cancel", headers=application.admin_headers, json=cancellation)
        assert cancelled.status_code == 200, cancelled.text
        assert cancelled.json()["is_closed"] is True

    assert all(persisted_ticket_records(application, ticket_id, user_ticket_id).values())
    deleted = application.api.delete(path, headers=headers)
    assert deleted.status_code == 204, deleted.text
    assert deleted.content == b""
    assert not any(persisted_ticket_records(application, ticket_id, user_ticket_id).values())
