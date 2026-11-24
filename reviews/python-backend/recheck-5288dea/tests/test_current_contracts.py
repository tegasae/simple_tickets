"""Behavioural contracts from the owner's latest decisions, not xfail markers."""
import secrets

import pytest

from conftest import transaction


def test_staff_is_the_actual_initial_actor_but_owner_is_preserved(world):
    response = world.api.post('/admin/tickets/', headers=world.admin_headers, json={
        'client_id': world.client_id, 'user_id': world.user_id,
        'text_of_ticket': 'Synthetic staff registration', 'comment': 'Synthetic staff note',
    })
    assert response.status_code == 201
    with transaction(world.path) as uow:
        external = uow.user_tickets.get(response.json()['user_ticket_id'])
        assert external.user_id == world.user_id
        assert external.comments[0].employee_id == world.admin_id
        assert external.statuses[0].actor_employee_id == world.admin_id


def test_admin_comment_and_status_comment_are_plain_strings(world):
    created = world.api.post('/admin/tickets/', headers=world.admin_headers, json={
        'client_id': world.client_id, 'text_of_ticket': 'Synthetic JSON request',
        'comment': 'Synthetic note',
    })
    assert created.status_code == 201
    internal_id = created.json()['ticket_id']
    response = world.api.get(f'/admin/tickets/{internal_id}', headers=world.admin_headers)
    assert response.status_code == 200
    assert response.json()['comments'][0]['comment'] == 'Synthetic note'
    assert all(isinstance(item['comment'], str) for item in response.json()['statuses'])


@pytest.mark.parametrize('world', ['memory', 'sqlite'], indirect=True)
@pytest.mark.parametrize('event', ['password', 'employee_disable_enable', 'account_disable_enable', 'detach_reattach'])
def test_account_lifecycle_permanently_rejects_old_refresh(world, event):
    root = f'/admin/users/{world.user_id}'
    if event == 'password':
        response = world.api.patch(root + '/password', headers=world.admin_headers,
                                  json={'password': 'Aa1!' + secrets.token_hex(12)})
        assert response.status_code == 200
    elif event == 'detach_reattach':
        assert world.api.delete(root + '/account', headers=world.admin_headers).status_code == 200
        response = world.api.post(root + '/account', headers=world.admin_headers,
                                  json={'login': world.login, 'password': world.password})
        assert response.status_code == 200
    else:
        suffix = '/account' if event == 'account_disable_enable' else ''
        # The existing routes place the account command after /account/.
        disabled = world.api.patch(root + suffix + '/disable', headers=world.admin_headers)
        assert disabled.status_code == 200, disabled.text
        while_disabled = world.api.post('/auth/user/refresh', json={'refresh_token': world.refresh})
        assert while_disabled.status_code == 401
        enabled = world.api.patch(root + suffix + '/enable', headers=world.admin_headers)
        assert enabled.status_code == 200
    response = world.api.post('/auth/user/refresh', json={'refresh_token': world.refresh})
    assert response.status_code == 401


@pytest.mark.parametrize('world', ['memory', 'sqlite'], indirect=True)
def test_same_optional_idempotency_key_returns_one_created_pair(world):
    headers = {**world.user_headers, 'Idempotency-Key': secrets.token_hex(16)}
    payload = {'text_of_ticket': 'Synthetic repeated request'}
    first = world.api.post('/user/tickets/', headers=headers, json=payload)
    repeated = world.api.post('/user/tickets/', headers=headers, json=payload)
    assert first.status_code == repeated.status_code == 201
    with transaction(world.path) as uow:
        assert uow.connection.connect.execute('SELECT COUNT(*) FROM user_tickets').fetchone()[0] == 1
        assert uow.connection.connect.execute('SELECT COUNT(*) FROM tickets').fetchone()[0] == 1
    assert repeated.json() == first.json()


def test_same_key_different_body_is_conflict(world):
    headers = {**world.user_headers, 'Idempotency-Key': secrets.token_hex(16)}
    assert world.api.post('/user/tickets/', headers=headers,
                          json={'text_of_ticket': 'Synthetic first body'}).status_code == 201
    changed = world.api.post('/user/tickets/', headers=headers,
                             json={'text_of_ticket': 'Synthetic changed body'})
    assert changed.status_code == 409


def test_no_key_and_different_keys_keep_intentionally_distinct_requests(world):
    first, second = world.user_ticket(), world.user_ticket()
    assert first['ticket_user_id'] != second['ticket_user_id']
    ids = []
    for _ in range(2):
        response = world.api.post('/user/tickets/',
            headers={**world.user_headers, 'Idempotency-Key': secrets.token_hex(16)},
            json={'text_of_ticket': 'Synthetic intentional duplicate text'})
        assert response.status_code == 201
        ids.append(response.json()['ticket_user_id'])
    assert ids[0] != ids[1]


def test_disabled_client_active_pair_can_finish_and_be_finalized_by_admin(world):
    internal_id, external_id = world.pair()
    response = world.api.patch(f'/admin/clients/{world.client_id}/disable', headers=world.admin_headers)
    assert response.status_code == 200
    world.action(internal_id, 'finish-work')
    with transaction(world.path) as uow:
        assert uow.tickets.get(internal_id).current_status() == 'ready_for_review'
    world.action(internal_id, 'execute')
    with transaction(world.path) as uow:
        assert uow.tickets.get(internal_id).is_closed
        assert uow.user_tickets.get(external_id).is_closed
