# tests/application/services/test_role_service.py

from __future__ import annotations

from typing import Generic, TypeVar

import pytest

import src.application.services.role_service as role_service_module

from src.application.dto.roles_dto import RoleDTO, RoleResponseDTO
from src.application.services.role_service import AdminRoleService, UserRoleService
from src.domain.exceptions import DomainOperationError, ItemNotFoundError
from src.domain.rbac.permissions import (
    AdminPermission,
    PermissionBase,
    UserPermission,
)
from src.domain.rbac.role_new import Role


P = TypeVar("P", bound=PermissionBase)


# ---------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------

class FakeRoleRepository(Generic[P]):
    def __init__(self):
        self.items: dict[int, Role[P]] = {}
        self.assigned_role_ids: set[int] = set()
        self.next_id = 1

    def add(self, role: Role[P]) -> Role[P]:
        saved_role = Role(
            role_id=self.next_id,
            name=role.name,
            permissions=role.permissions,
            description=role.description,
            is_system_role=role.is_system_role,
            date_created=role.date_created,
            version=role.version,
        )

        self.items[saved_role.role_id] = saved_role
        self.next_id += 1

        return saved_role

    def get(self, role_id: int) -> Role[P]:
        role = self.items.get(role_id)

        if role is None:
            raise ItemNotFoundError(f"The role {role_id} not found")

        return role

    def all(self) -> list[Role[P]]:
        return list(self.items.values())

    def delete(self, role_id: int) -> None:
        if role_id not in self.items:
            raise ItemNotFoundError(f"The role {role_id} not found")

        del self.items[role_id]

    def is_assigned(self, role_id: int) -> bool:
        return role_id in self.assigned_role_ids


class FakeUnitOfWork:
    def __init__(self):
        self.roles_admin = FakeRoleRepository[AdminPermission]()
        self.roles_user = FakeRoleRepository[UserPermission]()

        self.entered = False
        self.exited = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.exited = True
        return False


class FakeEmployeeActorHelper:
    allowed_admin_ids: set[int] = {1}

    def __init__(self, uow):
        self.uow = uow

    def require_actor_admin(
        self,
        *,
        actor_admin_id: int,
        permission: AdminPermission,
    ) -> None:
        if actor_admin_id not in self.allowed_admin_ids:
            raise PermissionError(
                f"Admin {actor_admin_id} does not have permission {permission}"
            )


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_actor_helper(monkeypatch):
    FakeEmployeeActorHelper.allowed_admin_ids = {1}

    monkeypatch.setattr(
        role_service_module,
        "EmployeeActorHelper",
        FakeEmployeeActorHelper,
    )


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def admin_role_service(uow: FakeUnitOfWork) -> AdminRoleService:
    return AdminRoleService(uow)


@pytest.fixture
def user_role_service(uow: FakeUnitOfWork) -> UserRoleService:
    return UserRoleService(uow)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def admin_create_dto(
    *,
    actor_admin_id: int = 1,
    name: str = "Admin operator",
    permissions: frozenset[AdminPermission] | None = None,
    description: str = "Admin role",
    is_system_role: bool = False,
) -> RoleDTO[AdminPermission]:
    return RoleDTO[AdminPermission](
        actor_admin_id=actor_admin_id,
        name=name,
        permissions=permissions
        if permissions is not None
        else frozenset({AdminPermission.ADMIN_OPERATION}),
        description=description,
        is_system_role=is_system_role,
    )


def user_create_dto(
    *,
    actor_admin_id: int = 1,
    name: str = "User operator",
    permissions: frozenset[UserPermission] | None = None,
    description: str = "User role",
    is_system_role: bool = False,
) -> RoleDTO[UserPermission]:
    return RoleDTO[UserPermission](
        actor_admin_id=actor_admin_id,
        name=name,
        permissions=permissions
        if permissions is not None
        else frozenset({UserPermission.TICKET_VIEW}),
        description=description,
        is_system_role=is_system_role,
    )


def admin_id_dto(
    *,
    actor_admin_id: int = 1,
    role_id: int,
) -> RoleDTO[AdminPermission]:
    return RoleDTO[AdminPermission](
        actor_admin_id=actor_admin_id,
        role_id=role_id,
    )


def user_id_dto(
    *,
    actor_admin_id: int = 1,
    role_id: int,
) -> RoleDTO[UserPermission]:
    return RoleDTO[UserPermission](
        actor_admin_id=actor_admin_id,
        role_id=role_id,
    )


def admin_list_dto(
    *,
    actor_admin_id: int = 1,
) -> RoleDTO[AdminPermission]:
    return RoleDTO[AdminPermission](
        actor_admin_id=actor_admin_id,
    )


def user_list_dto(
    *,
    actor_admin_id: int = 1,
) -> RoleDTO[UserPermission]:
    return RoleDTO[UserPermission](
        actor_admin_id=actor_admin_id,
    )


# ---------------------------------------------------------------------
# Admin role service tests
# ---------------------------------------------------------------------

def test_create_admin_role_success(
    admin_role_service: AdminRoleService,
):
    dto = admin_create_dto(
        name="Administrators",
        permissions=frozenset({
            AdminPermission.ADMIN_OPERATION,
        }),
        description="Full admin role",
    )

    response = admin_role_service.create_role(
        role_dto=dto,
    )

    assert isinstance(response, RoleResponseDTO)
    assert response.role_id == 1
    assert response.name == "Administrators"
    assert response.permissions == frozenset({
        AdminPermission.ADMIN_OPERATION,
    })
    assert response.description == "Full admin role"
    assert response.is_system_role is False


def test_create_admin_role_strips_name_and_description(
    admin_role_service: AdminRoleService,
):
    dto = admin_create_dto(
        name="  Administrators  ",
        description="  Admin role  ",
    )

    response = admin_role_service.create_role(
        role_dto=dto,
    )

    assert response.name == "Administrators"
    assert response.description == "Admin role"


def test_create_admin_role_empty_name_raises(
    admin_role_service: AdminRoleService,
):
    dto = admin_create_dto(
        name="   ",
    )

    with pytest.raises(DomainOperationError, match="Role name must not be empty"):
        admin_role_service.create_role(
            role_dto=dto,
        )


def test_create_admin_role_empty_permissions_raises(
    admin_role_service: AdminRoleService,
):
    dto = admin_create_dto(
        permissions=frozenset(),
    )

    with pytest.raises(DomainOperationError, match="Role must have at least one permission"):
        admin_role_service.create_role(
            role_dto=dto,
        )


def test_create_admin_role_with_user_permission_raises(
    admin_role_service: AdminRoleService,
):
    dto: RoleDTO[AdminPermission] = RoleDTO(
        actor_admin_id=1,
        name="Wrong admin role",
        permissions=frozenset({
            UserPermission.TICKET_VIEW,
        }),
    )

    with pytest.raises(DomainOperationError, match="Cannot mix permission types"):
        admin_role_service.create_role(
            role_dto=dto,
        )


def test_get_admin_role_success(
    admin_role_service: AdminRoleService,
):
    created = admin_role_service.create_role(
        role_dto=admin_create_dto(name="Administrators"),
    )

    response = admin_role_service.get_role(
        role_dto=admin_id_dto(role_id=created.role_id),
    )

    assert response.role_id == created.role_id
    assert response.name == "Administrators"
    assert response.permissions == created.permissions


def test_get_admin_role_with_invalid_id_raises(
    admin_role_service: AdminRoleService,
):
    with pytest.raises(DomainOperationError, match="Role id must be positive"):
        admin_role_service.get_role(
            role_dto=admin_id_dto(role_id=0),
        )


def test_get_admin_role_not_found_raises(
    admin_role_service: AdminRoleService,
):
    with pytest.raises(ItemNotFoundError):
        admin_role_service.get_role(
            role_dto=admin_id_dto(role_id=999),
        )


def test_get_all_admin_roles_success(
    admin_role_service: AdminRoleService,
):
    first = admin_role_service.create_role(
        role_dto=admin_create_dto(name="First admin role"),
    )
    second = admin_role_service.create_role(
        role_dto=admin_create_dto(name="Second admin role"),
    )

    responses = admin_role_service.get_all_roles(
        role_dto=admin_list_dto(),
    )

    assert [role.role_id for role in responses] == [
        first.role_id,
        second.role_id,
    ]
    assert [role.name for role in responses] == [
        "First admin role",
        "Second admin role",
    ]


def test_delete_admin_role_success(
    admin_role_service: AdminRoleService,
    uow: FakeUnitOfWork,
):
    created = admin_role_service.create_role(
        role_dto=admin_create_dto(name="Temporary role"),
    )

    admin_role_service.delete_role(
        role_dto=admin_id_dto(role_id=created.role_id),
    )

    assert created.role_id not in uow.roles_admin.items


def test_delete_admin_role_with_invalid_id_raises(
    admin_role_service: AdminRoleService,
):
    with pytest.raises(DomainOperationError, match="Role id must be positive"):
        admin_role_service.delete_role(
            role_dto=admin_id_dto(role_id=0),
        )


def test_delete_system_admin_role_raises(
    admin_role_service: AdminRoleService,
    uow: FakeUnitOfWork,
):
    system_role = admin_role_service.create_role(
        role_dto=admin_create_dto(
            name="System admin role",
            is_system_role=True,
        ),
    )

    with pytest.raises(DomainOperationError, match="Cannot delete system role"):
        admin_role_service.delete_role(
            role_dto=admin_id_dto(role_id=system_role.role_id),
        )

    assert system_role.role_id in uow.roles_admin.items


def test_delete_assigned_admin_role_raises(
    admin_role_service: AdminRoleService,
    uow: FakeUnitOfWork,
):
    created = admin_role_service.create_role(
        role_dto=admin_create_dto(name="Assigned admin role"),
    )

    uow.roles_admin.assigned_role_ids.add(created.role_id)

    with pytest.raises(DomainOperationError, match="cannot be deleted because it is assigned"):
        admin_role_service.delete_role(
            role_dto=admin_id_dto(role_id=created.role_id),
        )

    assert created.role_id in uow.roles_admin.items


def test_admin_actor_without_permission_raises(
    admin_role_service: AdminRoleService,
):
    dto = admin_create_dto(
        actor_admin_id=999,
        name="Forbidden role",
    )

    with pytest.raises(PermissionError):
        admin_role_service.create_role(
            role_dto=dto,
        )


# ---------------------------------------------------------------------
# User role service tests
# ---------------------------------------------------------------------

def test_create_user_role_success(
    user_role_service: UserRoleService,
):
    dto = user_create_dto(
        name="Client users",
        permissions=frozenset({
            UserPermission.TICKET_VIEW,
        }),
        description="User role",
    )

    response = user_role_service.create_role(
        role_dto=dto,
    )

    assert isinstance(response, RoleResponseDTO)
    assert response.role_id == 1
    assert response.name == "Client users"
    assert response.permissions == frozenset({
        UserPermission.TICKET_VIEW,
    })
    assert response.description == "User role"
    assert response.is_system_role is False


def test_create_user_role_empty_name_raises(
    user_role_service: UserRoleService,
):
    dto = user_create_dto(
        name="",
    )

    with pytest.raises(DomainOperationError, match="Role name must not be empty"):
        user_role_service.create_role(
            role_dto=dto,
        )


def test_create_user_role_empty_permissions_raises(
    user_role_service: UserRoleService,
):
    dto = user_create_dto(
        permissions=frozenset(),
    )

    with pytest.raises(DomainOperationError, match="Role must have at least one permission"):
        user_role_service.create_role(
            role_dto=dto,
        )


def test_create_user_role_with_admin_permission_raises(
    user_role_service: UserRoleService,
):
    dto: RoleDTO[UserPermission] = RoleDTO(
        actor_admin_id=1,
        name="Wrong user role",
        permissions=frozenset({
            AdminPermission.ADMIN_OPERATION,
        }),
    )

    with pytest.raises(DomainOperationError, match="Cannot mix permission types"):
        user_role_service.create_role(
            role_dto=dto,
        )


def test_get_user_role_success(
    user_role_service: UserRoleService,
):
    created = user_role_service.create_role(
        role_dto=user_create_dto(name="Client users"),
    )

    response = user_role_service.get_role(
        role_dto=user_id_dto(role_id=created.role_id),
    )

    assert response.role_id == created.role_id
    assert response.name == "Client users"
    assert response.permissions == created.permissions


def test_get_user_role_with_invalid_id_raises(
    user_role_service: UserRoleService,
):
    with pytest.raises(DomainOperationError, match="Role id must be positive"):
        user_role_service.get_role(
            role_dto=user_id_dto(role_id=0),
        )


def test_get_user_role_not_found_raises(
    user_role_service: UserRoleService,
):
    with pytest.raises(ItemNotFoundError):
        user_role_service.get_role(
            role_dto=user_id_dto(role_id=999),
        )


def test_get_all_user_roles_success(
    user_role_service: UserRoleService,
):
    first = user_role_service.create_role(
        role_dto=user_create_dto(name="First user role"),
    )
    second = user_role_service.create_role(
        role_dto=user_create_dto(name="Second user role"),
    )

    responses = user_role_service.get_all_roles(
        role_dto=user_list_dto(),
    )

    assert [role.role_id for role in responses] == [
        first.role_id,
        second.role_id,
    ]
    assert [role.name for role in responses] == [
        "First user role",
        "Second user role",
    ]


def test_delete_user_role_success(
    user_role_service: UserRoleService,
    uow: FakeUnitOfWork,
):
    created = user_role_service.create_role(
        role_dto=user_create_dto(name="Temporary user role"),
    )

    user_role_service.delete_role(
        role_dto=user_id_dto(role_id=created.role_id),
    )

    assert created.role_id not in uow.roles_user.items


def test_delete_user_role_with_invalid_id_raises(
    user_role_service: UserRoleService,
):
    with pytest.raises(DomainOperationError, match="Role id must be positive"):
        user_role_service.delete_role(
            role_dto=user_id_dto(role_id=0),
        )


def test_delete_system_user_role_raises(
    user_role_service: UserRoleService,
    uow: FakeUnitOfWork,
):
    system_role = user_role_service.create_role(
        role_dto=user_create_dto(
            name="System user role",
            is_system_role=True,
        ),
    )

    with pytest.raises(DomainOperationError, match="Cannot delete system role"):
        user_role_service.delete_role(
            role_dto=user_id_dto(role_id=system_role.role_id),
        )

    assert system_role.role_id in uow.roles_user.items


def test_delete_assigned_user_role_raises(
    user_role_service: UserRoleService,
    uow: FakeUnitOfWork,
):
    created = user_role_service.create_role(
        role_dto=user_create_dto(name="Assigned user role"),
    )

    uow.roles_user.assigned_role_ids.add(created.role_id)

    with pytest.raises(DomainOperationError, match="cannot be deleted because it is assigned"):
        user_role_service.delete_role(
            role_dto=user_id_dto(role_id=created.role_id),
        )

    assert created.role_id in uow.roles_user.items


def test_user_role_actor_without_permission_raises(
    user_role_service: UserRoleService,
):
    dto = user_create_dto(
        actor_admin_id=999,
        name="Forbidden user role",
    )

    with pytest.raises(PermissionError):
        user_role_service.create_role(
            role_dto=dto,
        )