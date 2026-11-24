"""FastAPI and persistence checks for the current string comment contract."""
import pytest

from conftest import transaction


def admin_create(world, *, owner=False, comment=""):
    response = world.api.post('/admin/tickets/', headers=world.admin_headers, json={
        'client_id': world.client_id,
        'user_id': world.user_id if owner else 0,
        'text_of_ticket': 'Synthetic administrative registration',
        'comment': comment,
    })
    assert response.status_code == 201, response.text
    return response.json()


def internal_for(world, external_id):
    with transaction(world.path) as uow:
        return uow.tickets.get_by_user_ticket_id(external_id).ticket_id


def read_internal(world, internal_id):
    response = world.api.get(f'/admin/tickets/{internal_id}', headers=world.admin_headers)
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize('source', ['user', 'admin_for_user', 'standalone'])
def test_admin_response_comment_contract_includes_empty_and_status_text(world, source):
    """Admin GET/create/comment returns plain strings and preserves author after reload."""
    if source == 'user':
        internal_id = internal_for(world, world.user_ticket()['ticket_user_id'])
        initial = read_internal(world, internal_id)
        assert initial['statuses'][0]['actor_id'] == 0
        accepted = world.action(internal_id, 'accept', {'comment': 'Accepted by operator'})
    else:
        accepted = admin_create(world, owner=source == 'admin_for_user', comment='Accepted by operator')
        internal_id = accepted['ticket_id']
        initial = read_internal(world, internal_id)

    response = world.api.post(f'/admin/tickets/{internal_id}/comments', headers=world.admin_headers,
                              json={'comment': 'Ordinary operator note'})
    assert response.status_code == 200, response.text
    current = read_internal(world, internal_id)
    for payload in [initial, accepted, response.json(), current]:
        for record in payload['statuses'] + payload['comments']:
            assert isinstance(record['comment'], str), record
    assert current['statuses'][0]['comment'] == ''
    assert current['statuses'][-1]['comment'] == 'Accepted by operator'
    assert current['comments'][-1]['comment'] == 'Ordinary operator note'
    assert current['comments'][-1]['actor_id'] == world.admin_id


@pytest.mark.parametrize("side", ["admin", "user"])
@pytest.mark.parametrize("entry", [{}, {"comment": None}, {"comment": "  "}], ids=["missing", "null", "blank"])
def test_invalid_comment_preserves_history(world, side, entry):
    """Reject omitted, null or blank comments; neither history is changed."""
    external_id = world.user_ticket()["ticket_user_id"]
    internal_id = internal_for(world, external_id)
    if side == "admin":
        url, headers = f"/admin/tickets/{internal_id}/comments", world.admin_headers
    else:
        url, headers = f"/user/tickets/{external_id}/comments", world.user_headers
    response = world.api.post(url, json=entry, headers=headers)
    assert response.status_code == 422
    with transaction(world.path) as uow:
        assert not uow.tickets.get(internal_id).comments
        assert not uow.user_tickets.get(external_id).comments


def test_telephone_registration_keeps_two_meanings_of_actor(world):
    """201. External CREATED is User; internal registration and comment are Admin."""
    stored = admin_create(world, owner=True, comment="Entered by operator")
    with transaction(world.path) as uow:
        external = uow.user_tickets.get(stored["user_ticket_id"])
        internal = uow.tickets.get(stored["ticket_id"])
        assert external.user_id == internal.user_id == world.user_id
        assert external.statuses[0].status.value == "created"
        assert external.statuses[0].actor_employee_id == world.user_id
        assert internal.statuses[0].status.value == "created_from_request_user"
        assert internal.statuses[0].actor_employee_id == world.admin_id
        assert external.comments[0].employee_id == internal.comments[0].employee_id == world.admin_id
