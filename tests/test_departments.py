"""Creation of departments with explicit or default activation state."""

from contextlib import closing
import sqlite3
from uuid import uuid4

import pytest

from test_creation_and_refresh import Application, application


@pytest.mark.parametrize(
    ("enabled_fields", "expected"),
    [({"enabled": False}, False), ({"enabled": True}, True), ({}, True)],
    ids=["disabled", "enabled", "default"],
)
def test_create_department_preserves_enabled(
    application: Application, enabled_fields: dict[str, bool], expected: bool,
):
    response = application.api.post(
        "/admin/departments/",
        headers=application.admin_headers,
        json={"name": "Test support department", **enabled_fields},
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["enabled"] is expected

    read = application.api.get(
        f"/admin/departments/{created['department_id']}",
        headers=application.admin_headers,
    )
    assert read.status_code == 200, read.text
    assert read.json()["enabled"] is expected


def test_create_disabled_department_is_idempotent(application: Application):
    headers = {**application.admin_headers, "Idempotency-Key": uuid4().hex}
    body = {"name": "Test disabled department", "enabled": False}

    created = application.api.post("/admin/departments/", headers=headers, json=body)
    replay = application.api.post("/admin/departments/", headers=headers, json=body)

    assert created.status_code == replay.status_code == 201
    assert created.json()["enabled"] is False
    assert replay.content == created.content
    with closing(sqlite3.connect(application.database)) as db:
        rows = db.execute(
            "SELECT department_id, enabled FROM departments WHERE name = ?", (body["name"],),
        ).fetchall()
    assert rows == [(created.json()["department_id"], 0)]
