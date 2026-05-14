import pytest

from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.employee import Admin, User
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role


def test_require_actor_admin_returns_admin_with_permission(uow):
    admin = Admin.create(employee_id=1, first_name="Root")
    admin.grant_role(1)
    uow.admins.save(admin)
    uow.roles_admin.save(Role(role_id=1, name="operators", permissions=frozenset({AdminPermission.CREATE_USER})))

    helper = EmployeeActorHelper(uow)  # type: ignore[arg-type]

    assert helper.require_actor_admin(actor_admin_id=1, permission=AdminPermission.CREATE_USER) == admin


def test_require_actor_admin_rejects_missing_permission(uow):
    admin = Admin.create(employee_id=1, first_name="Root")
    uow.admins.save(admin)
    helper = EmployeeActorHelper(uow)  # type: ignore[arg-type]

    with pytest.raises(PermissionError):
        helper.require_actor_admin(actor_admin_id=1, permission=AdminPermission.CREATE_USER)


def test_require_actor_user_returns_user_with_permission(uow):
    user = User.create(employee_id=2, first_name="Alice", client_id=10)
    user.grant_role(5)
    uow.users.save(user)
    uow.roles_user.save(Role(role_id=5, name="ticket creator", permissions=frozenset({UserPermission.CREATE_TICKET})))
    helper = EmployeeActorHelper(uow)  # type: ignore[arg-type]

    assert helper.require_actor_user(actor_user_id=2, permission=UserPermission.CREATE_TICKET) == user
