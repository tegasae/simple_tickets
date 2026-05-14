from src.domain.account import Account, NoAccount
from src.domain.employee import Admin, User


def test_admin_create_with_account_and_roles():
    admin = Admin.create(
        employee_id=1,
        first_name="John",
        last_name="Smith",
        email="john@example.com",
        login="john",
        password="Secret123!",
        roles=frozenset({1, 2}),
        job_title="Engineer",
    )

    assert admin.employee_id == 1
    assert admin.job_title == "Engineer"
    assert isinstance(admin.account, Account)
    assert admin.account.verify_password("Secret123!") is True
    assert admin.role_ids() == frozenset({1, 2})


def test_user_create_without_account_uses_null_object():
    user = User.create(employee_id=2, first_name="Alice", client_id=10)

    assert user.client_id == 10
    assert isinstance(user.account, NoAccount)
    assert bool(user.account) is False


def test_employee_enable_disable_updates_account_too():
    admin = Admin.create(
        employee_id=1,
        first_name="John",
        login="john",
        password="Secret123!",
        enable_account=True,
    )

    admin.disable()
    assert admin.enabled is False
    assert admin.account.enabled is False

    admin.enable()
    assert admin.enabled is True
    assert admin.account.enabled is True


def test_grant_and_revoke_role():
    user = User.create(employee_id=2, first_name="Alice", client_id=10)

    user.grant_role(5)
    user.grant_role(7)
    user.revoke_role(5)

    assert user.role_ids() == frozenset({7})
