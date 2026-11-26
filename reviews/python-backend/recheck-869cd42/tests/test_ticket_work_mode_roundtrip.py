"""Preserve the distinction between an absent mode and on-site work."""
from contextlib import closing
import sqlite3

import pytest


def modes(response):
    return {record["status"]: record["work_is_remote"] for record in response["statuses"]}


@pytest.mark.parametrize("work_is_remote", [False, True])
def test_ticket_work_mode_round_trip(world, work_is_remote):
    """Поле без режима остаётся null, событие работы сохраняет true или false после повторного GET."""
    created = world.api.post(
        "/admin/tickets/",
        headers=world.admin_headers,
        json={
            "client_id": world.client_id,
            "department_id": world.department_id,
            "text_of_ticket": "Work mode round trip",
        },
    )
    assert created.status_code == 201
    ticket_id = created.json()["ticket_id"]
    initial_modes = {"created": None, "accepted": None}
    assert modes(created.json()) == initial_modes
    read = world.api.get(f"/admin/tickets/{ticket_id}", headers=world.admin_headers)
    assert read.status_code == 200
    assert modes(read.json()) == initial_modes

    world.action(ticket_id, "executor", {"executor_id": world.admin_id})
    started = world.action(ticket_id, "start-work", {"work_is_remote": work_is_remote})
    expected = {**initial_modes, "assigned": None, "at_work": work_is_remote}
    assert modes(started) == expected
    assert modes(started)["at_work"] is work_is_remote
    read = world.api.get(f"/admin/tickets/{ticket_id}", headers=world.admin_headers)
    assert read.status_code == 200
    assert modes(read.json()) == expected
    assert modes(read.json())["at_work"] is work_is_remote

    with closing(sqlite3.connect(world.path)) as database:
        rows = database.execute(
            "SELECT status, work_is_remote FROM ticket_status_records WHERE ticket_id=?",
            (ticket_id,),
        ).fetchall()
    assert dict(rows) == {**initial_modes, "assigned": None, "at_work": int(work_is_remote)}


def test_legacy_null_for_required_mode_still_reloads(world):
    """Старый AT_WORK с NULL читается как false, GET успешен."""
    ticket_id, _ = world.pair(finish=True)
    with closing(sqlite3.connect(world.path)) as database, database:
        changed = database.execute(
            "UPDATE ticket_status_records SET work_is_remote=NULL WHERE ticket_id=? AND status=?",
            (ticket_id, "at_work"),
        )
        assert changed.rowcount == 1

    read = world.api.get(f"/admin/tickets/{ticket_id}", headers=world.admin_headers)
    assert read.status_code == 200
    assert modes(read.json())["at_work"] is False
    assert read.json()["statuses"][-1]["status"] == "ready_for_review"
