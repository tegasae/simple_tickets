"""Regression coverage for replaying user ticket comments."""

from contextlib import closing
import secrets
import sqlite3

from src.adapters.uow.sqlite_unit_of_work import SQLiteUnitOfWork
from src.domain.rbac.permissions import UserPermission
from src.domain.rbac.role_new import UserRole
from test_creation_and_refresh import Application, application
from utils.db.connect import Connection


def test_user_comment_replay_checks_target_and_current_permissions(application: Application):
    with closing(Connection.create_connection(str(application.database), engine=sqlite3)) as connection:
        with SQLiteUnitOfWork(connection) as uow:
            role = uow.roles_user.save(
                UserRole.create(
                    name="Ticket operator",
                    permissions=frozenset({UserPermission.TICKET_OPERATION}),
                ),
            )
            user = uow.users.get(application.user_id)
            user.grant_role(role.role_id)
            uow.users.save(user)

    api = application.api
    login = api.post(
        "/auth/user/login",
        data={"username": application.user_login, "password": application.user_password},
    )
    assert login.status_code == 200
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    ticket_a = api.post("/user/tickets/", headers=headers, json={"text_of_ticket": "Ticket A"})
    ticket_b = api.post("/user/tickets/", headers=headers, json={"text_of_ticket": "Ticket B"})
    assert ticket_a.status_code == ticket_b.status_code == 201
    ticket_a_id = ticket_a.json()["ticket_user_id"]
    ticket_b_id = ticket_b.json()["ticket_user_id"]
    assert ticket_a_id != ticket_b_id

    key = secrets.token_hex(16)
    comment_headers = {**headers, "Idempotency-Key": key}
    payload = {"comment": "One comment"}
    path_a = f"/user/tickets/{ticket_a_id}/comments"
    path_b = f"/user/tickets/{ticket_b_id}/comments"

    first = api.post(path_a, headers=comment_headers, json=payload)
    replay = api.post(path_a, headers=comment_headers, json=payload)
    conflict = api.post(path_b, headers=comment_headers, json=payload)
    assert first.status_code == replay.status_code == 200
    assert replay.content == first.content
    assert conflict.status_code == 409

    with closing(sqlite3.connect(application.database)) as db:
        with db:
            removed = db.execute(
                "DELETE FROM users_roles WHERE employee_id = ? AND role_id = ?",
                (application.user_id, role.role_id),
            )
            assert removed.rowcount == 1

    forbidden = api.post(path_a, headers=comment_headers, json={"comment": "Different comment"})
    assert forbidden.status_code == 403

    with closing(sqlite3.connect(application.database)) as db:
        assert db.execute(
            "SELECT user_ticket_id, employee_id, comment FROM user_tickets_comment",
        ).fetchall() == [(ticket_a_id, application.user_id, payload["comment"])]
        assert db.execute(
            "SELECT employee_id, idempotency_key, status_code, body FROM creation_results",
        ).fetchall() == [(application.user_id, key, 200, first.text)]
