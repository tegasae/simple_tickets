from __future__ import annotations

import pytest

from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError

pytestmark = pytest.mark.unit


def test_create_empty_marks_employee_as_empty() -> None:
    admin = Admin.create_empty()
    assert admin.is_empty()
    assert admin.employee_id == 0


def test_change_password_without_account_is_noop() -> None:
    admin = Admin.create(employee_id=1, first_name="Admin")
    admin.change_password("Strong1!")
    assert not bool(admin.account)


def test_disabled_employee_cannot_be_granted_role_but_revoke_remains_idempotent() -> None:
    admin = Admin.create(employee_id=1, first_name="Admin")
    admin.disable()
    with pytest.raises(DomainOperationError):
        admin.grant_role(10)
    admin.revoke_role(10)
    assert admin.role_ids() == frozenset()
