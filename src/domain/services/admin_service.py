# src/domain/services/admin_service.py

from src.domain.department import Department
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError


class AdminService:
    """
    Domain facade for Admin operations.

    Provides a single domain entry point for business operations
    involving Admin.

    Responsibilities:
    - create Admin;
    - update Admin;
    - manage Admin account;
    - enable / disable Admin;
    - change / remove Department;
    - enforce cross-aggregate Admin rules;
    - validate Admin deletion.

    Does not handle:
    - repositories;
    - UnitOfWork;
    - persistence;
    - transactions;
    - RBAC;
    - permissions;
    - RoleManager;
    - loading aggregates.
    """

    # ==================================================================
    # Create
    # ==================================================================

    @staticmethod
    def create(
        *,
        department: Department,
        employee_id: int,
        first_name: str,
        last_name: str = "",
        email: str = "",
        phone: str = "",
        enabled: bool = True,
        login: str = "",
        password: str = "",
        enable_account: bool = True,
        version: int = 0,
        roles: set[int] | None = None,
        job_title: str = "",
    ) -> Admin:
        """
        Create Admin.

        Admin cannot be created in disabled Department.
        """

        AdminService._ensure_department_enabled(
            department=department,
        )

        return Admin.create(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            enabled=enabled,
            login=login,
            password=password,
            enable_account=enable_account,
            version=version,
            roles=roles or set(),
            job_title=job_title,
            department_id=department.department_id,
        )

    # ==================================================================
    # Update
    # ==================================================================

    @staticmethod
    def update(
        *,
        admin: Admin,
        department: Department,
        has_current_executor_tickets: bool,
        job_title: str = "",
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        phone: str = "",
    ) -> None:
        """
        Update Admin.

        If Department is changed:
        - Admin must not be current executor of any Ticket;
        - target Department must be enabled.

        Ordinary Admin data may be updated without these checks
        when Department is unchanged.
        """

        department_changed = (
            admin.department_id != department.department_id
        )

        if department_changed:
            AdminService._ensure_not_current_executor(
                admin=admin,
                has_current_executor_tickets=(
                    has_current_executor_tickets
                ),
            )

            AdminService._ensure_department_enabled(
                department=department,
            )

        admin.update(
            job_title=job_title,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            department_id=department.department_id,
        )

    # ==================================================================
    # Account
    # ==================================================================

    @staticmethod
    def attach_account(
        *,
        admin: Admin,
        login: str,
        password: str,
        enabled_account: bool,
    ) -> None:
        admin.add_account(
            login=login,
            password=password,
            enabled_account=enabled_account,
        )

    @staticmethod
    def detach_account(
        *,
        admin: Admin,
    ) -> None:
        admin.remove_account()

    @staticmethod
    def change_password(
        *,
        admin: Admin,
        password: str,
    ) -> None:
        admin.change_password(
            password=password,
        )

    # ==================================================================
    # Enable / disable
    # ==================================================================

    @staticmethod
    def enable(
        *,
        admin: Admin,
    ) -> None:
        admin.enable()

    @staticmethod
    def disable(
        *,
        admin: Admin,
        has_current_executor_tickets: bool,
    ) -> None:
        """
        Disable Admin.

        Admin cannot be disabled while being current executor
        of at least one Ticket.
        """

        AdminService._ensure_not_current_executor(
            admin=admin,
            has_current_executor_tickets=(
                has_current_executor_tickets
            ),
        )

        admin.disable()

    # ==================================================================
    # Department
    # ==================================================================

    @staticmethod
    def change_department(
        *,
        admin: Admin,
        department: Department,
        has_current_executor_tickets: bool,
    ) -> None:
        """
        Move Admin to another Department.

        Admin cannot be moved while being current executor
        of at least one Ticket.

        Target Department must be enabled.
        """

        AdminService._ensure_not_current_executor(
            admin=admin,
            has_current_executor_tickets=(
                has_current_executor_tickets
            ),
        )

        AdminService._ensure_department_enabled(
            department=department,
        )

        admin.change_department(
            department.department_id,
        )

    @staticmethod
    def remove_department(
        *,
        admin: Admin,
        has_current_executor_tickets: bool,
    ) -> None:
        """
        Remove Admin from Department.

        Admin cannot lose Department while being current executor
        of at least one Ticket.
        """

        AdminService._ensure_not_current_executor(
            admin=admin,
            has_current_executor_tickets=(
                has_current_executor_tickets
            ),
        )

        admin.remove_department()

    # ==================================================================
    # Delete
    # ==================================================================

    @staticmethod
    def ensure_can_delete(
        *,
        admin: Admin,
        has_clients: bool,
        has_ticket_references: bool,
        has_ticket_user_references: bool,
    ) -> None:
        """
        Validate that Admin can be deleted.
        """

        if has_clients:
            raise DomainOperationError(
                f"Cannot delete admin {admin.employee_id}: "
                f"admin is referenced by clients"
            )

        if has_ticket_references:
            raise DomainOperationError(
                f"Cannot delete admin {admin.employee_id}: "
                f"admin is referenced by tickets"
            )

        if has_ticket_user_references:
            raise DomainOperationError(
                f"Cannot delete admin {admin.employee_id}: "
                f"admin is referenced by user tickets"
            )

    # ==================================================================
    # Internal rules
    # ==================================================================

    @staticmethod
    def _ensure_department_enabled(
        *,
        department: Department,
    ) -> None:
        if not department.enabled:
            raise DomainOperationError(
                f"Cannot assign admin to disabled department "
                f"{department.department_id}"
            )

    @staticmethod
    def _ensure_not_current_executor(
        *,
        admin: Admin,
        has_current_executor_tickets: bool,
    ) -> None:
        if has_current_executor_tickets:
            raise DomainOperationError(
                f"Cannot modify admin {admin.employee_id} "
                f"while admin is current ticket executor"
            )