import pytest
import secrets

from conftest import database_uow
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role_new import Role


def restrict_admin(world, *permissions):
    with database_uow(world.path) as uow:
        role = uow.roles_admin.save(Role.create(
            name="Synthetic limited " + secrets.token_hex(4), permissions=frozenset(permissions),
        ))
        uow.connection.connect.execute("DELETE FROM admins_roles WHERE employee_id = ?", (world.admin_id,))
        uow.connection.connect.execute("INSERT INTO admins_roles VALUES (?, ?)", (world.admin_id, role.role_id))


def user_role_id(world):
    with database_uow(world.path) as uow:
        return next(iter(uow.users.get(world.user_id).role_ids()))


def test_create_user_cannot_bypass_role_assignment_permission(world):
    role_id = user_role_id(world)
    restrict_admin(world, AdminPermission.USER_OPERATION)
    before = world.client.post(
        f"/admin/users/{world.contact_id}/roles", headers=world.admin_headers,
        json={"roles": [role_id]},
    )
    assert before.status_code == 403
    with database_uow(world.path) as uow:
        count = uow.connection.connect.execute("SELECT count(*) FROM users").fetchone()[0]
    response = world.client.post("/admin/users/", headers=world.admin_headers, json={
        "client_id": world.client_id, "first_name": "Synthetic requester", "roles": [role_id],
    })
    assert response.status_code == 403
    with database_uow(world.path) as uow:
        assert uow.connection.connect.execute("SELECT count(*) FROM users").fetchone()[0] == count
    response = world.client.post("/admin/users/", headers=world.admin_headers, json={
        "client_id": world.client_id, "first_name": "Synthetic requester",
    })
    assert response.status_code == 201
    restrict_admin(world, AdminPermission.USER_OPERATION, AdminPermission.ROLE_USER_ASSIGN)
    response = world.client.post("/admin/users/", headers=world.admin_headers, json={
        "client_id": world.client_id, "first_name": "Synthetic requester", "roles": [role_id],
    })
    assert response.status_code == 201
    assert role_id in response.json()["roles"]


@pytest.mark.parametrize("disabled_client", [False, True])
def test_revoke_user_role_does_not_require_admin_role_permission(world, disabled_client):
    role_id = user_role_id(world)
    if disabled_client:
        response = world.client.patch(
            f"/admin/clients/{world.client_id}/disable", headers=world.admin_headers,
        )
        assert response.status_code == 200
    restrict_admin(world, AdminPermission.ROLE_USER_ASSIGN)
    response = world.client.request(
        "DELETE", f"/admin/users/{world.user_id}/roles", headers=world.admin_headers,
        json={"roles": [role_id]},
    )
    assert response.status_code == 200
    assert role_id not in response.json()["roles"]
    restrict_admin(world, AdminPermission.USER_OPERATION)
    response = world.client.request(
        "DELETE", f"/admin/users/{world.user_id}/roles", headers=world.admin_headers,
        json={"roles": [role_id]},
    )
    assert response.status_code == 403


@pytest.mark.parametrize("realm", ["admins", "users"])
def test_short_password_is_client_error_and_does_not_change_account(world, realm):
    employee_id = world.admin_id if realm == "admins" else world.user_id
    response = world.client.patch(
        f"/admin/{realm}/{employee_id}/password", headers=world.admin_headers,
        json={"password": "x"},
    )
    assert response.status_code == 400
    with database_uow(world.path) as uow:
        entity = uow.admins.get(employee_id) if realm == "admins" else uow.users.get(employee_id)
        assert entity.account.verify_password(world.password)


def test_invalid_login_is_client_error_and_account_is_not_attached(world):
    response = world.client.post(
        f"/admin/users/{world.contact_id}/account", headers=world.admin_headers,
        json={"login": "invalid synthetic login", "password": world.password},
    )
    assert response.status_code == 400
    with database_uow(world.path) as uow:
        assert not uow.users.get(world.contact_id).account


@pytest.mark.parametrize("realm", ["admin", "user"])
def test_unknown_permission_is_request_validation_error(world, realm):
    response = world.client.post(f"/admin/roles/{realm}", headers=world.admin_headers, json={
        "name": "Synthetic invalid role", "permissions": ["synthetic.unknown"],
    })
    assert response.status_code == 422
    with database_uow(world.path) as uow:
        assert uow.connection.connect.execute(
            "SELECT count(*) FROM roles WHERE name = ?", ("Synthetic invalid role",),
        ).fetchone()[0] == 0


@pytest.mark.parametrize("realm", ["admin", "user"])
def test_description_limit_is_client_error_and_preserves_value(world, realm):
    created = world.create_user_ticket(description="Synthetic original")
    ticket_id = created["ticket_user_id"]
    if realm == "admin":
        with database_uow(world.path) as uow:
            ticket_id = uow.tickets.get_by_user_ticket_id(ticket_id).ticket_id
    headers = world.admin_headers if realm == "admin" else world.user_headers
    response = world.client.patch(
        f"/{realm}/tickets/{ticket_id}/description", headers=headers,
        json={"description": "x" * 4001},
    )
    assert response.status_code == 422
    with database_uow(world.path) as uow:
        ticket = uow.tickets.get(ticket_id) if realm == "admin" else uow.user_tickets.get(ticket_id)
        assert str(ticket.description) == "Synthetic original"
    response = world.client.patch(
        f"/{realm}/tickets/{ticket_id}/description", headers=headers,
        json={"description": "x" * 4000},
    )
    assert response.status_code == 200


@pytest.mark.parametrize("scenario", ["self_disable", "negative_client", "assigned_role", "system_role"])
def test_expected_application_rejection_returns_client_error(world, scenario):
    if scenario == "self_disable":
        response = world.client.patch(f"/admin/admins/{world.admin_id}/disable", headers=world.admin_headers)
    elif scenario == "negative_client":
        response = world.client.get("/admin/clients/-1", headers=world.admin_headers)
    else:
        with database_uow(world.path) as uow:
            role_id = next(iter(uow.admins.get(world.admin_id).role_ids()))
            if scenario == "system_role":
                uow.connection.connect.execute("UPDATE roles SET is_system_role = 1 WHERE role_id = ?", (role_id,))
        response = world.client.delete(f"/admin/roles/admin/{role_id}", headers=world.admin_headers)
    assert response.status_code == 400
    with database_uow(world.path) as uow:
        assert uow.admins.get(world.admin_id).enabled


def test_delete_role_assigned_to_user_is_rejected_before_delete(world):
    role_id = user_role_id(world)
    response = world.client.delete(f"/admin/roles/user/{role_id}", headers=world.admin_headers)
    assert response.status_code == 400
    with database_uow(world.path) as uow:
        assert uow.roles_user.get(role_id).role_id == role_id
        assert role_id in uow.users.get(world.user_id).role_ids()


@pytest.mark.parametrize("realm", ["admin", "user"])
def test_description_creation_uses_normalized_domain_limit(world, realm):
    headers = world.admin_headers if realm == "admin" else world.user_headers
    body = {"text_of_ticket": "Synthetic description boundary", "description": "x" * 4001}
    if realm == "admin":
        body["client_id"] = world.client_id
    invalid = world.client.post(f"/{realm}/tickets/", headers=headers, json=body)
    assert invalid.status_code == 422
    body["description"] = "  " + "x" * 4000 + "  "
    valid = world.client.post(f"/{realm}/tickets/", headers=headers, json=body)
    assert valid.status_code == 201
    assert valid.json()["description"] == "x" * 4000
