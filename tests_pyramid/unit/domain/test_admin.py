from __future__ import annotations

import pytest

from src.domain.account import Account, NoAccount
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError

pytestmark = pytest.mark.unit


def test_admin_create_with_credentials_creates_account_roles_and_department() -> None:
    admin = Admin.create(
        employee_id=1,
        first_name="Admin",
        login="admin",
        password="Strong1!",
        roles={4, 5},
        department_id=9,
    )
    assert isinstance(admin.account, Account)
    assert admin.role_ids() == frozenset({4, 5})
    assert admin.department_id == 9


@pytest.mark.parametrize(
    "login,password",
    [("admin", ""), ("", "Strong1!")],
)
def test_admin_requires_login_and_password_together(login: str, password: str) -> None:
    with pytest.raises(DomainOperationError):
        Admin.create(
            employee_id=1,
            first_name="Admin",
            login=login,
            password=password,
        )


def test_disabled_admin_cannot_operate_add_account_or_grant_role() -> None:
    admin = Admin.create(employee_id=1, first_name="Admin")
    admin.disable()
    with pytest.raises(DomainOperationError):
        admin.can_do_operation()
    with pytest.raises(DomainOperationError):
        admin.add_account("admin", "Strong1!", True)
    with pytest.raises(DomainOperationError):
        admin.grant_role(1)


def test_admin_enable_disable_propagates_to_account() -> None:
    admin = Admin.create(
        employee_id=1,
        first_name="Admin",
        login="admin",
        password="Strong1!",
    )
    admin.disable()
    assert not admin.enabled
    assert not admin.account.enabled
    admin.enable()
    assert admin.enabled
    assert admin.account.enabled


def test_admin_account_attach_remove_and_change_password() -> None:
    admin = Admin.create(employee_id=1, first_name="Admin")
    assert isinstance(admin.account, NoAccount)
    admin.add_account("admin", "Strong1!", True)
    assert isinstance(admin.account, Account)
    admin.change_password("Better2!")
    assert admin.account.verify_password("Better2!")
    admin.remove_account()
    assert isinstance(admin.account, NoAccount)


def test_admin_roles_are_exposed_immutably_and_revoke_is_idempotent() -> None:
    admin = Admin.create(employee_id=1, first_name="Admin")
    admin.grant_role(3)
    assert admin.role_ids() == frozenset({3})
    admin.revoke_role(3)
    admin.revoke_role(3)
    assert admin.role_ids() == frozenset()


def test_admin_update_updates_personal_fields_and_job_title() -> None:
    admin = Admin.create(
        employee_id=1,
        first_name="Old",
        last_name="Admin",
        email="old@example.com",
        phone="123",
        job_title="Junior",
    )
    admin.update(
        first_name="New",
        last_name="",
        email="",
        phone="",
        job_title="Senior",
    )
    assert str(admin.first_name) == "New"
    assert str(admin.last_name) == ""
    assert str(admin.email) == ""
    assert str(admin.phone) == ""
    assert admin.job_title == "Senior"


def test_admin_department_operations() -> None:
    admin = Admin.create(employee_id=1, first_name="Admin")
    assert not admin.has_department()
    admin.change_department(5)
    assert admin.has_department()
    assert admin.department_id == 5
    admin.remove_department()
    assert admin.department_id == 0
