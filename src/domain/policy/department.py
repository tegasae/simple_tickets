# src/domain/policy/department.py

from src.domain.department import Department
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError


class DepartmentPolicy:

    @staticmethod
    def ensure_can_disable(
        *,
        department: Department,
        admins: list[Admin],
    ) -> None:
        if not department.enabled:
            return

        for admin in admins:
            if admin.enabled:
                raise DomainOperationError(
                    "You can't disable this department because it has enabled admins"
                )
        department.disable()
