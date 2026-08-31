# tests/web/routers/admin/test_roles_router.py

from __future__ import annotations

from typing import Generic, TypeVar

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.application.dto.roles_dto import RoleDTO, RoleResponseDTO
from src.domain.rbac.permissions import (
    AdminPermission,
    PermissionBase,
    UserPermission,
)
from src.web.dependencies.auth import (
    get_current_admin,
    get_employee_id_from_request,
)
from src.web.dependencies.services import get_application_service_factory
from src.web.routers.admin.roles import router as admin_roles_router


T = TypeVar("T", bound=PermissionBase)


# ---------------------------------------------------------------------
# Fake services
# ---------------------------------------------------------------------

class FakeAdminRoleService:
    def __init__(self):
        self.created_dtos: list[RoleDTO[AdminPermission]] = []
        self.requested_dtos: list[RoleDTO[AdminPermission]] = []
        self.deleted_dtos: list[RoleDTO[AdminPermission]] = []
        self.list_dtos: list[RoleDTO[AdminPermission]] = []

    def create_role(
        self,
        *,
        role_dto: RoleDTO[AdminPermission],
    ) -> RoleResponseDTO[AdminPermission]:
        self.created_dtos.append(role_dto)

        return RoleResponseDTO(
            role_id=101,
            name=role_dto.name,
            permissions=role_dto.permissions,
            description=role_dto.description,
            is_system_role=role_dto.is_system_role,
        )

    def get_role(
        self,
        *,
        role_dto: RoleDTO[AdminPermission],
    ) -> RoleResponseDTO[AdminPermission]:
        self.requested_dtos.append(role_dto)

        return RoleResponseDTO(
            role_id=role_dto.role_id,
            name="Admin role",
            permissions=frozenset({
                AdminPermission.ADMIN_OPERATION,
            }),
            description="Admin role description",
            is_system_role=False,
        )

    def get_all_roles(
        self,
        *,
        role_dto: RoleDTO[AdminPermission],
    ) -> list[RoleResponseDTO[AdminPermission]]:
        self.list_dtos.append(role_dto)

        return [
            RoleResponseDTO(
                role_id=1,
                name="Admin role 1",
                permissions=frozenset({
                    AdminPermission.ADMIN_OPERATION,
                }),
                description="First admin role",
                is_system_role=False,
            ),
            RoleResponseDTO(
                role_id=2,
                name="Admin role 2",
                permissions=frozenset({
                    AdminPermission.ADMIN_VIEW,
                }),
                description="Second admin role",
                is_system_role=True,
            ),
        ]

    def delete_role(
        self,
        *,
        role_dto: RoleDTO[AdminPermission],
    ) -> None:
        self.deleted_dtos.append(role_dto)


class FakeUserRoleService:
    def __init__(self):
        self.created_dtos: list[RoleDTO[UserPermission]] = []
        self.requested_dtos: list[RoleDTO[UserPermission]] = []
        self.deleted_dtos: list[RoleDTO[UserPermission]] = []
        self.list_dtos: list[RoleDTO[UserPermission]] = []

    def create_role(
        self,
        *,
        role_dto: RoleDTO[UserPermission],
    ) -> RoleResponseDTO[UserPermission]:
        self.created_dtos.append(role_dto)

        return RoleResponseDTO(
            role_id=201,
            name=role_dto.name,
            permissions=role_dto.permissions,
            description=role_dto.description,
            is_system_role=role_dto.is_system_role,
        )

    def get_role(
        self,
        *,
        role_dto: RoleDTO[UserPermission],
    ) -> RoleResponseDTO[UserPermission]:
        self.requested_dtos.append(role_dto)

        return RoleResponseDTO(
            role_id=role_dto.role_id,
            name="User role",
            permissions=frozenset({
                UserPermission.TICKET_VIEW,
            }),
            description="User role description",
            is_system_role=False,
        )

    def get_all_roles(
        self,
        *,
        role_dto: RoleDTO[UserPermission],
    ) -> list[RoleResponseDTO[UserPermission]]:
        self.list_dtos.append(role_dto)

        return [
            RoleResponseDTO(
                role_id=1,
                name="User role 1",
                permissions=frozenset({
                    UserPermission.TICKET_VIEW,
                }),
                description="First user role",
                is_system_role=False,
            ),
            RoleResponseDTO(
                role_id=2,
                name="User role 2",
                permissions=frozenset({
                    UserPermission.TICKET_OPERATION,
                }),
                description="Second user role",
                is_system_role=True,
            ),
        ]

    def delete_role(
        self,
        *,
        role_dto: RoleDTO[UserPermission],
    ) -> None:
        self.deleted_dtos.append(role_dto)


class FakeApplicationServiceFactory:
    def __init__(self):
        self._admin_role_service = FakeAdminRoleService()
        self._user_role_service = FakeUserRoleService()

    def admin_role_service(self) -> FakeAdminRoleService:
        return self._admin_role_service

    def user_role_service(self) -> FakeUserRoleService:
        return self._user_role_service


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def fake_asf() -> FakeApplicationServiceFactory:
    return FakeApplicationServiceFactory()


@pytest.fixture
def app(fake_asf: FakeApplicationServiceFactory) -> FastAPI:
    app = FastAPI()
    app.include_router(admin_roles_router)

    app.dependency_overrides[get_current_admin] = lambda: True
    app.dependency_overrides[get_employee_id_from_request] = lambda: 1
    app.dependency_overrides[get_application_service_factory] = lambda: fake_asf

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------
# Permission endpoints
# ---------------------------------------------------------------------

def test_get_admin_permissions(
    client: TestClient,
):
    response = client.get("/admin/roles/admin/permissions")

    assert response.status_code == 200
    assert response.json() == [
        permission.value
        for permission in AdminPermission
    ]


def test_get_user_permissions(
    client: TestClient,
):
    response = client.get("/admin/roles/user/permissions")

    assert response.status_code == 200
    assert response.json() == [
        permission.value
        for permission in UserPermission
    ]


# ---------------------------------------------------------------------
# Admin role endpoints
# ---------------------------------------------------------------------

def test_create_admin_role(
    client: TestClient,
    fake_asf: FakeApplicationServiceFactory,
):
    response = client.post(
        "/admin/roles/admin",
        json={
            "name": "Admin operators",
            "permissions": [
                AdminPermission.ADMIN_OPERATION.value,
            ],
            "description": "Can manage admins",
            "is_system_role": False,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "role_id": 101,
        "name": "Admin operators",
        "permissions": [
            AdminPermission.ADMIN_OPERATION.value,
        ],
        "description": "Can manage admins",
        "is_system_role": False,
    }

    saved_dto = fake_asf._admin_role_service.created_dtos[-1]

    assert saved_dto.actor_admin_id == 1
    assert saved_dto.name == "Admin operators"
    assert saved_dto.permissions == frozenset({
        AdminPermission.ADMIN_OPERATION,
    })
    assert saved_dto.description == "Can manage admins"
    assert saved_dto.is_system_role is False


def test_get_all_admin_roles(
    client: TestClient,
    fake_asf: FakeApplicationServiceFactory,
):
    response = client.get("/admin/roles/admin")

    assert response.status_code == 200
    assert response.json() == [
        {
            "role_id": 1,
            "name": "Admin role 1",
            "permissions": [
                AdminPermission.ADMIN_OPERATION.value,
            ],
            "description": "First admin role",
            "is_system_role": False,
        },
        {
            "role_id": 2,
            "name": "Admin role 2",
            "permissions": [
                AdminPermission.ADMIN_VIEW.value,
            ],
            "description": "Second admin role",
            "is_system_role": True,
        },
    ]

    list_dto = fake_asf._admin_role_service.list_dtos[-1]

    assert list_dto.actor_admin_id == 1


def test_get_admin_role_by_id(
    client: TestClient,
    fake_asf: FakeApplicationServiceFactory,
):
    response = client.get("/admin/roles/admin/10")

    assert response.status_code == 200
    assert response.json() == {
        "role_id": 10,
        "name": "Admin role",
        "permissions": [
            AdminPermission.ADMIN_OPERATION.value,
        ],
        "description": "Admin role description",
        "is_system_role": False,
    }

    requested_dto = fake_asf._admin_role_service.requested_dtos[-1]

    assert requested_dto.actor_admin_id == 1
    assert requested_dto.role_id == 10


def test_delete_admin_role(
    client: TestClient,
    fake_asf: FakeApplicationServiceFactory,
):
    response = client.delete("/admin/roles/admin/10")

    assert response.status_code == 204
    assert response.content == b""

    deleted_dto = fake_asf._admin_role_service.deleted_dtos[-1]

    assert deleted_dto.actor_admin_id == 1
    assert deleted_dto.role_id == 10


# ---------------------------------------------------------------------
# User role endpoints
# ---------------------------------------------------------------------

def test_create_user_role(
    client: TestClient,
    fake_asf: FakeApplicationServiceFactory,
):
    response = client.post(
        "/admin/roles/user",
        json={
            "name": "Client users",
            "permissions": [
                UserPermission.TICKET_VIEW.value,
            ],
            "description": "Can view own tickets",
            "is_system_role": False,
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "role_id": 201,
        "name": "Client users",
        "permissions": [
            UserPermission.TICKET_VIEW.value,
        ],
        "description": "Can view own tickets",
        "is_system_role": False,
    }

    saved_dto = fake_asf._user_role_service.created_dtos[-1]

    assert saved_dto.actor_admin_id == 1
    assert saved_dto.name == "Client users"
    assert saved_dto.permissions == frozenset({
        UserPermission.TICKET_VIEW,
    })
    assert saved_dto.description == "Can view own tickets"
    assert saved_dto.is_system_role is False


def test_get_all_user_roles(
    client: TestClient,
    fake_asf: FakeApplicationServiceFactory,
):
    response = client.get("/admin/roles/user")

    assert response.status_code == 200
    assert response.json() == [
        {
            "role_id": 1,
            "name": "User role 1",
            "permissions": [
                UserPermission.TICKET_VIEW.value,
            ],
            "description": "First user role",
            "is_system_role": False,
        },
        {
            "role_id": 2,
            "name": "User role 2",
            "permissions": [
                UserPermission.TICKET_OPERATION.value,
            ],
            "description": "Second user role",
            "is_system_role": True,
        },
    ]

    list_dto = fake_asf._user_role_service.list_dtos[-1]

    assert list_dto.actor_admin_id == 1


def test_get_user_role_by_id(
    client: TestClient,
    fake_asf: FakeApplicationServiceFactory,
):
    response = client.get("/admin/roles/user/20")

    assert response.status_code == 200
    assert response.json() == {
        "role_id": 20,
        "name": "User role",
        "permissions": [
            UserPermission.TICKET_VIEW.value,
        ],
        "description": "User role description",
        "is_system_role": False,
    }

    requested_dto = fake_asf._user_role_service.requested_dtos[-1]

    assert requested_dto.actor_admin_id == 1
    assert requested_dto.role_id == 20


def test_delete_user_role(
    client: TestClient,
    fake_asf: FakeApplicationServiceFactory,
):
    response = client.delete("/admin/roles/user/20")

    assert response.status_code == 204
    assert response.content == b""

    deleted_dto = fake_asf._user_role_service.deleted_dtos[-1]

    assert deleted_dto.actor_admin_id == 1
    assert deleted_dto.role_id == 20