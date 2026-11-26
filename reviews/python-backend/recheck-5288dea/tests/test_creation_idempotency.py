"""HTTP replay contracts for the complete agreed business-creation inventory.

Account attach is deliberately excluded. Account created with Admin/User belongs
to the parent creation, which is checked by the two additional parent cases.
No xfail: this snapshot lacks the feature, so replay tests must fail honestly.
"""
import secrets
from dataclasses import dataclass, field

import pytest

from conftest import transaction


CASES = (
    'client', 'department', 'admin', 'user', 'admin_role', 'user_role',
    'admin_ticket', 'user_ticket', 'admin_comment', 'user_comment',
    'admin_with_account', 'user_with_account',
)


@dataclass
class Creation:
    path: str
    headers: dict = field(repr=False)
    payload: dict = field(repr=False)
    effects: dict
    identity: str
    success: int = 201


def creation(world, case):
    """Prepare valid targets before taking the database baseline."""
    name = 'Synthetic creation ' + secrets.token_hex(5)
    if case == 'client':
        return Creation('/admin/clients/', world.admin_headers,
                        {'name': name}, {'clients': 1}, 'client_id')
    if case == 'department':
        return Creation('/admin/departments/', world.admin_headers,
                        {'name': name}, {'departments': 1}, 'department_id')
    if case in ('admin', 'admin_with_account', 'user', 'user_with_account'):
        admin = case.startswith('admin')
        payload = {'first_name': name}
        effects = {'employees': 1, 'admins' if admin else 'users': 1}
        if not admin:
            payload['client_id'] = world.client_id
        if case.endswith('_with_account'):
            payload.update(login='synthetic' + secrets.token_hex(8),
                           password='Aa1!' + secrets.token_hex(12))
            effects['accounts'] = 1
        return Creation('/admin/admins/' if admin else '/admin/users/',
                        world.admin_headers, payload, effects, 'employee_id')
    if case in ('admin_role', 'user_role'):
        realm = 'admin' if case == 'admin_role' else 'user'
        return Creation('/admin/roles/' + realm, world.admin_headers,
                        {'name': name, 'permissions': ['ticket.view']},
                        {'roles': 1}, 'role_id')
    if case == 'admin_ticket':
        # A linked pair checks the entire compound command, not just one INSERT.
        return Creation('/admin/tickets/', world.admin_headers, {
            'client_id': world.client_id, 'user_id': world.user_id,
            'text_of_ticket': 'Synthetic repeated staff request',
        }, {'tickets': 1, 'user_tickets': 1,
            'ticket_status_records': 2, 'user_tickets_status_record': 2}, 'ticket_id')
    if case == 'user_ticket':
        return Creation('/user/tickets/', world.user_headers,
                        {'text_of_ticket': 'Synthetic repeated owner request'},
                        {'tickets': 1, 'user_tickets': 1,
                         'ticket_status_records': 1, 'user_tickets_status_record': 1},
                        'ticket_user_id')
    external = world.user_ticket()['ticket_user_id']
    if case == 'user_comment':
        return Creation(f'/user/tickets/{external}/comments', world.user_headers,
                        {'comment': 'Synthetic repeated owner note'},
                        {'user_tickets_comment': 1}, 'ticket_user_id', 200)
    assert case == 'admin_comment'
    with transaction(world.path) as uow:
        internal = uow.tickets.get_by_user_ticket_id(external).ticket_id
    return Creation(f'/admin/tickets/{internal}/comments', world.admin_headers,
                    {'comment': 'Synthetic repeated staff note'},
                    {'ticket_comments': 1}, 'ticket_id', 200)


def counts(world, command):
    # Table names come exclusively from the fixed inventory above.
    with transaction(world.path) as uow:
        return {table: uow.connection.connect.execute(
            f'SELECT COUNT(*) FROM {table}'
        ).fetchone()[0] for table in command.effects}


def expected_counts(before, command, factor=1):
    return {table: before[table] + increment * factor
            for table, increment in command.effects.items()}


def post(world, command, key=None, payload=None):
    headers = dict(command.headers)
    if key is not None:
        headers['Idempotency-Key'] = key
    return world.api.post(command.path, headers=headers,
                          json=command.payload if payload is None else payload)


@pytest.mark.parametrize('world', ['memory', 'sqlite'], indirect=True)
@pytest.mark.parametrize('case', CASES)
def test_same_key_replays_original_success_with_one_business_effect(world, case):
    command = creation(world, case)
    before = counts(world, command)
    key = secrets.token_hex(16)
    first = post(world, command, key)
    assert first.status_code == command.success
    assert counts(world, command) == expected_counts(before, command)
    repeated = post(world, command, key)
    # A uniqueness 409 is not a replay of the original success either.
    assert repeated.status_code == first.status_code, (
        case, first.status_code, repeated.status_code)
    assert counts(world, command) == expected_counts(before, command), case
    assert repeated.json() == first.json(), case


@pytest.mark.parametrize('case', CASES)
def test_creation_accepts_omitted_optional_key(world, case):
    command = creation(world, case)
    before = counts(world, command)
    response = post(world, command)
    assert response.status_code == command.success
    assert counts(world, command) == expected_counts(before, command)


def second_valid_payload(command):
    """Avoid genuine uniqueness conflicts for independent named creations.

    Ticket text and comment text stay identical: a new logical command may
    intentionally repeat those texts. Department name and Account login retain
    their separate business uniqueness constraints.
    """
    payload = dict(command.payload)
    if 'name' in payload:
        payload['name'] += ' other'
    if 'login' in payload:
        payload['login'] += 'other'
    return payload


@pytest.mark.parametrize('case', CASES)
@pytest.mark.parametrize('use_keys', [False, True], ids=['no-key', 'different-keys'])
def test_separate_commands_keep_ordinary_creation_semantics(world, case, use_keys):
    command = creation(world, case)
    before = counts(world, command)
    first = post(world, command, secrets.token_hex(16) if use_keys else None)
    second = post(world, command, secrets.token_hex(16) if use_keys else None,
                  second_valid_payload(command))
    assert first.status_code == second.status_code == command.success
    assert counts(world, command) == expected_counts(before, command, factor=2)
    if case.endswith('_comment'):
        assert len(second.json()['comments']) == len(first.json()['comments']) + 1
    else:
        assert second.json()[command.identity] != first.json()[command.identity]
