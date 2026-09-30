# src/domain/facades/department_facade.py

from src.domain.department import Department
from src.domain.exceptions import DomainOperationError


class DepartmentFacade:
    """
    Domain facade for Department operations.

    Provides a single domain entry point for business operations
    involving Department.

    Responsibilities:
    - execute Department operations;
    - enforce Department business rules;
    - enforce cross-aggregate rules using facts supplied
      by the application layer.

    Does not handle:
    - repositories;
    - UnitOfWork;
    - persistence;
    - transactions;
    - RBAC;
    - permissions;
    - loading aggregates.
    """

    # ==================================================================
    # Enable / disable
    # ==================================================================

    @staticmethod
    def disable(
        *,
        department: Department,
        has_enabled_admins: bool,
        has_open_tickets: bool,
    ) -> None:
        """
        Disable Department.

        Department cannot be disabled while:

        - at least one enabled Admin belongs to Department;
        - at least one open Ticket belongs to Department.

        No cascade is performed.

        Admins are not disabled automatically.
        Tickets are not suspended automatically.
        """

        if has_enabled_admins:
            raise DomainOperationError(
                f"Cannot disable department "
                f"{department.department_id}: "
                f"department has enabled admins"
            )

        if has_open_tickets:
            raise DomainOperationError(
                f"Cannot disable department "
                f"{department.department_id}: "
                f"department has open tickets"
            )

        department.disable()

    @staticmethod
    def enable(
        *,
        department: Department,
    ) -> None:
        """
        Enable Department.

        Enabling Department has no cross-aggregate side effects.
        """

        department.enable()