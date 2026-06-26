from __future__ import annotations

import pytest

from src.application.dto.client_dto import ClientDTO
from src.application.dto.employee_dto import UserDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.application.helper.employee_helper import EmployeeHelper
from src.application.services.client_service import ClientApplicationService
from src.application.services.user_service import UserApplicationService
from src.domain.account import NoAccount
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission, UserPermission


def test_actor_helper_returns_admin_with_required_permission(
    uow,
    admin_with_all_permissions,
):
    uow.admins.save(admin_with_all_permissions)

    helper = EmployeeActorHelper(uow)

    actor = helper.require_actor_admin(
        actor_admin_id=admin_with_all_permissions.employee_id,
        permission=AdminPermission.TICKET_OPERATION,
    )

    assert actor == admin_with_all_permissions

def test_actor_helper_rejects_admin_without_required_permission(
    uow,
    admin_with_all_permissions,
):
    role = type(
        "Role",
        (),
        {
            "role_id": 1,
            "permissions": frozenset({AdminPermission.TICKET_VIEW}),
        },
    )()

    admin_with_all_permissions.revoke_role(1)
    admin_with_all_permissions.grant_role(1)

    uow.admins.save(admin_with_all_permissions)
    uow.roles_admin.save(role)

    helper = EmployeeActorHelper(uow)

    with pytest.raises(PermissionError):
        helper.require_actor_admin(
            actor_admin_id=admin_with_all_permissions.employee_id,
            permission=AdminPermission.TICKET_OPERATION,
        )

def test_actor_helper_returns_user_with_required_permission(uow, user):
    helper = EmployeeActorHelper(uow)

    actor = helper.require_actor_user(
        actor_user_id=user.employee_id,
        permission=UserPermission.TICKET_OPERATION,
    )

    assert actor == user


def test_employee_helper_detects_existing_login(uow, user):
    helper = EmployeeHelper(uow)

    with pytest.raises(DomainOperationError, match="already exists"):
        helper.ensure_login_is_free(login=str(user.account.login))


def test_employee_helper_allows_empty_or_new_login(uow):
    helper = EmployeeHelper(uow)

    helper.ensure_login_is_free(login=None)
    helper.ensure_login_is_free(login="new-login")


def test_client_service_create_client_saves_and_returns_dto(uow, admin_with_all_permissions):
    service = ClientApplicationService(uow)
    dto = ClientDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        name="New Client",
        email="new@example.com",
        address="Some Street",
        phone="123",
    )

    result = service.create_client(dto)

    assert result.client_id != 0
    assert result.name == "New Client"
    assert result.email == "new@example.com"

    saved_client = uow.clients.get(result.client_id)

    assert saved_client.name.value == "New Client"
    assert saved_client.email.value == "new@example.com"

def test_client_service_update_contact(uow, admin_with_all_permissions, client):
    service = ClientApplicationService(uow)
    dto = ClientDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        client_id=client.client_id,
        name="ignored",
        email="support@example.com",
        address="New Street",
        phone="456",
    )

    result = service.update_contact(dto)

    assert result.email == "support@example.com"
    assert result.address == "New Street"
    assert result.phone == "456"


def test_client_service_disable_and_enable(uow, admin_with_all_permissions, client):
    service = ClientApplicationService(uow)
    dto = ClientDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        client_id=client.client_id,
        name="ignored",
    )

    disabled = service.disable(dto)
    assert disabled.enabled is False

    enabled = service.enable(dto)
    assert enabled.enabled is True


def test_client_service_delete_rejects_client_with_users(uow, admin_with_all_permissions, client):
    service = ClientApplicationService(uow)
    dto = ClientDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        client_id=client.client_id,
        name=client.name.value,
    )

    with pytest.raises(DomainOperationError, match="cannot be deleted"):
        service.delete(dto_client=dto)


def test_user_service_create_user_saves_and_returns_dto(uow, admin_with_all_permissions, client):
    service = UserApplicationService(uow)
    dto = UserDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        client_id=client.client_id,
        first_name="New User",
        email="new.user@example.com",
        login="new_user",
        password="Strong1!",
    )

    result = service.create_user(user_dto=dto)

    assert result.employee_id != 0
    assert result.first_name == "New User"
    assert result.client_id == client.client_id
    assert result.login == "new_user"


def test_user_service_update_user(uow, admin_with_all_permissions, user):
    service = UserApplicationService(uow)
    dto = UserDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        employee_id=user.employee_id,
        client_id=user.client_id,
        first_name="Updated",
        last_name="Name",
        email="updated@example.com",
    )

    result = service.update_user(user_dto=dto)

    assert result.first_name == "Updated"
    assert result.last_name == "Name"
    assert result.email == "updated@example.com"


def test_user_service_attach_detach_account(uow, admin_with_all_permissions, other_user):
    service = UserApplicationService(uow)
    dto = UserDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        employee_id=other_user.employee_id,
        client_id=other_user.client_id,
        login="attached_login",
        password="Strong1!",
    )

    attached = service.attach_account(user_dto=dto)
    assert attached.login == "attached_login"

    detached = service.detach_account(user_dto=dto)
    assert detached.login == ""
    assert isinstance(other_user.account, NoAccount)


def test_user_service_change_password_requires_password(uow, admin_with_all_permissions, user):
    service = UserApplicationService(uow)
    dto = UserDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        employee_id=user.employee_id,
        client_id=user.client_id,
        password="",
    )

    with pytest.raises(ValueError, match="Password cannot be empty"):
        service.change_password(user_dto=dto)


def test_user_service_disable_and_enable(uow, admin_with_all_permissions, user):
    service = UserApplicationService(uow)
    dto = UserDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        employee_id=user.employee_id,
        client_id=user.client_id,
    )

    disabled = service.disable(user_dto=dto)
    assert disabled.enabled is False

    enabled = service.enable(user_dto=dto)
    assert enabled.enabled is True


def test_user_service_delete_rejects_user_with_user_tickets(uow, admin_with_all_permissions, user, user_ticket):
    uow.user_tickets.items[user_ticket.ticket_id] = user_ticket
    service = UserApplicationService(uow)
    dto = UserDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        employee_id=user.employee_id,
        client_id=user.client_id,
    )

    with pytest.raises(DomainOperationError, match="has tickets"):
        service.delete(user_dto=dto)
