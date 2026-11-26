import sqlite3

import pytest

from src.domain.client import Client

from old_review_tests.conftest import sample, uow, web  # noqa: F401
from old_review_tests.test_ticket_workflows import create_from_user, create_internal, work_ticket


def test_disable_client_obeys_confirmed_review_policy(web, sample, uow):
    active = work_ticket(web, sample)
    awaiting_review = work_ticket(web, sample, finish=True)
    request = create_from_user(web)
    with uow:
        other_client = uow.clients.save(
            Client.create(name="Second synthetic client", created_by_admin_id=sample.admin_id),
        )
    unrelated = create_internal(web, sample, client_id=other_client.client_id)
    assert web.patch(f"/admin/clients/{sample.client_id}/disable").status_code == 200
    with uow:
        assert not uow.clients.get(sample.client_id).enabled
        assert not uow.users.get(sample.user_id).enabled
        assert uow.clients.get(other_client.client_id).enabled
        assert uow.tickets.get(unrelated["ticket_id"]).current_status() == "accepted"
        finished = uow.user_tickets.get_finished_by_client_id(sample.client_id)
        assert {item.ticket_user_id for item in finished} == {
            awaiting_review["user_ticket_id"], request["ticket_user_id"],
        }
        active_external = uow.user_tickets.get(active["user_ticket_id"])
        assert uow.tickets.get(active["ticket_id"]).current_status() == "at_work"
        assert active_external.current_status() == "in_work"
        assert not active_external.is_closed
        for user_ticket_id in (awaiting_review["user_ticket_id"], request["ticket_user_id"]):
            internal = uow.tickets.get_by_user_ticket_id(user_ticket_id)
            external = uow.user_tickets.get(user_ticket_id)
            assert internal.current_status() == external.current_status() == "suspended"
            assert internal.is_closed and external.is_closed
    finished = web.patch(f"/admin/tickets/{active['ticket_id']}/finish-work", json={})
    assert finished.status_code == 200
    with uow:
        pair = uow.user_tickets.get(active["user_ticket_id"])
        assert pair.current_status() == "waiting_for_confirmation"


def test_user_disable_persists_projected_suspension(web, sample, uow):
    request = create_from_user(web)
    linked_id = request["ticket_user_id"]
    for _ in range(2):
        assert web.patch(f"/admin/users/{sample.user_id}/disable").status_code == 200
    with uow:
        assert not uow.users.get(sample.user_id).enabled
        internal = uow.tickets.get_by_user_ticket_id(linked_id)
        external = uow.user_tickets.get(linked_id)
        assert internal.current_status() == external.current_status() == "suspended"
        assert [status.status for status in external.statuses] == ["created", "suspended"]


def test_reenable_does_not_reopen_suspended_ticket(web, sample, uow):
    request = create_from_user(web)
    root = f"/admin/clients/{sample.client_id}"
    for action in ("disable", "enable", "disable"):
        assert web.patch(f"{root}/{action}").status_code == 200
    with uow:
        tied = uow.user_tickets.get(request["ticket_user_id"])
        assert tied.is_closed
        assert [status.status for status in tied.statuses] == ["created", "suspended"]


@pytest.mark.parametrize("path", ["/admin/tickets/", "/user/tickets/"])
@pytest.mark.parametrize("text", ["  ", "x", "x" * 4001], ids=["blank", "short", "long"])
def test_text_is_validated_at_the_request_boundary(web, sample, path, text):
    body = {"text_of_ticket": text}
    if path.startswith("/admin/"):
        body["client_id"] = sample.client_id
    assert web.post(path, json=body).status_code == 422


def test_negative_department_path_is_a_client_error(web):
    assert web.get("/admin/departments/-1").status_code == 422


def test_seeded_legacy_default_urgency_is_normal(web, sample, uow):
    created = create_internal(web, sample)
    with sqlite3.connect(sample.path) as db:
        db.execute("UPDATE tickets SET urgency_level = 0 WHERE ticket_id = ?", (created["ticket_id"],))
    with uow:
        assert uow.tickets.get(created["ticket_id"]).urgency == "normal"


def test_fresh_schema_default_and_link_foreign_key(sample):
    with sqlite3.connect(sample.path) as db:
        columns = {column[1]: column for column in db.execute("PRAGMA table_info(tickets)")}
        assert columns["urgency_level"][4] == "'normal'"
        foreign_keys = db.execute("PRAGMA foreign_key_list(tickets)").fetchall()
        assert any(key[2:5] == ("user_tickets", "user_ticket_id", "user_ticket_id")
                   for key in foreign_keys)


def test_whitespace_comment_is_a_client_error(web):
    created = create_from_user(web)
    route = f"/user/tickets/{created['ticket_user_id']}/comments"
    assert web.post(route, json={"comment": "  "}).status_code == 422


def test_admin_comment_preserves_the_author_in_the_user_history(web, sample):
    created = create_internal(
        web, sample, user_id=sample.user_id, comment="Synthetic staff comment",
    )
    loaded = web.get(f"/user/tickets/{created['user_ticket_id']}")
    assert loaded.status_code == 200
    assert loaded.json()["comments"][0]["actor_id"] == sample.admin_id


def test_workflow_error_names_the_statuses_without_dumping_the_aggregate():
    from src.domain.exceptions import DomainOperationError
    from src.domain.ticket import Ticket

    ticket = Ticket.create(client_id=1, admin_id=1, text_of_ticket="Synthetic ticket")
    with pytest.raises(DomainOperationError) as raised:
        ticket.execute(actor_employee_id=1)
    assert raised.value.message == (
        "Operation failed: Ticket status transition is not allowed: created -> executed"
    )


def test_legacy_suspended_projection_does_not_block_client_disable(web, sample, uow):
    created = create_from_user(web)
    linked_id = created["ticket_user_id"]
    client_route = f"/admin/clients/{sample.client_id}"
    assert web.patch(f"{client_route}/disable").status_code == 200
    assert web.patch(f"{client_route}/enable").status_code == 200
    with sqlite3.connect(sample.path) as db:
        db.execute("UPDATE user_tickets SET date_finished=NULL WHERE user_ticket_id=?", (linked_id,))
    assert web.patch(f"{client_route}/disable").status_code == 200
    with uow:
        assert not uow.clients.get(sample.client_id).enabled
        linked = uow.user_tickets.get(linked_id)
        assert linked.is_closed
        assert [status.status for status in linked.statuses] == ["created", "suspended"]



def test_owner_disable_closes_both_tickets_awaiting_review(web, sample, uow):
    created = work_ticket(web, sample, finish=True)
    linked_id = created["user_ticket_id"]
    with uow:
        internal = uow.tickets.get(created["ticket_id"])
        external = uow.user_tickets.get(linked_id)
        assert internal.current_status() == "ready_for_review"
        assert external.current_status() == "waiting_for_confirmation"

    for _ in range(2):
        response = web.patch(f"/admin/users/{sample.user_id}/disable")
        assert response.status_code == 200, response.text

    with uow:
        assert not uow.users.get(sample.user_id).enabled
        internal = uow.tickets.get(created["ticket_id"])
        external = uow.user_tickets.get(linked_id)
        assert internal.current_status() == external.current_status() == "suspended"
        assert internal.is_closed and external.is_closed
        assert internal.date_finished is not None
        assert external.date_finished is not None
        assert sum(record.status == "suspended" for record in internal.statuses) == 1
        assert sum(record.status == "suspended" for record in external.statuses) == 1
