from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.application.dto.employee_dto import AdminDTO
from src.application.services.admin_service import AdminApplicationService
from src.domain.client import Client
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role_new import Role
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from tests_pyramid.support.fakes import FakeUnitOfWork

pytestmark = pytest.mark.unit
BASE = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


def setup_actor(uow: FakeUnitOfWork, *, permissions=frozenset(AdminPermission)) -> Admin:
    role = Role(role_id=1, name="actor-role", permissions=permissions)
    uow.roles_admin.save(role)
    actor = Admin.create(
        employee_id=10,
        first_name="Actor",
        login="actor",
        password="Strong1!",
        roles={1},
    )
    uow.admins.save(actor)
    uow.calls.clear()
    return actor


def test_create_admin_assigns_repository_id() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    service = AdminApplicationService(uow)
    result = service.create_admin(
        admin_dto=AdminDTO(
            actor_admin_id=actor.employee_id,
            first_name="New Admin",
            job_title="Engineer",
        )
    )
    assert result.employee_id > 0
    assert result.first_name == "New Admin"
    assert result.job_title == "Engineer"


def test_create_admin_with_roles_validates_and_grants_roles() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    target_role = Role(role_id=2, name="view", permissions=frozenset({AdminPermission.TICKET_VIEW}))
    uow.roles_admin.save(target_role)
    service = AdminApplicationService(uow)
    result = service.create_admin(
        admin_dto=AdminDTO(
            actor_admin_id=actor.employee_id,
            first_name="New Admin",
            roles={2},
        )
    )
    assert result.roles == frozenset({2})


def test_create_admin_rejects_login_used_by_user() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    uow.users.save(
        User.create(
            employee_id=20,
            first_name="User",
            client_id=100,
            login="taken",
            password="Strong2!",
        )
    )
    service = AdminApplicationService(uow)
    with pytest.raises(DomainOperationError, match="already exists"):
        service.create_admin(
            admin_dto=AdminDTO(
                actor_admin_id=actor.employee_id,
                first_name="New Admin",
                login="taken",
                password="Strong3!",
            )
        )


def test_update_admin_changes_fields() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    target = Admin.create(employee_id=20, first_name="Old", job_title="Old")
    uow.admins.save(target)
    service = AdminApplicationService(uow)
    result = service.update_admin(
        admin_dto=AdminDTO(
            actor_admin_id=actor.employee_id,
            employee_id=target.employee_id,
            first_name="New",
            job_title="New title",
        )
    )
    assert result.first_name == "New"
    assert result.job_title == "New title"


def test_attach_detach_and_change_password() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    target = Admin.create(employee_id=20, first_name="Target")
    uow.admins.save(target)
    service = AdminApplicationService(uow)

    attached = service.attach_account(
        admin_dto=AdminDTO(
            actor_admin_id=actor.employee_id,
            employee_id=20,
            login="target",
            password="Strong2!",
        )
    )
    assert attached.login == "target"

    changed = service.change_password(
        admin_dto=AdminDTO(
            actor_admin_id=actor.employee_id,
            employee_id=20,
            password="Better3!",
        )
    )
    assert changed.login == "target"
    assert target.account.verify_password("Better3!")

    detached = service.detach_account(
        admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20)
    )
    assert detached.login == ""


def test_change_password_requires_nonempty_password() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    target = Admin.create(employee_id=20, first_name="Target")
    uow.admins.save(target)
    with pytest.raises(DomainOperationError, match="Password is required"):
        AdminApplicationService(uow).change_password(
            admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20)
        )


def test_grant_revoke_and_get_permissions() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    target_role = Role(role_id=2, name="view", permissions=frozenset({AdminPermission.TICKET_VIEW}))
    uow.roles_admin.save(target_role)
    target = Admin.create(employee_id=20, first_name="Target")
    uow.admins.save(target)
    service = AdminApplicationService(uow)

    granted = service.grant_role(
        admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20, roles={2})
    )
    assert granted.roles == frozenset({2})
    perms = service.get_permissions(
        admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20)
    )
    assert perms.permissions == (AdminPermission.TICKET_VIEW.value,)
    revoked = service.revoke_role(
        admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20, roles={2})
    )
    assert revoked.roles == frozenset()


def test_enable_disable_admin() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    target = Admin.create(employee_id=20, first_name="Target", login="target", password="Strong2!")
    uow.admins.save(target)
    service = AdminApplicationService(uow)
    assert service.disable(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20)).enabled is False
    assert target.account.enabled is False
    assert service.enable(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20)).enabled is True
    assert target.account.enabled is True


def test_change_department_rejects_nonpositive_disabled_and_working_ticket() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    target = Admin.create(employee_id=20, first_name="Target", department_id=1)
    uow.admins.save(target)
    disabled = Department.create(department_id=2, name="Disabled", enabled=False)
    uow.departments.save(disabled)
    service = AdminApplicationService(uow)

    with pytest.raises(DomainOperationError, match="positive"):
        service.change_department(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20, department_id=0))
    with pytest.raises(DomainOperationError, match="disabled"):
        service.change_department(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20, department_id=2))

    enabled = Department.create(department_id=3, name="Enabled")
    uow.departments.save(enabled)
    ticket = Ticket.create(client_id=100, admin_id=actor.employee_id, text_of_ticket="x", department_id=1, date_created=BASE)
    ticket.ticket_id = 1000
    TicketManagementService.accept(ticket=ticket, actor_employee_id=actor.employee_id, date_created=BASE + timedelta(minutes=1))
    TicketManagementService.assign(ticket=ticket, actor_employee_id=actor.employee_id, executor_id=target.employee_id, date_created=BASE + timedelta(minutes=2))
    ticket.append_status(TicketStatusRecord.create_at_work(actor_employee_id=target.employee_id, executor_id=target.employee_id, date_created=BASE + timedelta(minutes=3)))
    uow.tickets.save(ticket)
    with pytest.raises(DomainOperationError, match="tickets in work"):
        service.change_department(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20, department_id=3))


def test_change_and_remove_department_happy_path() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    target = Admin.create(employee_id=20, first_name="Target", department_id=1)
    uow.admins.save(target)
    uow.departments.save(Department.create(department_id=2, name="Support"))
    service = AdminApplicationService(uow)
    assert service.change_department(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20, department_id=2)).department_id == 2
    assert service.remove_department(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20)).department_id == 0


def test_delete_admin_rejects_client_ticket_and_ticket_user_references() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    target = Admin.create(employee_id=20, first_name="Target")
    uow.admins.save(target)
    service = AdminApplicationService(uow)

    uow.clients.save(Client.create(client_id=100, name="Client", created_by_admin_id=20))
    with pytest.raises(DomainOperationError, match="clients"):
        service.delete(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20))
    uow.clients.items.clear()

    ticket = Ticket.create(client_id=100, admin_id=20, text_of_ticket="x")
    ticket.ticket_id = 2000
    uow.tickets.save(ticket)
    with pytest.raises(DomainOperationError, match="tickets"):
        service.delete(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20))
    uow.tickets.items.clear()

    tu = TicketUser.create_confirmed_by_admin(client_id=100, user_id=30, actor_admin_id=20, text_of_ticket="x")
    tu.ticket_id = 3000
    uow.user_tickets.save(tu)
    with pytest.raises(DomainOperationError, match="user tickets"):
        service.delete(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20))


def test_delete_admin_without_references_removes_it() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    target = Admin.create(employee_id=20, first_name="Target")
    uow.admins.save(target)
    AdminApplicationService(uow).delete(
        admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20)
    )
    assert 20 not in uow.admins.items


def test_admin_queries_and_login_required() -> None:
    uow = FakeUnitOfWork()
    actor = setup_actor(uow)
    target = Admin.create(employee_id=20, first_name="Target", login="target", password="Strong2!")
    uow.admins.save(target)
    service = AdminApplicationService(uow)
    assert service.get_by_id(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, employee_id=20)).employee_id == 20
    assert {dto.employee_id for dto in service.get_all(admin_dto=AdminDTO(actor_admin_id=actor.employee_id))} == {10, 20}
    assert service.find_by_login(admin_dto=AdminDTO(actor_admin_id=actor.employee_id, login="target")).employee_id == 20
    with pytest.raises(DomainOperationError, match="Login is required"):
        service.find_by_login(admin_dto=AdminDTO(actor_admin_id=actor.employee_id))
