from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.application.assemblers.assembler import (
    AdminAssembler,
    ClientAssembler,
    DepartmentAssembler,
    PermissionAssembler,
    RoleAssembler,
    TicketAssembler,
    TicketUserAssembler,
    UserAssembler,
)
from src.application.helper.actor_helper import EmployeeActorHelper
from src.application.helper.employee_helper import EmployeeHelper
from src.domain.client import Client
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role
from src.domain.ticket import Comment, Ticket
from src.domain.ticket_user import TicketUser
from tests_pyramid.support.fakes import FakeUnitOfWork

pytestmark = pytest.mark.unit
BASE = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


def prepare_admin_actor(uow: FakeUnitOfWork, *, enabled: bool = True) -> Admin:
    role = Role(
        role_id=1,
        name="admin-role",
        permissions=frozenset({AdminPermission.ADMIN_OPERATION}),
    )
    uow.roles_admin.save(role)
    actor = Admin.create(employee_id=10, first_name="Actor", roles={1}, enabled=enabled)
    uow.admins.save(actor)
    return actor


def prepare_user_actor(uow: FakeUnitOfWork, *, enabled: bool = True) -> User:
    role = Role(
        role_id=2,
        name="user-role",
        permissions=frozenset({UserPermission.TICKET_OPERATION}),
    )
    uow.roles_user.save(role)
    actor = User.create(employee_id=20, first_name="User", client_id=100, roles={2}, enabled=enabled)
    uow.users.save(actor)
    return actor


def test_actor_helper_returns_authorized_admin_and_user() -> None:
    uow = FakeUnitOfWork()
    admin = prepare_admin_actor(uow)
    user = prepare_user_actor(uow)
    helper = EmployeeActorHelper(uow)
    assert helper.require_actor_admin(actor_admin_id=admin.employee_id, permission=AdminPermission.ADMIN_OPERATION) is admin
    assert helper.require_actor_user(actor_user_id=user.employee_id, permission=UserPermission.TICKET_OPERATION) is user


def test_actor_helper_rejects_disabled_or_missing_permission() -> None:
    uow = FakeUnitOfWork()
    actor = prepare_admin_actor(uow)
    helper = EmployeeActorHelper(uow)
    with pytest.raises(PermissionError):
        helper.require_actor_admin(actor_admin_id=actor.employee_id, permission=AdminPermission.TICKET_VIEW)
    actor.disable()
    with pytest.raises(DomainOperationError):
        helper.require_actor_admin(actor_admin_id=actor.employee_id, permission=AdminPermission.ADMIN_OPERATION)


def test_employee_helper_login_free_and_role_manager_realms() -> None:
    uow = FakeUnitOfWork()
    existing = User.create(employee_id=20, first_name="User", client_id=1, login="taken", password="Strong1!")
    uow.users.save(existing)
    helper = EmployeeHelper(uow)
    with pytest.raises(DomainOperationError):
        helper.ensure_login_is_free(login="taken")
    helper.ensure_login_is_free(login="free")
    assert helper.get_role_manager_admin()._roles is uow.roles_admin
    assert helper.get_role_manager_user()._roles is uow.roles_user


def test_client_department_admin_user_role_assemblers() -> None:
    client = Client.create(client_id=1, name="Acme", created_by_admin_id=10)
    department = Department.create(department_id=2, name="Support")
    admin = Admin.create(employee_id=10, first_name="Admin", job_title="Dev", department_id=2)
    user = User.create(employee_id=20, first_name="User", client_id=1)
    role = Role(role_id=3, name="view", permissions=frozenset({AdminPermission.TICKET_VIEW}), description="desc")

    assert ClientAssembler.to_dto(client).created_by_admin == 10
    assert DepartmentAssembler.to_dto(department).name == "Support"
    assert AdminAssembler.to_dto(admin).department_id == 2
    assert UserAssembler.to_dto(user).client_id == 1
    assert RoleAssembler.to_dto(role).permissions == role.permissions


def test_permission_assembler_sorts_stable_permission_values() -> None:
    dto = PermissionAssembler.to_admin_dto(
        frozenset({AdminPermission.TICKET_VIEW, AdminPermission.ADMIN_OPERATION})
    )
    assert dto.permissions == tuple(sorted(dto.permissions))
    assert set(dto.permissions) == {"ticket.view", "admin.operation"}


def test_ticket_assembler_preserves_creator_status_payload_and_comments() -> None:
    ticket = Ticket.create(
        client_id=1,
        admin_id=10,
        text_of_ticket="Need help",
        description="desc",
        comment="initial",
        date_created=BASE,
    )
    ticket.ticket_id = 100
    dto = TicketAssembler.to_dto(ticket)
    assert dto.ticket_id == 100
    assert dto.admin_id == 10
    assert dto.date_finished is None
    assert dto.statuses[0]["status"] == "created"
    assert dto.statuses[0]["actor_id"] == 10
    assert dto.comments[0]["comment"] == "initial"


def test_ticket_user_assembler_uses_status_comment_and_none_date_finished() -> None:
    ticket_user = TicketUser.create(
        client_id=1,
        user_id=20,
        text_of_ticket="Need help",
        date_created=BASE,
    )
    ticket_user.ticket_id = 200
    ticket_user.confirm_by_admin(actor_employee_id=10, comment="accepted")
    dto = TicketUserAssembler.to_dto(ticket_user)
    assert dto.ticket_id == 200
    assert dto.current_status == "confirmed_by_admin"
    assert dto.date_finished is None
    assert dto.statuses[-1]["status_comment"] == "accepted"
