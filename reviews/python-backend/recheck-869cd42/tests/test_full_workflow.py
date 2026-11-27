"""Use the same pair throughout the workflow, reading through both realms."""
import pytest

from conftest import transaction
from test_executor_guard import accepted_pair, pair_state


@pytest.mark.parametrize("branch", ["office", "remote"])
def test_pair_completes_and_user_can_read_history(world, branch):
    """Early confirm rejects without changes; finished work confirms both cards."""
    internal_id, external_id = accepted_pair(world, recommended=branch == "remote")
    path = f"/user/tickets/{external_id}"
    before = pair_state(world, internal_id, external_id)
    early = world.api.patch(path + "/confirm", headers=world.user_headers, json={})
    assert early.status_code == 400
    assert pair_state(world, internal_id, external_id) == before

    if branch == "office":
        world.action(internal_id, "executor", {"executor_id": world.admin_id})
        world.action(internal_id, "start-work")
    else:
        world.action(internal_id, "start-remote-work")
    assert pair_state(world, internal_id, external_id)[:2] == ("at_work", world.admin_id)

    finished = world.action(internal_id, "finish-work")
    assert finished["statuses"][-1]["status"] == "ready_for_review"
    review = world.api.get(path, headers=world.user_headers)
    assert review.status_code == 200
    assert review.json()["statuses"][-1]["status"] == "waiting_for_confirmation"
    with transaction(world.path) as uow:
        assert uow.tickets.get(internal_id).current_status() == "ready_for_review"
        assert uow.user_tickets.get(external_id).current_status() == "waiting_for_confirmation"

    response = world.api.patch(path + "/confirm", headers=world.user_headers, json={"comment": "Work verified"})
    assert response.status_code == 200
    readback = world.api.get(path, headers=world.user_headers)
    assert readback.status_code == 200
    assert readback.json()["statuses"][-1]["status"] == "confirmed_by_user"
    assert readback.json()["statuses"][-1]["comment"] == "Work verified"
    with transaction(world.path) as uow:
        internal, external = uow.tickets.get(internal_id), uow.user_tickets.get(external_id)
        assert internal.current_status() == external.current_status() == "confirmed_by_user"
        assert internal.is_closed and external.is_closed
        assert internal.user_ticket_id == external.ticket_user_id
