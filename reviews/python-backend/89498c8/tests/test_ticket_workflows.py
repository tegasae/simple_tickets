import sqlite3
from pathlib import Path

import pytest

from src.domain.ticket import Ticket
from src.domain.ticket_components import TicketUrgency


def create_internal(web, sample, **details):
    response = web.post("/admin/tickets/", json={
        "client_id": sample.client_id,
        "text_of_ticket": "Review synthetic request",
        **details,
    })
    assert response.status_code == 201, response.text
    return response.json()


def create_from_user(web, **details):
    response = web.post("/user/tickets/", json={
        "text_of_ticket": "Review synthetic request",
        **details,
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_delete_standalone_ticket(web, sample, uow):
    created = create_internal(web, sample)
    ticket_id = created["ticket_id"]
    response = web.delete(f"/admin/tickets/{ticket_id}")
    assert response.status_code == 204, response.text
    with uow:
        assert uow.tickets.get_all() == []


def test_delete_linked_ticket_and_history(web, sample, uow):
    created = create_internal(web, sample, user_id=sample.user_id, comment="Synthetic note")
    response = web.delete(f"/admin/tickets/{created['ticket_id']}")
    assert response.status_code == 204, response.text
    with uow:
        assert uow.tickets.get_all() == []
        assert uow.user_tickets.get_all() == []


def test_user_create_persists_selected_contact_in_both_tickets(web, sample, uow):
    created = create_from_user(web, contact_user_id=sample.contact_id)
    with uow:
        internal = uow.tickets.get_by_user_ticket_id(created["ticket_user_id"])
    assert (created["contact_user_id"], internal.contact_user_id) == (
        sample.contact_id, sample.contact_id,
    )


@pytest.mark.parametrize("auto_accept", [False, True])
def test_admin_create_persists_selected_contact_in_both_tickets(web, sample, uow, auto_accept):
    if not auto_accept:
        with sqlite3.connect(sample.path) as db:
            role_id, permissions = db.execute(
                "SELECT role_id, permissions FROM roles WHERE is_admin=1",
            ).fetchone()
            allowed = [permission for permission in permissions.split(",")
                       if permission != "ticket.accepted"]
            db.execute("UPDATE roles SET permissions=? WHERE role_id=?",
                       (",".join(allowed), role_id))
    internal = create_internal(web, sample, user_id=sample.user_id, contact_user_id=sample.contact_id)
    with uow:
        linked = uow.user_tickets.get(internal["user_ticket_id"])
    assert (internal["contact_user_id"], linked.contact_user_id) == (
        sample.contact_id, sample.contact_id,
    )


def test_user_changes_and_resets_contact_in_both_tickets(web, sample, uow):
    created = create_from_user(web)
    ticket_user_id = created["ticket_user_id"]
    route = f"/user/tickets/{ticket_user_id}/contact-user"
    for requested, expected in [(sample.contact_id, sample.contact_id), (0, sample.user_id)]:
        response = web.patch(route, json={"contact_user_id": requested})
        assert response.status_code == 200, response.text
        assert response.json()["contact_user_id"] == expected
        with uow:
            assert uow.tickets.get_by_user_ticket_id(ticket_user_id).contact_user_id == expected
            assert uow.user_tickets.get(ticket_user_id).contact_user_id == expected


def test_batch_loads_full_projection_in_normal_column_order(sample, uow):
    with uow:
        ticket = uow.tickets.save(Ticket.create(
            client_id=sample.client_id, admin_id=sample.admin_id,
            text_of_ticket="One synthetic ticket", description="A nonempty description",
            urgency=TicketUrgency.NORMAL,
        ))
        for tickets in (
            uow.tickets.iter_get_all(batch_size=1),
            uow.tickets.iter_by_client_id(client_id=sample.client_id, batch_size=1),
        ):
            loaded, = tickets
            assert (loaded.ticket_id, loaded.description.value, loaded.urgency) == (
                ticket.ticket_id, "A nonempty description", TicketUrgency.NORMAL,
            )


def test_closed_for_client_returns_only_closed_tickets(sample, uow):
    with uow:
        for closed in (False, True):
            ticket = Ticket.create(
                client_id=sample.client_id, admin_id=sample.admin_id,
                text_of_ticket=f"Synthetic closed={closed}",
            )
            if closed:
                ticket.reject(actor_employee_id=sample.admin_id, comment="Synthetic reason")
            uow.tickets.save(ticket)
        found, = uow.tickets.get_finished(client_id=sample.client_id)
        assert found.is_closed


def test_schema_initializes_empty_sqlite(tmp_path):
    with sqlite3.connect(tmp_path / "empty.sqlite3") as db:
        db.executescript(Path("db/schema.sql").read_text())
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)


def test_user_comment_survives_reload(web):
    created = create_from_user(web, comment="Initial synthetic comment")
    route = f"/user/tickets/{created['ticket_user_id']}"
    response = web.get(route)
    assert response.status_code == 200, response.text
    assert [record["comment"] for record in response.json()["comments"]] == [
        "Initial synthetic comment",
    ]
    added = web.post(f"{route}/comments", json={"comment": "Follow-up synthetic comment"})
    assert added.status_code in (200, 201), added.text
    assert [record["comment"] for record in web.get(route).json()["comments"]] == [
        "Initial synthetic comment", "Follow-up synthetic comment",
    ]


def test_admin_user_account_updates_commit_in_both_directions(web, sample):
    for action, expected_enabled in [("disable", False), ("enable", True)]:
        if expected_enabled:
            with sqlite3.connect(sample.path) as db:
                db.execute("UPDATE accounts SET enabled=0 WHERE employee_id=?", (sample.user_id,))
        response = web.patch(f"/admin/users/{sample.user_id}/account/{action}")
        assert response.status_code == 200, response.text
        assert response.json()["enabled_login"] is expected_enabled
        with sqlite3.connect(sample.path) as db:
            assert db.execute(
                "SELECT enabled FROM accounts WHERE employee_id=?", (sample.user_id,),
            ).fetchone() == (int(expected_enabled),)


def work_ticket(web, sample, *, finish=False):
    ticket = create_internal(
        web, sample, user_id=sample.user_id, department_id=sample.department_id,
    )
    route = f"/admin/tickets/{ticket['ticket_id']}"
    for action, body in (
        ("executor", {"executor_id": sample.admin_id}),
        ("start-work", {"work_is_remote": False}),
    ):
        response = web.patch(f"{route}/{action}", json=body)
        assert response.status_code == 200, response.text
    if finish:
        response = web.patch(f"{route}/finish-work", json={})
        assert response.status_code == 200, response.text
    return ticket


def test_client_disable_preserves_in_progress_and_review_pairs(web, sample, uow):
    active = work_ticket(web, sample)
    under_review = work_ticket(web, sample, finish=True)
    can_suspend = create_from_user(web)
    route = f"/admin/clients/{sample.client_id}/disable"
    for _ in range(2):
        response = web.patch(route)
        assert response.status_code == 200, response.text
    enabled = web.patch(f"/admin/clients/{sample.client_id}/enable")
    assert enabled.status_code == 200, enabled.text
    response = web.patch(route)
    assert response.status_code == 200, response.text
    with uow:
        assert not uow.clients.get(sample.client_id).enabled
        assert not uow.users.get(sample.user_id).enabled
        assert uow.tickets.get(active["ticket_id"]).current_status() == "at_work"
        assert uow.user_tickets.get(active["user_ticket_id"]).current_status() == "in_work"
        assert uow.tickets.get(under_review["ticket_id"]).current_status() == "ready_for_review"
        assert uow.user_tickets.get(under_review["user_ticket_id"]).current_status() == "waiting_for_confirmation"
        linked_id = can_suspend["ticket_user_id"]
        assert uow.tickets.get_by_user_ticket_id(linked_id).current_status() == "suspended"
        assert uow.user_tickets.get(linked_id).current_status() == "suspended"


def test_user_disable_keeps_review_and_saves_linked_suspension(web, sample, uow):
    under_review = work_ticket(web, sample, finish=True)
    can_suspend = create_from_user(web)
    response = web.patch(f"/admin/users/{sample.user_id}/disable")
    assert response.status_code == 200, response.text
    with uow:
        assert not uow.users.get(sample.user_id).enabled
        assert uow.tickets.get(under_review["ticket_id"]).current_status() == "ready_for_review"
        linked_id = can_suspend["ticket_user_id"]
        assert uow.tickets.get_by_user_ticket_id(linked_id).current_status() == "suspended"
        assert uow.user_tickets.get(linked_id).current_status() == "suspended"


def test_ordinary_remote_assignment_in_own_department(web, sample):
    ticket = create_internal(web, sample, department_id=sample.department_id,
                             remote_work_recommended=True)
    response = web.patch(f"/admin/tickets/{ticket['ticket_id']}/start-remote-work", json={})
    assert response.status_code == 200, response.text
    assert response.json()["current_executor_id"] == sample.admin_id


def test_invalid_urgency_is_rejected_by_http_model(web, sample):
    response = web.post("/admin/tickets/", json={
        "client_id": sample.client_id,
        "text_of_ticket": "Invalid urgency fixture",
        "urgency": "unsupported",
    })
    assert response.status_code == 422


def test_future_date_with_offset_is_normalized_for_scheduling(web, sample):
    from datetime import UTC, datetime, timedelta, timezone

    ticket = create_internal(web, sample)
    planned = datetime.now(timezone(timedelta(hours=3))) + timedelta(days=2)
    response = web.patch(
        f"/admin/tickets/{ticket['ticket_id']}/schedule",
        json={"planned_at": planned.isoformat()},
    )
    assert response.status_code == 200, response.text
    assert datetime.fromisoformat(response.json()["planned_at"]) == planned.astimezone(UTC)


def test_retroactive_work_accepts_explicit_offset(web, sample):
    from datetime import datetime, timedelta, timezone

    ticket = create_internal(web, sample, department_id=sample.department_id)
    route = f"/admin/tickets/{ticket['ticket_id']}"
    assert web.patch(f"{route}/executor", json={"executor_id": sample.admin_id}).status_code == 200
    ended = datetime.now(timezone(timedelta(hours=3))) - timedelta(hours=1)
    response = web.patch(f"{route}/complete-work-retroactively", json={
        "actual_started_at": (ended - timedelta(minutes=23)).isoformat(),
        "actual_finished_at": ended.isoformat(),
    })
    assert response.status_code == 200, response.text
    assert response.json()["statuses"][-1]["status"] == "ready_for_review"


def test_read_legacy_null_duration_as_unspecified(web, sample, uow):
    ticket = create_internal(web, sample)
    with sqlite3.connect(sample.path) as db:
        db.execute("UPDATE ticket_status_records SET duration=NULL WHERE ticket_id=?",
                   (ticket["ticket_id"],))
    with uow:
        reloaded = uow.tickets.get(ticket["ticket_id"])
        assert reloaded.current_status_record().duration.total_seconds() == 0


def test_closed_user_tickets_filter_uses_client_id(web, sample, uow):
    open_ticket = create_from_user(web)
    closed_ticket = create_from_user(web)
    response = web.patch(f"/user/tickets/{closed_ticket['ticket_user_id']}/cancel", json={})
    assert response.status_code == 200, response.text
    with uow:
        actual = [ticket.ticket_user_id for ticket in
                  uow.user_tickets.get_finished_by_client_id(sample.client_id)]
    assert actual == [closed_ticket["ticket_user_id"]]
    assert open_ticket["ticket_user_id"] not in actual


def test_user_lists_fetch_only_scoped_roots(web, monkeypatch):
    from src.adapters.repositories.ticket_user_repository import TicketUserRepositorySQLite

    create_from_user(web)
    unscoped_calls = 0
    original = TicketUserRepositorySQLite.get_all

    def count_load_all(self):
        nonlocal unscoped_calls
        unscoped_calls += 1
        return original(self)

    monkeypatch.setattr(TicketUserRepositorySQLite, "get_all", count_load_all)
    assert len(web.get("/user/tickets/open").json()) == 1
    assert web.get("/user/tickets/closed").json() == []
    assert unscoped_calls == 0


def test_work_completion_can_be_confirmed_and_reloaded(web, sample, uow):
    created = work_ticket(web, sample, finish=True)
    linked_id = created["user_ticket_id"]
    response = web.patch(f"/user/tickets/{linked_id}/confirm", json={"comment": "Synthetic approval"})
    assert response.status_code == 200, response.text
    with uow:
        internal = uow.tickets.get(created["ticket_id"])
        external = uow.user_tickets.get(linked_id)
        assert internal.current_status() == external.current_status() == "confirmed_by_user"
        assert internal.current_status_record().comment.value == "Synthetic approval"
        assert external.current_status_record().comment.value == "Synthetic approval"


def test_admin_can_clear_contact_on_standalone_ticket(web, sample, uow):
    ticket = create_internal(web, sample, contact_user_id=sample.contact_id)
    response = web.patch(f"/admin/tickets/{ticket['ticket_id']}/contact-user",
                         json={"contact_user_id": 0})
    assert response.status_code == 200, response.text
    assert response.json()["contact_user_id"] == 0
    with uow:
        assert uow.tickets.get(ticket["ticket_id"]).contact_user_id == 0


def test_user_can_cancel_a_fresh_ticket_with_selected_contact(web, sample, uow):
    ticket = create_from_user(web, contact_user_id=sample.contact_id)
    linked_id = ticket["ticket_user_id"]
    result = web.patch(f"/user/tickets/{linked_id}/cancel", json={"comment": "Synthetic cancel"})
    assert result.status_code == 200, result.text
    with uow:
        internal = uow.tickets.get_by_user_ticket_id(linked_id)
        external = uow.user_tickets.get(linked_id)
        assert internal.current_status() == external.current_status() == "cancelled_by_user"
        assert internal.contact_user_id == external.contact_user_id == sample.contact_id
