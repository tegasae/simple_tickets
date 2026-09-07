from __future__ import annotations

import pytest

from src.application.dto.department_dto import DepartmentDTO
from src.application.services.department_service import DepartmentApplicationService
from src.domain.department import Department
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission
from src.domain.rbac.role_new import Role
from src.domain.ticket import Ticket
from tests_pyramid.support.fakes import FakeUnitOfWork

pytestmark = pytest.mark.unit


def setup_actor(uow: FakeUnitOfWork) -> Admin:
    role = Role(role_id=1, name="dept", permissions=frozenset({AdminPermission.ADMIN_OPERATION}))
    uow.roles_admin.save(role)
    actor = Admin.create(employee_id=10, first_name="Actor", roles={1})
    uow.admins.save(actor)
    uow.calls.clear()
    return actor


def test_create_department_assigns_id_and_payload() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    result = DepartmentApplicationService(uow).create_department(
        department_dto=DepartmentDTO(actor_admin_id=actor.employee_id, name="Support", enabled=True)
    )
    assert result.department_id > 0 and result.name == "Support" and result.enabled is True


def test_update_department_renames_only() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    uow.departments.save(Department.create(department_id=100, name="Old", enabled=True))
    result = DepartmentApplicationService(uow).update_department(
        department_dto=DepartmentDTO(actor_admin_id=actor.employee_id, department_id=100, name="New")
    )
    assert result.name == "New" and result.enabled is True


def test_enable_department() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    uow.departments.save(Department.create(department_id=100, name="Dept", enabled=False))
    assert DepartmentApplicationService(uow).enable_department(
        department_dto=DepartmentDTO(actor_admin_id=actor.employee_id, department_id=100)
    ).enabled is True


def test_disable_department_without_admins() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    uow.departments.save(Department.create(department_id=100, name="Dept", enabled=True))
    result = DepartmentApplicationService(uow).disable_department(
        department_dto=DepartmentDTO(actor_admin_id=actor.employee_id, department_id=100)
    )
    assert result.enabled is False


def test_disable_department_rejects_assigned_admin() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    uow.departments.save(Department.create(department_id=100, name="Dept", enabled=True))
    uow.admins.save(Admin.create(employee_id=20, first_name="Target", department_id=100))
    with pytest.raises(DomainOperationError):
        DepartmentApplicationService(uow).disable_department(
            department_dto=DepartmentDTO(actor_admin_id=actor.employee_id, department_id=100)
        )


@pytest.mark.parametrize("reference", ["admin", "ticket"])
def test_delete_department_rejects_references(reference: str) -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    uow.departments.save(Department.create(department_id=100, name="Dept"))
    if reference == "admin":
        uow.admins.save(Admin.create(employee_id=20, first_name="Target", department_id=100))
    else:
        ticket = Ticket.create(client_id=1, admin_id=actor.employee_id, text_of_ticket="x", department_id=100)
        ticket.ticket_id = 200
        uow.tickets.save(ticket)
    with pytest.raises(DomainOperationError):
        DepartmentApplicationService(uow).delete_department(
            department_dto=DepartmentDTO(actor_admin_id=actor.employee_id, department_id=100)
        )


def test_delete_department_without_references() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    uow.departments.save(Department.create(department_id=100, name="Dept"))
    DepartmentApplicationService(uow).delete_department(
        department_dto=DepartmentDTO(actor_admin_id=actor.employee_id, department_id=100)
    )
    assert 100 not in uow.departments.items


def test_department_queries() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    uow.departments.save(Department.create(department_id=100, name="Dept A"))
    uow.departments.save(Department.create(department_id=101, name="Dept B"))
    service = DepartmentApplicationService(uow)
    assert service.get_by_id(department_dto=DepartmentDTO(actor_admin_id=actor.employee_id, department_id=100)).name == "Dept A"
    assert {x.department_id for x in service.get_all(department_dto=DepartmentDTO(actor_admin_id=actor.employee_id))} == {100, 101}


def test_department_operations_require_admin_operation_permission() -> None:
    uow = FakeUnitOfWork()
    actor = Admin.create(employee_id=10, first_name="Actor")
    uow.admins.save(actor)
    with pytest.raises(PermissionError):
        DepartmentApplicationService(uow).create_department(
            department_dto=DepartmentDTO(actor_admin_id=10, name="Dept")
        )
