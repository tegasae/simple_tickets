from __future__ import annotations

from datetime import datetime

import pytest

from src.domain.department import Department
from src.domain.exceptions import DomainOperationError, ItemValidationError

pytestmark = pytest.mark.unit


def test_department_create_and_restore() -> None:
    department = Department.create(department_id=0, name="Support")
    assert department.department_id == 0
    assert str(department.name) == "Support"

    created = datetime(2025, 1, 1)
    restored = Department.restore(
        department_id=5,
        name="Support",
        enabled=False,
        date_created=created,
        version=3,
    )
    assert restored.department_id == 5
    assert restored.enabled is False
    assert restored.date_created == created
    assert restored.version == 3


@pytest.mark.parametrize(
    "factory,extra",
    [
        (Department.create, {}),
        (Department.restore, {"enabled": True, "date_created": datetime.now()}),
    ],
)
def test_department_rejects_negative_id(factory, extra) -> None:
    with pytest.raises(ItemValidationError):
        factory(department_id=-1, name="Support", **extra)


def test_department_rename_requires_enabled_department() -> None:
    department = Department.create(department_id=1, name="Support")
    department.rename("Helpdesk")
    assert str(department.name) == "Helpdesk"
    department.disable()
    with pytest.raises(DomainOperationError, match="disabled"):
        department.rename("Other")


def test_department_rename_wraps_invalid_name() -> None:
    department = Department.create(department_id=1, name="Support")
    with pytest.raises(ItemValidationError):
        department.rename("A")


def test_department_enable_disable_and_identity() -> None:
    department = Department.create(department_id=1, name="Support")
    department.disable()
    with pytest.raises(DomainOperationError):
        department.ensure_enabled()
    department.enable()
    department.ensure_enabled()
    assert department == Department.create(department_id=1, name="Other")
    assert department != Department.create(department_id=2, name="Support")
