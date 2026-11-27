"""Replacing Account credentials through the ordinary attach route retires all old sessions."""

from contextlib import closing
from importlib.util import find_spec
import secrets
import sqlite3

import pytest

from test_shared_sessions import auth_data, saved_session, staff_member


@pytest.mark.parametrize("realm", ["admin", "user"])
def test_attach_account_to_existing_employee_retires_previous_sessions(world, realm):
    """POST account даёт 200, две старые сессии удалены, новый и посторонний вход действуют."""
    subject_id, old_login, old_password = (
        staff_member(world) if realm == "admin" else (world.user_id, world.login, world.password)
    )
    previous = [
        auth_data(world, realm, old_login, old_password)["refresh_token"]
        for _ in range(2)
    ]
    assert all(saved_session(world, token) is not None for token in previous)

    new_login = "replacement" + secrets.token_hex(8)
    new_password = "Aa1!" + secrets.token_hex(12)
    result = world.api.post(
        f"/admin/{realm}s/{subject_id}/account",
        headers=world.admin_headers,
        json={"login": new_login, "password": new_password},
    )
    assert result.status_code == 200
    assert result.json()["login"] == new_login
    assert [saved_session(world, token) is None for token in previous] == [True, True]
    assert saved_session(world, world.admin_refresh) is not None

    replacement = auth_data(world, realm, new_login, new_password)["refresh_token"]
    assert saved_session(world, replacement) is not None


@pytest.mark.skipif(
    find_spec("src.web.auth.services.shared_sessions") is None,
    reason="Shared session storage is introduced by patch 05",
)
@pytest.mark.parametrize("realm", ("admin", "user"))
def test_attach_cas_and_revocation_share_commit(world, realm):
    """500 при ошибке отзыва откатывает Account, версии и сессии, следующий POST даёт 200."""
    if realm == "admin":
        employee_id, login, password = staff_member(world)
    else:
        employee_id, login, password = world.user_id, world.login, world.password
    auth_data(world, realm, login, password)
    auth_data(world, realm, login, password)

    def state():
        with closing(sqlite3.connect(world.path)) as db:
            (version,) = db.execute("SELECT version FROM employees WHERE employee_id=?", (employee_id,)).fetchone()
            account = db.execute("SELECT account_id,login,enabled FROM accounts WHERE employee_id=?", (employee_id,)).fetchone()
            (client_version,) = db.execute("SELECT version FROM clients WHERE client_id=?", (world.client_id,)).fetchone()
            (sessions,) = db.execute(
                "SELECT COUNT(*) FROM auth_refresh_sessions WHERE subject_type=? AND subject_id=?",
                (realm, employee_id),
            ).fetchone()
            return version, account, client_version, sessions

    previous = state()
    assert previous[1][1] == login
    assert previous[3] >= 2
    new_login = "attach-review-" + secrets.token_hex(8)

    def attach():
        return world.api.post(
            f"/admin/{realm}s/{employee_id}/account",
            headers=world.admin_headers,
            json={"login": new_login, "password": "Aa1!" + secrets.token_hex(12)},
        )

    with closing(sqlite3.connect(world.path)) as db, db:
        db.execute("""CREATE TRIGGER test_stop_before_session_delete
            BEFORE DELETE ON auth_refresh_sessions BEGIN SELECT RAISE(ABORT, 'synthetic write failure'); END""")
    assert attach().status_code == 500
    assert state() == previous
    with closing(sqlite3.connect(world.path)) as db, db:
        db.execute("DROP TRIGGER test_stop_before_session_delete")
    assert attach().status_code == 200
    assert state() == (
        previous[0] + 1,
        (previous[1][0], new_login, previous[1][2]),
        previous[2] + (realm == "user"),
        0,
    )
