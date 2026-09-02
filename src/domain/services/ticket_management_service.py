# src/domain/services/ticket_management_service.py

from datetime import datetime

from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket


class TicketManagementService:
    """
    Управленческие workflow-действия над Ticket.

    Здесь нет:
    - RBAC;
    - permissions;
    - проверки существования Admin/Executor;
    - проверки Department;
    - enabled/disabled состояния сотрудников;
    - знания о конкретных TicketStatus.

    TicketStatusRecord создаёт корректную status-record.

    Ticket проверяет допустимость перехода
    и добавляет record в status history.
    """

    @staticmethod
    def accept(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> TicketStatusRecord:
        record = TicketStatusRecord.create_accepted(
            actor_employee_id=actor_employee_id,
            comment=comment,
            date_created=date_created,
        )

        ticket.append_status(record)
        return record

    @staticmethod
    def reject(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str,
        date_created: datetime | None = None,
    ) -> TicketStatusRecord:
        record = TicketStatusRecord.create_rejected(
            actor_employee_id=actor_employee_id,
            comment=comment,
            date_created=date_created,
        )

        ticket.append_status(record)
        return record

    @staticmethod
    def defer(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str,
        date_created: datetime | None = None,
    ) -> TicketStatusRecord:
        record = TicketStatusRecord.create_deferred(
            actor_employee_id=actor_employee_id,
            comment=comment,
            date_created=date_created,
        )

        ticket.append_status(record)
        return record

    @staticmethod
    def schedule(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        planned_start_at: datetime,
        planned_finish_at: datetime | None = None,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> TicketStatusRecord:
        record = TicketStatusRecord.create_scheduled(
            actor_employee_id=actor_employee_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
            date_created=date_created,
        )

        ticket.append_status(record)
        return record

    @staticmethod
    def assign(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        executor_id: int,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> TicketStatusRecord:
        record = TicketStatusRecord.create_assigned(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
            date_created=date_created,
        )

        ticket.append_status(record)
        return record

    @staticmethod
    def ready_to_work(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        executor_id: int,
        planned_start_at: datetime,
        planned_finish_at: datetime | None = None,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> TicketStatusRecord:
        record = TicketStatusRecord.create_ready_to_work(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
            date_created=date_created,
        )

        ticket.append_status(record)
        return record

    @staticmethod
    def cancel(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str,
        date_created: datetime | None = None,
    ) -> TicketStatusRecord:
        record = TicketStatusRecord.create_cancelled(
            actor_employee_id=actor_employee_id,
            comment=comment,
            date_created=date_created,
        )

        ticket.append_status(record)
        return record

    @staticmethod
    def cancel_by_user(
        *,
        ticket: Ticket,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> TicketStatusRecord:
        record = TicketStatusRecord.create_cancelled_by_user(
            comment=comment,
            date_created=date_created,
        )

        ticket.append_status(record)
        return record