"""Confirm the existing contact rules explicitly accepted by the owner."""
import pytest

from conftest import transaction


@pytest.mark.parametrize("side", ["admin", "user"])
def test_contact_can_change_in_initial_state(world, side):
    """200 and the positive new contact in both freshly read initial cards."""
    ticket_user_id = world.user_ticket()["ticket_user_id"]
    with transaction(world.path) as uow:
        ticket_id = uow.tickets.get_by_user_ticket_id(ticket_user_id).ticket_id
    if side == "admin":
        url, headers = f"/admin/tickets/{ticket_id}/contact-user", world.admin_headers
    else:
        url, headers = f"/user/tickets/{ticket_user_id}/contact-user", world.user_headers
    response = world.api.patch(url, headers=headers, json={"contact_user_id": world.contact_id})
    assert response.status_code == 200
    assert response.json()["contact_user_id"] == world.contact_id
    with transaction(world.path) as uow:
        internal = uow.tickets.get(ticket_id)
        external = uow.user_tickets.get(ticket_user_id)
        assert internal.contact_user_id == external.contact_user_id == world.contact_id
        assert internal.current_status() == "created_from_ticket_user"
        assert external.current_status() == "created"


def test_disabling_only_contact_closes_review_pair(world):
    """Disabling the contact in READY closes both cards with the owner still active."""
    ticket_user_id = world.user_ticket(contact_user_id=world.contact_id)["ticket_user_id"]
    with transaction(world.path) as uow:
        ticket_id = uow.tickets.get_by_user_ticket_id(ticket_user_id).ticket_id
    for step, body in [
        ("accept", {}), ("department", {"department_id": world.department_id}),
        ("executor", {"executor_id": world.admin_id}), ("start-work", {}), ("finish-work", {}),
    ]:
        world.action(ticket_id, step, body)
    answer = world.api.patch(f"/admin/users/{world.contact_id}/disable", headers=world.admin_headers)
    assert answer.status_code == 200
    with transaction(world.path) as uow:
        assert uow.users.get(world.user_id).enabled
        assert not uow.users.get(world.contact_id).enabled
        internal, external = uow.tickets.get(ticket_id), uow.user_tickets.get(ticket_user_id)
        assert internal.current_status() == external.current_status() == "suspended"
        assert internal.is_closed and external.is_closed
