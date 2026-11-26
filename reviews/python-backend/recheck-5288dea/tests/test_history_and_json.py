"""Regression contracts for actual creation actors and admin comment JSON."""
import pytest

from conftest import transaction
from src.domain.services.ticket_user_service import TicketUserService
from src.domain.ticket_user import TicketUser


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


def test_admin_registration_records_initiator_separately_from_owner(world):
    created = admin_create(world, owner=True, comment='Entered by operator')
    with transaction(world.path) as uow:
        external = uow.user_tickets.get(created['user_ticket_id'])
        internal = uow.tickets.get(created['ticket_id'])
        assert external.user_id == internal.user_id == world.user_id
        assert external.statuses[0].actor_employee_id == world.admin_id
        assert internal.statuses[0].actor_employee_id == world.admin_id
        assert external.comments[0].employee_id == internal.comments[0].employee_id == world.admin_id
        assert external.comments[0].comment.value == 'Entered by operator'
        assert external.statuses[-1].actor_employee_id == world.admin_id


def test_user_creation_preserves_owner_actor_and_system_internal_origin(world):
    created = world.user_ticket(comment='Entered by owner')
    with transaction(world.path) as uow:
        external = uow.user_tickets.get(created['ticket_user_id'])
        internal = uow.tickets.get_by_user_ticket_id(external.ticket_user_id)
        assert external.user_id == internal.user_id == world.user_id
        assert external.statuses[0].actor_employee_id == world.user_id
        assert external.comments[0].employee_id == world.user_id
        assert internal.statuses[0].actor_employee_id == 0
        assert internal.statuses[0].status.value == 'created_from_ticket_user'


def test_standalone_admin_creation_preserves_admin_history(world):
    created = admin_create(world, comment='Standalone operator note')
    with transaction(world.path) as uow:
        internal = uow.tickets.get(created['ticket_id'])
        assert internal.user_id == internal.user_ticket_id == 0
        assert internal.statuses[0].actor_employee_id == world.admin_id
        assert internal.comments[0].employee_id == world.admin_id


def test_factory_calls_without_optional_actor_remain_compatible(world):
    created = TicketUser.create(client_id=world.client_id, user_id=world.user_id,
                                text_of_ticket='Factory owner request', comment='Owner note')
    assert created.statuses[0].actor_employee_id == created.comments[0].employee_id == world.user_id
    with transaction(world.path) as uow:
        created = TicketUserService.create(client=uow.clients.get(world.client_id),
                    user=uow.users.get(world.user_id), contact_user=uow.users.get(world.contact_id),
                    text_of_ticket='Service owner request')
    assert created.statuses[0].actor_employee_id == world.user_id


def test_factory_explicit_initiator_owns_creation_record_and_comment(world):
    created = TicketUser.create(client_id=world.client_id, user_id=world.user_id,
                text_of_ticket='Request entered by staff', comment='Staff note',
                actor_employee_id=world.admin_id)
    assert created.user_id == world.user_id
    assert created.statuses[0].actor_employee_id == world.admin_id
    assert created.comments[0].employee_id == world.admin_id


def test_reading_legacy_created_actor_does_not_rewrite_history(world):
    created = admin_create(world, owner=True, comment='Historical operator note')
    with transaction(world.path) as uow:
        # Simulate a pre-fix stored row: the real initiator cannot be recovered
        # reliably from the owner ID or an unrelated ordinary comment.
        uow.connection.connect.execute('UPDATE user_tickets_status_record SET actor_employee_id=? '
            'WHERE user_ticket_id=? AND status=?', (world.user_id, created['user_ticket_id'], 'created'))
    response = world.api.get(f'/user/tickets/{created["user_ticket_id"]}', headers=world.user_headers)
    assert response.status_code == 200, response.text
    assert response.json()['statuses'][0]['actor_id'] == world.user_id
    with transaction(world.path) as uow:
        assert uow.user_tickets.get(created['user_ticket_id']).statuses[0].actor_employee_id == world.user_id


@pytest.mark.parametrize('source', ['user', 'admin_for_user', 'standalone'])
def test_admin_response_comment_contract_includes_empty_and_status_text(world, source):
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
