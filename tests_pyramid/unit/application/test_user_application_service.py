from __future__ import annotations

import pytest

from src.application.dto.employee_dto import UserDTO
from src.application.services.user_service import UserApplicationService
from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from tests_pyramid.support.fakes import FakeUnitOfWork

pytestmark = pytest.mark.unit


def setup(uow: FakeUnitOfWork) -> tuple[Admin, Client]:
    admin_role = Role(role_id=1, name="admin", permissions=frozenset(AdminPermission))
    uow.roles_admin.save(admin_role)
    actor = Admin.create(employee_id=10, first_name="Actor", roles={1})
    uow.admins.save(actor)
    client = Client.create(client_id=100, name="Client")
    uow.clients.save(client)
    uow.calls.clear()
    return actor, client


def test_create_user_and_optional_roles() -> None:
    uow = FakeUnitOfWork()
    actor, client = setup(uow)
    role = Role(role_id=2, name="user-ticket", permissions=frozenset({UserPermission.TICKET_VIEW}))
    uow.roles_user.save(role)
    service = UserApplicationService(uow)
    result = service.create_user(
        user_dto=UserDTO(
            actor_admin_id=actor.employee_id,
            client_id=client.client_id,
            first_name="New User",
            roles={2},
        )
    )
    assert result.employee_id > 0
    assert result.client_id == client.client_id
    assert result.roles == frozenset({2})


def test_create_user_rejects_disabled_client_and_taken_login() -> None:
    uow = FakeUnitOfWork()
    actor, client = setup(uow)
    client.disable()
    service = UserApplicationService(uow)
    with pytest.raises(DomainOperationError, match="disabled client"):
        service.create_user(user_dto=UserDTO(actor_admin_id=actor.employee_id, client_id=client.client_id, first_name="User"))
    client.enable()
    existing = User.create(employee_id=20, first_name="Existing", client_id=100, login="taken", password="Strong1!")
    uow.users.save(existing)
    with pytest.raises(DomainOperationError, match="already exists"):
        service.create_user(user_dto=UserDTO(actor_admin_id=actor.employee_id, client_id=100, first_name="User", login="taken", password="Strong2!"))


def test_update_requires_enabled_client_and_user() -> None:
    uow = FakeUnitOfWork()
    actor, client = setup(uow)
    user = User.create(employee_id=20, first_name="Old", client_id=100)
    uow.users.save(user)
    service = UserApplicationService(uow)
    result = service.update_user(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20, first_name="New"))
    assert result.first_name == "New"
    user.disable()
    with pytest.raises(DomainOperationError, match="disabled user"):
        service.update_user(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20, first_name="Again"))


def test_account_management_and_enable_disable() -> None:
    uow = FakeUnitOfWork()
    actor, client = setup(uow)
    user = User.create(employee_id=20, first_name="User", client_id=100)
    uow.users.save(user)
    service = UserApplicationService(uow)
    assert service.attach_account(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20, login="user", password="Strong1!")).login == "user"
    service.change_password(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20, password="Better2!"))
    assert user.account.verify_password("Better2!")
    assert service.detach_account(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20, client_id=100)).login == ""
    assert service.disable(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20)).enabled is False
    assert service.enable(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20)).enabled is True


def test_enable_rejects_disabled_client() -> None:
    uow = FakeUnitOfWork()
    actor, client = setup(uow)
    user = User.create(employee_id=20, first_name="User", client_id=100, enabled=False)
    uow.users.save(user)
    client.disable()
    with pytest.raises(DomainOperationError):
        UserApplicationService(uow).enable(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20))


def test_grant_and_revoke_user_role() -> None:
    uow = FakeUnitOfWork()
    actor, _ = setup(uow)
    role = Role(role_id=2, name="view", permissions=frozenset({UserPermission.TICKET_VIEW}))
    uow.roles_user.save(role)
    user = User.create(employee_id=20, first_name="User", client_id=100)
    uow.users.save(user)
    service = UserApplicationService(uow)
    assert service.grant_role(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20, roles={2})).roles == frozenset({2})
    assert service.revoke_role(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20, roles={2})).roles == frozenset()


def test_delete_rejects_ticket_user_reference() -> None:
    uow = FakeUnitOfWork()
    actor, _ = setup(uow)
    user = User.create(employee_id=20, first_name="User", client_id=100)
    uow.users.save(user)
    tu = TicketUser.create(client_id=100, user_id=20, text_of_ticket="x")
    tu.ticket_id = 1000
    uow.user_tickets.save(tu)
    with pytest.raises(DomainOperationError, match="has tickets"):
        UserApplicationService(uow).delete(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20))


def test_delete_without_references_removes_user() -> None:
    uow = FakeUnitOfWork()
    actor, _ = setup(uow)
    user = User.create(employee_id=20, first_name="User", client_id=100)
    uow.users.save(user)
    UserApplicationService(uow).delete(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20))
    assert 20 not in uow.users.items


def test_user_queries() -> None:
    uow = FakeUnitOfWork()
    actor, _ = setup(uow)
    u1 = User.create(employee_id=20, first_name="One", client_id=100, login="one", password="Strong1!")
    u2 = User.create(employee_id=21, first_name="Two", client_id=101)
    uow.users.save(u1)
    uow.users.save(u2)
    service = UserApplicationService(uow)
    assert service.get_by_id(user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=20)).employee_id == 20
    assert len(service.get_all(user_dto=UserDTO(actor_admin_id=actor.employee_id))) == 2
    assert [x.employee_id for x in service.get_by_client_id(user_dto=UserDTO(actor_admin_id=actor.employee_id, client_id=100))] == [20]
    assert service.find_by_login(user_dto=UserDTO(actor_admin_id=actor.employee_id, login="one")).employee_id == 20
    with pytest.raises(DomainOperationError, match="Login is required"):
        service.find_by_login(user_dto=UserDTO(actor_admin_id=actor.employee_id))


def test_delete_rejects_internal_ticket_reference_even_without_ticket_user() -> None:
    uow = FakeUnitOfWork()
    actor, _ = setup(uow)
    user = User.create(employee_id=20, first_name="User", client_id=100)
    uow.users.save(user)
    ticket = Ticket.create(
        client_id=100,
        admin_id=actor.employee_id,
        user_id=0,
        contact_user_id=user.employee_id,
        text_of_ticket="Phone request",
    )
    ticket.ticket_id = 2000
    uow.tickets.save(ticket)

    with pytest.raises(DomainOperationError, match="has tickets"):
        UserApplicationService(uow).delete(
            user_dto=UserDTO(actor_admin_id=actor.employee_id, employee_id=user.employee_id)
        )
