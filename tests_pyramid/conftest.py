from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.client import Client
from src.domain.department import Department
from src.domain.employee import Admin, User
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role
from tests_pyramid.support.fakes import FakeUnitOfWork

ADMIN_ID = 101
OTHER_ADMIN_ID = 102
USER_ID = 201
OTHER_USER_ID = 202
CLIENT_ID = 301
OTHER_CLIENT_ID = 302
DEPARTMENT_ID = 401
OTHER_DEPARTMENT_ID = 402


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def admin() -> Admin:
    return Admin.create(
        employee_id=ADMIN_ID,
        first_name="Admin",
        last_name="One",
        login="admin-one",
        password="Strong1!",
        department_id=DEPARTMENT_ID,
    )


@pytest.fixture
def other_admin() -> Admin:
    return Admin.create(
        employee_id=OTHER_ADMIN_ID,
        first_name="Admin",
        last_name="Two",
        login="admin-two",
        password="Strong2!",
        department_id=DEPARTMENT_ID,
    )


@pytest.fixture
def client() -> Client:
    return Client.create(
        client_id=CLIENT_ID,
        name="Client One",
        created_by_admin_id=ADMIN_ID,
    )


@pytest.fixture
def other_client() -> Client:
    return Client.create(
        client_id=OTHER_CLIENT_ID,
        name="Client Two",
        created_by_admin_id=ADMIN_ID,
    )


@pytest.fixture
def user() -> User:
    return User.create(
        employee_id=USER_ID,
        first_name="User",
        last_name="One",
        client_id=CLIENT_ID,
        login="user-one",
        password="Strong3!",
    )


@pytest.fixture
def other_user() -> User:
    return User.create(
        employee_id=OTHER_USER_ID,
        first_name="User",
        last_name="Two",
        client_id=CLIENT_ID,
        login="user-two",
        password="Strong4!",
    )


@pytest.fixture
def department() -> Department:
    return Department.create(
        department_id=DEPARTMENT_ID,
        name="Support",
        enabled=True,
    )


@pytest.fixture
def other_department() -> Department:
    return Department.create(
        department_id=OTHER_DEPARTMENT_ID,
        name="Infrastructure",
        enabled=True,
    )


def grant_all_admin_permissions(uow: FakeUnitOfWork, admin: Admin) -> None:
    role = Role(
        role_id=1,
        name="all-admin",
        permissions=frozenset(AdminPermission),
    )
    uow.roles_admin.save(role)
    admin.grant_role(role.role_id)


def grant_all_user_permissions(uow: FakeUnitOfWork, user: User) -> None:
    role = Role(
        role_id=2,
        name="all-user",
        permissions=frozenset(UserPermission),
    )
    uow.roles_user.save(role)
    user.grant_role(role.role_id)
