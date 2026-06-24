from __future__ import annotations

from datetime import datetime

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.statuses.ticket_status_record_factory import TicketStatusRecordFactory
from src.domain.ticket import Ticket


class TicketExecutionService:
    """
    Операции, которые выполняет текущий исполнитель заявки.
    """

    @staticmethod
    def take_to_work(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        executor_id = TicketExecutionService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecordFactory.at_work(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
        )

        TicketExecutionService._append_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def pause_work(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        executor_id = TicketExecutionService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecordFactory.paused(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
        )

        TicketExecutionService._append_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def resume_work(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        executor_id = TicketExecutionService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecordFactory.at_work(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
        )

        TicketExecutionService._append_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def register_offline_work(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        actual_started_at: datetime,
        actual_finished_at: datetime,
        comment: str = "",
    ) -> TicketStatusRecord:
        executor_id = TicketExecutionService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecordFactory.offline_work(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
            comment=comment,
        )

        TicketExecutionService._append_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def submit_for_review(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        executor_id = TicketExecutionService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecordFactory.ready_for_review(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            actual_finished_at=(
                TicketExecutionService._resolve_actual_finished_at(ticket)
            ),
            comment=comment,
        )

        TicketExecutionService._append_status(
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
        ticket.append_status(record)

    @staticmethod
    def _ensure_current_executor(
        *,
        ticket: Ticket,
        actor_employee_id: int,
    ) -> int:
        if actor_employee_id <= 0:
            raise DomainOperationError(
                "Actor employee ID must be positive"
            )

        executor_id = ticket.current_executor_id()

        if executor_id <= 0:
            raise DomainOperationError(
                "Ticket has no current executor"
            )

        if actor_employee_id != executor_id:
            raise DomainOperationError(
                f"Actor {actor_employee_id} is not current ticket executor"
            )

        return executor_id

    @staticmethod
    def _resolve_actual_finished_at(
        ticket: Ticket,
    ) -> datetime | None:
        current_record = ticket.current_status_record()

        if current_record.status == TicketStatus.OFFLINE_WORK:
            return current_record.actual_finished_at

        return None