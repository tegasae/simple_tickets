# src/domain/services/ticket_execution_service.py

from datetime import datetime, timezone

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket


class TicketExecutionService:
    """
    Domain service для фиксации выполнения работы.

    Не отвечает за:
    - permissions;
    - роли;
    - проверку enabled Admin;
    - проверку department;
    - поиск Ticket в repository.

    Application service должен проверить право вызвать use case.
    """
    @staticmethod
    def take_to_work(

        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Начинает обычную онлайн-работу.

        Допустимо только из:
        - ASSIGNED;
        - READY_TO_WORK.

        Начать работу может только current executor.
        """
        TicketExecutionService._ensure_current_status(
            ticket=ticket,
            allowed_statuses=(
                TicketStatus.ASSIGNED,
                TicketStatus.READY_TO_WORK,
            ),
            operation="take ticket to work",
        )
        TicketExecutionService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecord(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.AT_WORK,
            executor_id=ticket.current_executor_id(),
            actual_started_at=datetime.now(timezone.utc),
            comment=comment,
        )

        ticket.append_status(record)
        return record

    @staticmethod
    def pause_work(

        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Временно приостанавливает текущую работу.

        Допустимо только из AT_WORK.
        Исполнитель сохраняется.
        """
        TicketExecutionService._ensure_current_status(
            ticket=ticket,
            allowed_statuses=(TicketStatus.AT_WORK,),
            operation="pause ticket work",
        )
        TicketExecutionService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecord(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.PAUSED,
            executor_id=ticket.current_executor_id(),
            comment=comment,
        )

        ticket.append_status(record)
        return record
    @staticmethod
    def resume_work(

        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Возобновляет ранее приостановленную работу.

        Допустимо только из PAUSED.
        """
        TicketExecutionService._ensure_current_status(
            ticket=ticket,
            allowed_statuses=(TicketStatus.PAUSED,),
            operation="resume ticket work",
        )
        TicketExecutionService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecord(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.AT_WORK,
            executor_id=ticket.current_executor_id(),
            actual_started_at=datetime.now(timezone.utc),
            comment=comment,
        )

        ticket.append_status(record)
        return record

    @staticmethod
    def submit_for_review(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Завершает текущий интервал онлайн-работы
        и отправляет Ticket на review.

        Допустимо только из AT_WORK.

        actual_started_at здесь не передаётся:
        начало работы уже отражено записью AT_WORK.
        """
        TicketExecutionService._ensure_current_status(
            ticket=ticket,
            allowed_statuses=(TicketStatus.AT_WORK,),
            operation="submit ticket for review",
        )
        TicketExecutionService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecord(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=ticket.current_executor_id(),
            actual_finished_at=datetime.now(timezone.utc),
            comment=comment,
        )

        ticket.append_status(record)
        return record

    @staticmethod
    def record_completed_work_for_review(

        *,
        ticket: Ticket,
        actor_employee_id: int,
        executor_id: int,
        actual_started_at: datetime,
        actual_finished_at: datetime,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Регистрирует завершённую работу задним числом.

        Допустимо только из:
        - SCHEDULED;
        - ASSIGNED;
        - READY_TO_WORK.

        Создаёт READY_FOR_REVIEW напрямую.

        executor_id — сотрудник, который фактически выполнил работу.
        actor_employee_id — сотрудник, который внёс запись в систему.

        При наличии current executor фактический исполнитель обязан
        совпадать с ним. Если работу выполнил другой сотрудник,
        сначала должно быть отдельное бизнес-событие переназначения.
        """
        TicketExecutionService._ensure_current_status(
            ticket=ticket,
            allowed_statuses=(
                TicketStatus.SCHEDULED,
                TicketStatus.ASSIGNED,
                TicketStatus.READY_TO_WORK,
            ),
            operation="record completed work for review",
        )

        if executor_id <= 0:
            raise DomainOperationError(
                "Completed work requires executor_id"
            )

        if (
            ticket.has_executor()
            and ticket.current_executor_id() != executor_id
        ):
            raise DomainOperationError(
                "Completed work executor must match "
                "the current ticket executor"
            )

        record = TicketStatusRecord(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=executor_id,
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
            comment=comment,
        )

        ticket.append_status(record)
        return record

    @staticmethod
    def _ensure_current_status(
        *,
        ticket: Ticket,
        allowed_statuses: tuple[TicketStatus, ...],
        operation: str,
    ) -> None:
        current_status = ticket.current_status()

        if current_status in allowed_statuses:
            return

        allowed = ", ".join(
            str(status)
            for status in allowed_statuses
        )

        raise DomainOperationError(
            f"Cannot {operation} from {current_status.value}. "
            f"Allowed statuses: {allowed}"
        )

    @staticmethod
    def _ensure_current_executor(
        *,
        ticket: Ticket,
        actor_employee_id: int,
    ) -> None:
        current_executor_id = ticket.current_executor_id()

        if current_executor_id <= 0:
            raise DomainOperationError(
                "Ticket has no current executor"
            )

        if current_executor_id != actor_employee_id:
            raise DomainOperationError(
                "Only current executor can perform this action"
            )