from __future__ import annotations

from src.domain.account import NoAccount
from src.domain.employee import Admin, User

import pytest

pytestmark = pytest.mark.unit


def test_user_create_without_credentials_uses_no_account() -> None:
    user = User.create(employee_id=1, first_name="User", client_id=10)
    assert isinstance(user.account, NoAccount)
    assert user.client_id == 10
    assert user.role_ids() == frozenset()


def test_user_update_replaces_optional_values_with_empty() -> None:
    user = User.create(
        employee_id=1,
        first_name="User",
        last_name="Old",
        email="old@example.com",
        phone="123",
        client_id=10,
    )
    user.update(first_name="New", last_name="", email="", phone="")
    assert str(user.first_name) == "New"
    assert str(user.last_name) == ""
    assert str(user.email) == ""
    assert str(user.phone) == ""


def test_user_identity_uses_global_employee_id_space() -> None:
    admin = Admin.create(employee_id=1, first_name="Admin")
    user = User.create(employee_id=1, first_name="User", client_id=10)
    other = User.create(employee_id=2, first_name="User", client_id=10)
    assert admin == user
    assert user == admin
    assert user != other


