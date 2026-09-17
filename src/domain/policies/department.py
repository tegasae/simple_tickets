# src/domain/policies/department.py

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


    @staticmethod
    def can_operation(*,department:Department):
        if not department.enabled:
            raise DomainOperationError(
                    f"You can't work with disable department {department.department_id} {department.name}"
                )