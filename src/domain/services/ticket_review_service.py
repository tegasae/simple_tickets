# src/domain/services/ticket_review_service.py

from datetime import datetime

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket


class TicketReviewService:
    """
    Domain service для проверки результата Ticket.

    Здесь нет:
    - RBAC;
    - permissions;
    - repository;
    - знания о конкретных TicketStatus.

    Review-операции допустимы только тогда,
    когда текущая TicketStatusRecord допускает review результата.

    Ticket проверяет итоговый workflow-переход.
    """

    @staticmethod
    def confirm_execution(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Подтверждает результат выполнения Ticket.
        """
        TicketReviewService._ensure_review_pending(
            ticket=ticket,
        )

        record = TicketStatusRecord.create_executed(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        ticket.append_status(record)

        return record

    @staticmethod
    def return_to_work(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Возвращает Ticket в работу тому же executor.

        Новая рабочая сессия начинается в момент возврата.
        """
        TicketReviewService._ensure_review_pending(
            ticket=ticket,
        )

        executor_id = (
            TicketReviewService._current_executor_or_raise(
                ticket=ticket,
            )
        )

        record = TicketStatusRecord.create_at_work(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
        )

        ticket.append_status(record)

        return record

    @staticmethod
    def return_to_assigned(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        executor_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Возвращает Ticket в назначенное состояние.

        Executor может быть изменён.
        """
        TicketReviewService._ensure_review_pending(
            ticket=ticket,
        )

        record = TicketStatusRecord.create_assigned(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
        )

        ticket.append_status(record)

        return record

    @staticmethod
    def return_to_scheduled(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        planned_start_at: datetime,
        planned_finish_at: datetime | None = None,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Возвращает Ticket к планированию.
        """
        TicketReviewService._ensure_review_pending(
            ticket=ticket,
        )

        record = TicketStatusRecord.create_scheduled(
            actor_employee_id=actor_employee_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
        )

        ticket.append_status(record)

        return record

    @staticmethod
    def return_to_ready_to_work(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        executor_id: int,
        planned_start_at: datetime,
        planned_finish_at: datetime | None = None,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Возвращает Ticket в подготовленное к работе состояние.
        """
        TicketReviewService._ensure_review_pending(
            ticket=ticket,
        )

        record = TicketStatusRecord.create_ready_to_work(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
        )

        ticket.append_status(record)

        return record

    @staticmethod
    def return_to_deferred(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str,
    ) -> TicketStatusRecord:
        """
        Переводит Ticket с review в отложенное состояние.
        """
        TicketReviewService._ensure_review_pending(
            ticket=ticket,
        )

        record = TicketStatusRecord.create_deferred(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        ticket.append_status(record)

        return record

    @staticmethod
    def _ensure_review_pending(
        *,
        ticket: Ticket,
    ) -> None:
        if not ticket.current_status_record().can_review_result():
            raise DomainOperationError(
                "Ticket result is not awaiting review"
            )

    @staticmethod
    def _current_executor_or_raise(
        *,
        ticket: Ticket,
    ) -> int:
        executor_id = ticket.current_executor_id()

        if executor_id <= 0:
            raise DomainOperationError(
                "Ticket has no current executor"
            )

        return executor_id