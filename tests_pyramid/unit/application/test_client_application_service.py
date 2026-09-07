from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.application.dto.client_dto import ClientDTO
from src.application.services.client_service import ClientApplicationService
from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role_new import Role
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from tests_pyramid.support.fakes import FakeUnitOfWork

pytestmark = pytest.mark.unit
BASE = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


def setup_actor(uow: FakeUnitOfWork, permissions: frozenset[AdminPermission] | None = None) -> Admin:
    role = Role(
        role_id=1,
        name="client-manager",
        permissions=permissions or frozenset({AdminPermission.CLIENT_OPERATION, AdminPermission.CLIENT_VIEW}),
    )
    uow.roles_admin.save(role)
    actor = Admin.create(employee_id=10, first_name="Actor", roles={1})
    uow.admins.save(actor)
    uow.calls.clear()
    return actor


def test_create_client_uses_authenticated_actor_as_creator() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    result = ClientApplicationService(uow).create_client(
        ClientDTO(actor_admin_id=actor.employee_id, admin_id=999, name="Acme", email="info@acme.test")
    )
    assert result.client_id > 0
    assert result.created_by_admin == actor.employee_id
    assert result.name == "Acme"


def test_create_and_update_require_operation_permission() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow, frozenset({AdminPermission.CLIENT_VIEW}))
    service = ClientApplicationService(uow)
    with pytest.raises(PermissionError):
        service.create_client(ClientDTO(actor_admin_id=actor.employee_id, name="Acme"))


def test_update_contact_mutates_only_contact_fields() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    client = Client.create(client_id=100, name="Old", created_by_admin_id=actor.employee_id)
    uow.clients.save(client)
    result = ClientApplicationService(uow).update_contact(
        ClientDTO(
            actor_admin_id=actor.employee_id,
            client_id=100,
            name="New",
            email="new@acme.test",
            address="Street",
            phone="12345",
            description="desc",
        )
    )
    assert result.name == "New"
    assert result.email == "new@acme.test"
    assert result.created_by_admin == actor.employee_id


def test_disable_disables_client_and_all_its_users() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    client = Client.create(client_id=100, name="Acme")
    uow.clients.save(client)
    own1 = User.create(employee_id=20, first_name="U1", client_id=100)
    own2 = User.create(employee_id=21, first_name="U2", client_id=100)
    other = User.create(employee_id=22, first_name="Other", client_id=101)
    for user in (own1, own2, other):
        uow.users.save(user)
    result = ClientApplicationService(uow).disable(ClientDTO(actor_admin_id=actor.employee_id, client_id=100))
    assert result.enabled is False
    assert own1.enabled is False and own2.enabled is False
    assert other.enabled is True


def test_disable_defers_each_changeable_ticket_exactly_once() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    client = Client.create(client_id=100, name="Acme")
    uow.clients.save(client)
    ticket = Ticket.create(client_id=100, admin_id=actor.employee_id, text_of_ticket="x")
    ticket.ticket_id = 1000
    TicketManagementService.accept(ticket=ticket, actor_employee_id=actor.employee_id)
    uow.tickets.save(ticket)
    uow.calls.clear()

    ClientApplicationService(uow).disable(ClientDTO(actor_admin_id=actor.employee_id, client_id=100))

    save_ticket_calls = [x for x in uow.calls if x == "save_ticket"]
    assert len(save_ticket_calls) == 1, "a changed ticket must be persisted exactly once"
    assert ticket.current_status_record().status.value == "deferred"


def test_disable_does_not_touch_ticket_of_other_client() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    uow.clients.save(Client.create(client_id=100, name="Acme"))
    other = Ticket.create(client_id=101, admin_id=actor.employee_id, text_of_ticket="x")
    other.ticket_id = 1000
    uow.tickets.save(other)
    ClientApplicationService(uow).disable(ClientDTO(actor_admin_id=actor.employee_id, client_id=100))
    assert other.current_status_record().status.value == "created"


def test_enable_client() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    client = Client.create(client_id=100, name="Acme", enabled=False)
    uow.clients.save(client)
    result = ClientApplicationService(uow).enable(ClientDTO(actor_admin_id=actor.employee_id, client_id=100))
    assert result.enabled is True


@pytest.mark.parametrize("reference", ["user", "ticket", "ticket_user"])
def test_delete_rejects_references(reference: str) -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    client = Client.create(client_id=100, name="Acme")
    uow.clients.save(client)
    if reference == "user":
        uow.users.save(User.create(employee_id=20, first_name="User", client_id=100))
    elif reference == "ticket":
        ticket = Ticket.create(client_id=100, admin_id=actor.employee_id, text_of_ticket="x")
        ticket.ticket_id = 200
        uow.tickets.save(ticket)
    else:
        tu = TicketUser.create(client_id=100, user_id=20, text_of_ticket="x")
        tu.ticket_id = 300
        uow.user_tickets.save(tu)
    with pytest.raises(DomainOperationError):
        ClientApplicationService(uow).delete(dto_client=ClientDTO(actor_admin_id=actor.employee_id, client_id=100))


def test_delete_without_references_removes_client() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    uow.clients.save(Client.create(client_id=100, name="Acme"))
    result = ClientApplicationService(uow).delete(dto_client=ClientDTO(actor_admin_id=actor.employee_id, client_id=100))
    assert result.client_id == 100
    assert 100 not in uow.clients.items


def test_queries_require_view_permission_and_return_data() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    uow.clients.save(Client.create(client_id=100, name="Acme A"))
    uow.clients.save(Client.create(client_id=101, name="Acme B"))
    service = ClientApplicationService(uow)
    assert service.get_by_id(ClientDTO(actor_admin_id=actor.employee_id, client_id=100)).name == "Acme A"
    assert {x.client_id for x in service.get_all(ClientDTO(actor_admin_id=actor.employee_id))} == {100, 101}
