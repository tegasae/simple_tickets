# src/domain/services/admin_department_service.py

from src.domain.department import Department
from src.domain.employee import Admin
from src.domain.exceptions import DomainOperationError


class AdminDepartmentService:
    """
    Domain service для управления принадлежностью Admin к Department.

    Отвечает за межагрегатные бизнес-правила между:
    - Admin;
    - Department;
    - фактом наличия у Admin выполняемых Ticket.

    Не отвечает за:
    - RBAC;
    - permissions;
    - загрузку Admin / Department;
    - поиск Ticket;
    - repositories;
    - UnitOfWork;
    - persistence.

    Application layer обязан заранее определить
    has_at_work_tickets.
    """

    @staticmethod
    def change_department(
        *,
        admin: Admin,
        department: Department,
        has_at_work_tickets: bool,
    ) -> None:
        """
        Переводит Admin в другой Department.

        Нельзя:
        - переводить Admin в disabled Department;
        - менять Department, пока Admin является
          исполнителем Ticket, находящейся в работе.
        """
        AdminDepartmentService._ensure_no_tickets_in_work(
            admin=admin,
            has_at_work_tickets=has_at_work_tickets,
        )

        if not department.enabled:
            raise DomainOperationError(
                f"Cannot assign admin {admin.employee_id} "
                f"to disabled department "
                f"{department.department_id}",
            )

        admin.department_id = department.department_id

    @staticmethod
    def remove_department(
        *,
        admin: Admin,
        has_at_work_tickets: bool,
    ) -> None:
        """
        Снимает Department с Admin.

        Нельзя снимать Department, пока Admin является
        исполнителем Ticket, находящейся в работе.
        """
        AdminDepartmentService._ensure_no_tickets_in_work(
            admin=admin,
            has_at_work_tickets=has_at_work_tickets,
        )

        admin.remove_department()

    @staticmethod
    def _ensure_no_tickets_in_work(
        *,
        admin: Admin,
        has_at_work_tickets: bool,
    ) -> None:
        if has_at_work_tickets:
            raise DomainOperationError(
                f"Cannot change department of admin "
                f"{admin.employee_id} while admin has "
                f"tickets in work",
            )