from __future__ import annotations

import pytest

from src.domain.employee import Admin
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role import Authorizer, RoleManager
from src.domain.rbac.role_new import AdminRole, Role, RoleStore, UserRole
from tests_pyramid.support.fakes import InMemoryRoleRepository

pytestmark = pytest.mark.unit


def test_role_has_permission_and_hashes_by_id() -> None:
    role = Role(
        role_id=1,
        name="ops",
        permissions=frozenset({AdminPermission.TICKET_VIEW}),
    )
    same_id = Role(role_id=1, name="other")
    assert role.has_permission(AdminPermission.TICKET_VIEW)
    assert hash(role) == hash(same_id)


def test_admin_role_rejects_user_permission() -> None:
    with pytest.raises(ValueError):
        AdminRole(
            role_id=1,
            name="bad",
            permissions=frozenset({UserPermission.TICKET_VIEW}),
        )


def test_user_role_rejects_admin_permission() -> None:
    with pytest.raises(ValueError):
        UserRole(
            role_id=1,
            name="bad",
            permissions=frozenset({AdminPermission.TICKET_VIEW}),
        )


def test_role_store_put_check_delete() -> None:
    store = RoleStore[AdminPermission]()
    role = Role(role_id=1, name="ops")
    store.put_role(role)
    assert store.check_role(role)
    store.delete_role(role)
    assert not store.check_role(role)


def test_authorizer_unions_permissions_from_all_roles() -> None:
    repo = InMemoryRoleRepository([
        Role(1, "view", frozenset({AdminPermission.TICKET_VIEW})),
        Role(2, "operate", frozenset({AdminPermission.TICKET_OPERATION})),
    ])
    admin = Admin.create(employee_id=1, first_name="Admin", roles={1, 2})
    permissions = Authorizer(repo).permissions_of(admin)
    assert permissions == {
        AdminPermission.TICKET_VIEW,
        AdminPermission.TICKET_OPERATION,
    }


def test_authorizer_require_rejects_missing_permission() -> None:
    repo = InMemoryRoleRepository([
        Role(1, "view", frozenset({AdminPermission.TICKET_VIEW})),
    ])
    admin = Admin.create(employee_id=1, first_name="Admin", roles={1})
    with pytest.raises(PermissionError):
        Authorizer(repo).require(admin, AdminPermission.TICKET_OPERATION)


def test_role_manager_validates_role_and_mutates_target() -> None:
    repo = InMemoryRoleRepository([
        Role(1, "assigner", frozenset({AdminPermission.ROLE_ASSIGN, AdminPermission.ROLE_REVOKE})),
        Role(2, "target", frozenset({AdminPermission.TICKET_VIEW})),
    ])
    actor = Admin.create(employee_id=1, first_name="Actor", roles={1})
    target = Admin.create(employee_id=2, first_name="Target")
    manager = RoleManager(Authorizer(repo), repo)

    manager.grant_roles(
        actor=actor,
        target=target,
        role_ids=frozenset({2}),
        required_permission=AdminPermission.ROLE_ASSIGN,
    )
    assert target.role_ids() == frozenset({2})

    manager.revoke_roles(
        actor=actor,
        target=target,
        role_ids=frozenset({2}),
        required_permission=AdminPermission.ROLE_REVOKE,
    )
    assert target.role_ids() == frozenset()


def test_role_manager_does_not_grant_unknown_role() -> None:
    repo = InMemoryRoleRepository([
        Role(1, "assigner", frozenset({AdminPermission.ROLE_ASSIGN})),
    ])
    actor = Admin.create(employee_id=1, first_name="Actor", roles={1})
    target = Admin.create(employee_id=2, first_name="Target")
    manager = RoleManager(Authorizer(repo), repo)
    with pytest.raises(KeyError):
        manager.grant_role(
            actor,
            target,
            999,
            required_permission=AdminPermission.ROLE_ASSIGN,
        )
