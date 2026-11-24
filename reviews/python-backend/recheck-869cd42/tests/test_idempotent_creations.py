"""HTTP replay contracts for the complete agreed business-creation inventory.

Account attach is deliberately excluded. Account created with Admin/User belongs
to the parent creation, which is checked by the two additional parent cases.
The expected response and persistent effects are identical for both snapshots.
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


@pytest.mark.parametrize('case', CASES)
def test_same_key_replays_original_success_with_one_business_effect(world, case):
    """Same key and request return original success and one set of database effects."""
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
    """No key keeps the original success status and one business effect."""
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
    """Separate operations both succeed and both effects persist."""
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


@pytest.mark.parametrize("case", CASES)
def test_same_key_changed_body_is_conflict(world, case):
    """Committed key with changed request returns 409 and keeps first effects."""
    command = creation(world, case)
    before = counts(world, command)
    payload = second_valid_payload(command)
    if "text_of_ticket" in payload:
        payload["text_of_ticket"] += " updated"
    if "comment" in payload:
        payload["comment"] += " updated"
    if payload == command.payload:
        payload["first_name"] += " updated"
    key = secrets.token_hex(16)
    assert post(world, command, key).status_code == command.success
    changed = post(world, command, key, payload)
    assert changed.status_code == 409
    assert changed.json()["detail"] == "Idempotency-Key already used for a different request"
    assert counts(world, command) == expected_counts(before, command)


def test_header_optional_in_openapi_on_creation_routes_only(world):
    """All ten routes advertise the optional header; Account attach does not."""
    spec = world.api.get("/openapi.json")
    assert spec.status_code == 200
    functions = [
        "/admin/clients/", "/admin/departments/", "/admin/admins/", "/admin/users/",
        "/admin/roles/admin", "/admin/roles/user", "/admin/tickets/", "/user/tickets/",
        "/admin/tickets/{ticket_id}/comments", "/user/tickets/{ticket_user_id}/comments",
    ]
    for path in functions:
        parameters = spec.json()["paths"][path]["post"].get("parameters", [])
        matches = [x for x in parameters if x["name"].lower() == "idempotency-key"]
        assert len(matches) == 1, path
        assert matches[0]["in"] == "header" and matches[0]["required"] is False
    for path in ("/admin/admins/{employee_id}/account", "/admin/users/{employee_id}/account"):
        params = spec.json()["paths"][path]["post"].get("parameters", [])
        assert not any(p["name"].lower() == "idempotency-key" for p in params)


@pytest.mark.parametrize("entry", ["", "contains space", "x" * 129])
def test_invalid_key_rejected_with_no_writes(world, entry):
    """Invalid optional header gives 422 before creating the pair."""
    command = creation(world, "user_ticket")
    before = counts(world, command)
    assert post(world, command, entry).status_code == 422
    assert counts(world, command) == before


def test_default_fields_and_role_sets_replay(world):
    """Omitted defaults and reordering an unordered permission list replay."""
    ticket = creation(world, "user_ticket")
    key = secrets.token_hex(16)
    first = post(world, ticket, key)
    response = post(world, ticket, key, {**ticket.payload, "description": "", "contact_user_id": 0})
    assert first.status_code == response.status_code == 201
    assert response.json() == first.json()
    roles = creation(world, "admin_role")
    left = {**roles.payload, "permissions": ["ticket.view", "ticket.operation"]}
    right = {**roles.payload, "permissions": ["ticket.operation", "ticket.view", "ticket.view"]}
    first, second = post(world, roles, key, left), post(world, roles, key, right)
    assert first.status_code == second.status_code == 201
    assert second.json() == first.json()


def test_key_scope_separates_commands_and_authenticated_subjects(world):
    """One key has independent results across subjects and commands."""
    from src.domain.employee import User

    with transaction(world.path) as uow:
        owner = uow.users.get(world.user_id)
        login_name = "additional" + secrets.token_hex(8)
        password = "Aa1!" + secrets.token_hex(12)
        other = User.create(
            first_name="Synthetic second requester", client_id=world.client_id,
            login=login_name, password=password,
        )
        other = uow.users.save(other)
        for role_id in owner.role_ids():
            uow.connection.connect.execute("INSERT INTO users_roles VALUES(?, ?)", (other.employee_id, role_id))
    result = world.api.post("/auth/user/login", data={"username": login_name, "password": password})
    assert result.status_code == 200
    headers = {"Authorization": "Bearer " + result.json()["access_token"]}
    ticket = creation(world, "user_ticket")
    second = Creation(ticket.path, headers, ticket.payload, ticket.effects, ticket.identity)
    key = secrets.token_hex(16)
    first, later = post(world, ticket, key), post(world, second, key)
    assert first.status_code == later.status_code == 201
    assert first.json()["ticket_user_id"] != later.json()["ticket_user_id"]
    assert post(world, second, key).json() == later.json()
    assert post(world, ticket, key).json() == first.json()
    for command in ("client", "department"):
        creation_request = creation(world, command)
        success = post(world, creation_request, key)
        assert success.status_code == 201
        assert post(world, creation_request, key).json() == success.json()


def test_replay_checks_current_permissions_and_survives_access_rotation(world):
    """200 refresh preserves subject scope; revoked permission denies replay."""
    from test_lifetime import refresh

    ticket = creation(world, "user_ticket")
    key = secrets.token_hex(16)
    first = post(world, ticket, key)
    assert first.status_code == 201
    rotated = refresh(world, world.refresh)
    assert rotated.status_code == 200
    ticket.headers = {"Authorization": "Bearer " + rotated.json()["access_token"]}
    assert post(world, ticket, key).json() == first.json()
    with transaction(world.path) as uow:
        roles = list(uow.users.get(world.user_id).role_ids())
    for role_id in roles:
        result = world.api.request(
            "DELETE", f"/admin/users/{world.user_id}/roles", json={"roles": [role_id]},
            headers=world.admin_headers,
        )
        assert result.status_code == 200
    before = counts(world, ticket)
    denied = post(world, ticket, key)
    assert denied.status_code == 403
    assert counts(world, ticket) == before


def test_comment_key_fingerprints_the_target(world):
    """The same key and comment text on another ticket are a conflict."""
    command, other = creation(world, "user_comment"), creation(world, "user_comment")
    before = counts(world, command)
    key = secrets.token_hex(16)
    assert post(world, command, key).status_code == 200
    assert post(world, other, key).status_code == 409
    assert counts(world, command) == expected_counts(before, command)


def test_duplicate_key_header_rejected_before_write(world):
    """Ambiguous multiple header values give 422 without an entity write."""
    command = creation(world, "user_ticket")
    before = counts(world, command)
    headers = list(command.headers.items()) + [("Idempotency-Key", "one"), ("Idempotency-Key", "two")]
    result = world.api.post(command.path, headers=headers, json=command.payload)
    assert result.status_code == 422
    assert counts(world, command) == before
