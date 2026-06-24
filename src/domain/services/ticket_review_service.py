from __future__ import annotations

from datetime import datetime

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.statuses.ticket_status_record_factory import TicketStatusRecordFactory
from src.domain.ticket import Ticket


class TicketReviewService:
    """
    Операции проверки результата заявки.
    """

    @staticmethod
    def confirm_execution(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        READY_FOR_REVIEW -> EXECUTED
        """


        record = TicketStatusRecordFactory.executed(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        TicketReviewService._append_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def return_to_work(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        READY_FOR_REVIEW -> AT_WORK

        Возвращает заявку тому же исполнителю.
        """


        executor_id = TicketReviewService._current_executor_or_raise(
            ticket
        )

        record = TicketStatusRecordFactory.at_work(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
        )

        TicketReviewService._append_status(
            ticket=ticket,
            record=record,
        )

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
        READY_FOR_REVIEW -> ASSIGNED

        Исполнитель может быть изменён.
        """

        record = TicketStatusRecordFactory.assigned(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
        )

        TicketReviewService._append_status(
            ticket=ticket,
            record=record,
        )

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
        READY_FOR_REVIEW -> SCHEDULED
        """


        record = TicketStatusRecordFactory.scheduled(
            actor_employee_id=actor_employee_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
        )

        TicketReviewService._append_status(
            ticket=ticket,
            record=record,
        )

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
        READY_FOR_REVIEW -> READY_TO_WORK
        """


        record = TicketStatusRecordFactory.ready_to_work(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
        )

        TicketReviewService._append_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def return_to_deferred(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str,
    ) -> TicketStatusRecord:
        """
        READY_FOR_REVIEW -> DEFERRED
        """


        record = TicketStatusRecordFactory.deferred(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        TicketReviewService._append_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def _append_status(
            *,
            ticket: Ticket,
            record: TicketStatusRecord,
    ) -> None:
        if ticket.current_status() != TicketStatus.READY_FOR_REVIEW:
            raise DomainOperationError(
                "Ticket must be in READY_FOR_REVIEW status"
            )
        ticket.append_status(record)

    @staticmethod
    def _current_executor_or_raise(ticket: Ticket) -> int:
        executor_id = ticket.current_executor_id()

        if executor_id <= 0:
            raise DomainOperationError(
                "Ticket has no current executor"
            )

        return executor_id

