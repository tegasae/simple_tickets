"""Ordinary duplicate account input is rejected before an employee is inserted."""
import secrets
import sqlite3

import pytest


@pytest.mark.parametrize("realm", ["admins", "users"])
@pytest.mark.parametrize("spaced", [False, True], ids=["canonical", "outer-spaces"])
def test_duplicate_normalized_login_is_client_error(world, realm, spaced):
    """400 for an existing canonical login, with no partial Employee or Account."""
    payload = {
        "first_name": "Synthetic duplicate registration",
        "login": f" {world.login} " if spaced else world.login,
        "password": "Aa1!" + secrets.token_hex(12),
    }
    if realm == "users":
        payload["client_id"] = world.client_id

    def counts():
        with sqlite3.connect(world.path) as db:
            return tuple(db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                         for table in ("employees", "admins", "users", "accounts"))

    before = counts()
    response = world.api.post(f"/admin/{realm}/", headers=world.admin_headers, json=payload)
    assert counts() == before
    assert response.status_code == 400
