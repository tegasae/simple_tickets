import pytest

from src.application.helper.employee_helper import EmployeeHelper
from src.domain.employee import User
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import AdminPermission, UserPermission
from src.domain.rbac.role_new import Role


def test_employee_helper_allows_empty_or_new_login(uow):
    helper = EmployeeHelper(uow)  # type: ignore[arg-type]

    helper.ensure_login_is_free(login=None)
    helper.ensure_login_is_free(login="new-login")


def test_employee_helper_rejects_existing_user_login(uow):
    user = User.create(
        employee_id=1,
        first_name="Alice",
        client_id=1,
        login="alice",
        password="Secret123!",
    )
    uow.users.save(user)
    helper = EmployeeHelper(uow)  # type: ignore[arg-type]

    with pytest.raises(DomainOperationError):
        helper.ensure_login_is_free(login="alice")


def test_employee_helper_returns_role_managers(uow):
    uow.roles_admin.save(Role(role_id=1, name="admin", permissions=frozenset({AdminPermission.ASSIGN_ROLE})))
    uow.roles_user.save(Role(role_id=2, name="user", permissions=frozenset({UserPermission.CREATE_TICKET})))

    helper = EmployeeHelper(uow)  # type: ignore[arg-type]

    assert helper.get_role_manager_admin() is not None
    assert helper.get_role_manager_user() is not None
