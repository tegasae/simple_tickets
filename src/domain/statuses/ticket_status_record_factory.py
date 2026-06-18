# src/domain/ticket_status_record_factory.py

from datetime import datetime

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import StatusRecordTicket


class TicketStatusRecordFactory:
    """
    Фабрика записей статусов заявки.

    Здесь задаются правила создания конкретных бизнес-событий:

    - где executor_id обязателен;
    - где planned_start_at обязателен;
    - где actual_started_at ставится автоматически;
    - где actual_started_at должен быть передан явно;
    - где comment обязателен.
    """

    @staticmethod
    def created(
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> StatusRecordTicket:
        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.CREATED,
            comment=comment,
        )

    @staticmethod
    def accepted(
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> StatusRecordTicket:
        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.ACCEPTED,
            comment=comment,
        )

    @staticmethod
    def rejected(
        *,
        actor_employee_id: int,
        comment: str,
    ) -> StatusRecordTicket:
        TicketStatusRecordFactory._require_comment(
            comment,
            "Reject reason is required",
        )

        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.REJECTED,
            comment=comment,
        )

    @staticmethod
    def deferred(
        *,
        actor_employee_id: int,
        comment: str,
    ) -> StatusRecordTicket:
        TicketStatusRecordFactory._require_comment(
            comment,
            "Defer reason is required",
        )

        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.DEFERRED,
            comment=comment,
        )

    @staticmethod
    def scheduled(
        *,
        actor_employee_id: int,
        planned_start_at: datetime,
        planned_finish_at: datetime | None = None,
        executor_id: int = 0,
        comment: str = "",
    ) -> StatusRecordTicket:
        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.SCHEDULED,
            executor_id=executor_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
        )

    @staticmethod
    def assigned(
        *,
        actor_employee_id: int,
        executor_id: int,
        planned_start_at: datetime | None = None,
        planned_finish_at: datetime | None = None,
        comment: str = "",
    ) -> StatusRecordTicket:
        TicketStatusRecordFactory._require_executor(executor_id)

        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.ASSIGNED,
            executor_id=executor_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
        )

    @staticmethod
    def at_work(
        *,
        actor_employee_id: int,
        executor_id: int,
        comment: str = "",
    ) -> StatusRecordTicket:
        TicketStatusRecordFactory._require_executor(executor_id)

        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.AT_WORK,
            executor_id=executor_id,
            actual_started_at=datetime.now(),
            comment=comment,
        )

    @staticmethod
    def paused(
        *,
        actor_employee_id: int,
        executor_id: int,
        comment: str = "",
    ) -> StatusRecordTicket:
        TicketStatusRecordFactory._require_executor(executor_id)

        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.PAUSED,
            executor_id=executor_id,
            comment=comment,
        )

    @staticmethod
    def offline_work(
        *,
        actor_employee_id: int,
        executor_id: int,
        actual_started_at: datetime,
        actual_finished_at: datetime | None = None,
        comment: str = "",
    ) -> StatusRecordTicket:
        TicketStatusRecordFactory._require_executor(executor_id)

        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.OFFLINE_WORK,
            executor_id=executor_id,
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
            comment=comment,
        )

    @staticmethod
    def ready_for_review(
        *,
        actor_employee_id: int,
        executor_id: int,
        actual_finished_at: datetime | None = None,
        comment: str = "",
    ) -> StatusRecordTicket:
        TicketStatusRecordFactory._require_executor(executor_id)

        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=executor_id,
            actual_finished_at=actual_finished_at or datetime.now(),
            comment=comment,
        )

    @staticmethod
    def executed(
        *,
        actor_employee_id: int,
        comment: str = "",
    ) -> StatusRecordTicket:
        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.EXECUTED,
            comment=comment,
        )

    @staticmethod
    def cancelled(
        *,
        actor_employee_id: int,
        comment: str,
    ) -> StatusRecordTicket:
        TicketStatusRecordFactory._require_comment(
            comment,
            "Cancel reason is required",
        )

        return StatusRecordTicket(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.CANCELLED,
            comment=comment,
        )

    @staticmethod
    def _require_executor(executor_id: int) -> None:
        if executor_id <= 0:
            raise ItemValidationError("Executor is required")

    @staticmethod
    def _require_comment(comment: str, message: str) -> None:
        if not comment or not comment.strip():
            raise ItemValidationError(message)