from __future__ import annotations

import pytest

from src.application.dto.roles_dto import RoleDTO
from src.application.services.role_service import AdminRoleService, UserRoleService
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role
from tests_pyramid.support.fakes import FakeUnitOfWork

pytestmark = pytest.mark.unit


def setup_actor(uow: FakeUnitOfWork) -> Admin:
    actor_role = Role(role_id=99, name="manager", permissions=frozenset({AdminPermission.ADMIN_OPERATION}))
    uow.roles_admin.save(actor_role)
    actor = Admin.create(employee_id=10, first_name="Actor", roles={99})
    uow.admins.save(actor)
    return actor


def test_create_admin_role_and_user_role() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    admin_result = AdminRoleService(uow).create_role(role_dto=RoleDTO(
        actor_admin_id=actor.employee_id,
        name="  tickets  ",
        permissions=frozenset({AdminPermission.TICKET_VIEW}),
        description="  desc  ",
    ))
    user_result = UserRoleService(uow).create_role(role_dto=RoleDTO(
        actor_admin_id=actor.employee_id,
        name="user tickets",
        permissions=frozenset({UserPermission.TICKET_VIEW}),
    ))
    assert admin_result.name == "tickets" and admin_result.description == "desc"
    assert user_result.permissions == frozenset({UserPermission.TICKET_VIEW})
    assert admin_result.role_id > 0 and user_result.role_id > 0


@pytest.mark.parametrize("name,permissions", [("   ", frozenset({AdminPermission.TICKET_VIEW})), ("x", frozenset())])
def test_create_role_validates_name_and_permissions(name, permissions) -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    with pytest.raises(DomainOperationError):
        AdminRoleService(uow).create_role(role_dto=RoleDTO(actor_admin_id=actor.employee_id, name=name, permissions=permissions))


def test_create_role_rejects_mixed_permission_realm() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    with pytest.raises(DomainOperationError, match="Cannot mix permission types"):
        AdminRoleService(uow).create_role(role_dto=RoleDTO(
            actor_admin_id=actor.employee_id,
            name="bad",
            permissions=frozenset({UserPermission.TICKET_VIEW}),  # type: ignore[arg-type]
        ))


def test_get_and_get_all_roles() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    role = Role(role_id=1, name="r", permissions=frozenset({AdminPermission.TICKET_VIEW}))
    uow.roles_admin.save(role)
    service = AdminRoleService(uow)
    assert service.get_role(role_dto=RoleDTO(actor_admin_id=actor.employee_id, role_id=1)).name == "r"
    ids = {r.role_id for r in service.get_all_roles(role_dto=RoleDTO(actor_admin_id=actor.employee_id))}
    assert ids == {1, 99}


def test_delete_role_rejects_invalid_id_system_and_assigned() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow); service = AdminRoleService(uow)
    with pytest.raises(DomainOperationError):
        service.delete_role(role_dto=RoleDTO(actor_admin_id=actor.employee_id, role_id=0))

    system = Role(role_id=1, name="system", permissions=frozenset({AdminPermission.TICKET_VIEW}), is_system_role=True)
    uow.roles_admin.save(system)
    with pytest.raises(DomainOperationError, match="system role"):
        service.delete_role(role_dto=RoleDTO(actor_admin_id=actor.employee_id, role_id=1))

    normal = Role(role_id=2, name="normal", permissions=frozenset({AdminPermission.TICKET_VIEW}))
    uow.roles_admin.save(normal)
    uow.roles_admin.assigned_role_ids.add(2)
    with pytest.raises(DomainOperationError, match="assigned"):
        service.delete_role(role_dto=RoleDTO(actor_admin_id=actor.employee_id, role_id=2))


def test_delete_unassigned_role() -> None:
    uow = FakeUnitOfWork(); actor = setup_actor(uow)
    uow.roles_admin.save(Role(role_id=1, name="normal", permissions=frozenset({AdminPermission.TICKET_VIEW})))
    AdminRoleService(uow).delete_role(role_dto=RoleDTO(actor_admin_id=actor.employee_id, role_id=1))
    assert 1 not in uow.roles_admin.items


def test_role_service_requires_authorized_admin() -> None:
    uow = FakeUnitOfWork()
    actor = Admin.create(employee_id=10, first_name="Actor")
    uow.admins.save(actor)
    with pytest.raises(PermissionError):
        AdminRoleService(uow).get_all_roles(role_dto=RoleDTO(actor_admin_id=actor.employee_id))
