# src/domain/services/department_service.py

from src.domain.department import Department
from src.domain.exceptions import DomainOperationError


class DepartmentService:
    """
    Domain service for Department operations.

    Intended to become the Department domain facade.

    Responsibilities:
    - create Department;
    - rename Department;
    - enable / disable Department;
    - enforce cross-aggregate Department rules;
    - validate Department deletion.

    Does not handle:
    - repositories;
    - UnitOfWork;
    - persistence;
    - transactions;
    - RBAC;
    - permissions;
    """

    # ==================================================================
    # Create
    # ==================================================================

    @staticmethod
    def create(
        *,
        department_id: int,
        name: str,
        enabled: bool = True,
    ) -> Department:
        return Department.create(
            department_id=department_id,
            name=name,
            enabled=enabled,
        )

    # ==================================================================
    # Update
    # ==================================================================

    @staticmethod
    def rename(
        *,
        department: Department,
        name: str,
    ) -> None:
        department.rename(name)

    # ==================================================================
    # Enable / disable
    # ==================================================================

    @staticmethod
    def enable(
        *,
        department: Department,
    ) -> None:
        department.enable()

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

    # ==================================================================
    # Delete
    # ==================================================================

    @staticmethod
    def ensure_can_delete(
        *,
        department: Department,
        has_admin_references: bool,
        has_ticket_references: bool,
    ) -> None:
        """
        Validate that Department can be deleted.

        Department cannot be deleted while referenced by:
        - Admin;
        - Ticket.
        """

        if has_admin_references:
            raise DomainOperationError(
                f"Cannot delete department "
                f"{department.department_id}: "
                f"department is referenced by admins"
            )

        if has_ticket_references:
            raise DomainOperationError(
                f"Cannot delete department "
                f"{department.department_id}: "
                f"department is referenced by tickets"
            )