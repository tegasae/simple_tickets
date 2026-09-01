# src/domain/services/ticket_execution_service.py

from datetime import datetime

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket


class TicketExecutionService:
    """
    Domain service для выполнения работы по Ticket.

    Не отвечает за:
    - RBAC;
    - permissions;
    - роли;
    - проверку enabled Admin;
    - проверку Department;
    - repository;
    - конкретные TicketStatus.

    TicketStatusRecord:
        - знает семантику текущего workflow-состояния;
        - создаёт корректные status-records.

    Ticket:
        - проверяет допустимость workflow-перехода;
        - добавляет status-record в историю.

    TicketExecutionService:
        - проверяет правила конкретных execution use cases;
        - проверяет связь действия с текущим executor.
    """

    @staticmethod
    def take_to_work(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Начинает обычную работу.

        Допустимо только из состояния,
        из которого можно начать новую работу.

        Выполнить действие может только current executor.
        """
        current_record = ticket.current_status_record()

        if not current_record.can_take_to_work():
            raise DomainOperationError(
                "Ticket cannot be taken to work "
                "from the current state"
            )

        executor_id = (
            TicketExecutionService
            ._current_executor_for_actor_or_raise(
                ticket=ticket,
                actor_employee_id=actor_employee_id,
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
    def pause_work(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Приостанавливает текущую работу.

        Исполнитель сохраняется.

        Выполнить действие может только current executor.
        """
        current_record = ticket.current_status_record()

        if not current_record.can_pause_work():
            raise DomainOperationError(
                "Ticket work cannot be paused "
                "from the current state"
            )

        executor_id = (
            TicketExecutionService
            ._current_executor_for_actor_or_raise(
                ticket=ticket,
                actor_employee_id=actor_employee_id,
            )
        )

        record = TicketStatusRecord.create_paused(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
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

        Исполнитель сохраняется.

        Выполнить действие может только current executor.
        """
        current_record = ticket.current_status_record()

        if not current_record.can_resume_work():
            raise DomainOperationError(
                "Ticket work cannot be resumed "
                "from the current state"
            )

        executor_id = (
            TicketExecutionService
            ._current_executor_for_actor_or_raise(
                ticket=ticket,
                actor_employee_id=actor_employee_id,
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
    def submit_for_review(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Завершает текущий интервал обычной работы
        и передаёт результат на review.

        actual_started_at в новой record отсутствует:
        начало работы уже зафиксировано предыдущей
        рабочей status-record.

        Выполнить действие может только current executor.
        """
        current_record = ticket.current_status_record()

        if not current_record.can_submit_for_review():
            raise DomainOperationError(
                "Ticket cannot be submitted for review "
                "from the current state"
            )

        executor_id = (
            TicketExecutionService
            ._current_executor_for_actor_or_raise(
                ticket=ticket,
                actor_employee_id=actor_employee_id,
            )
        )

        record = (
            TicketStatusRecord
            .create_ready_for_review_from_work(
                actor_employee_id=actor_employee_id,
                executor_id=executor_id,
                comment=comment,
            )
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
        Регистрирует завершённую работу ретроспективно.

        actor_employee_id:
            сотрудник, который внёс событие.

        executor_id:
            сотрудник, который фактически выполнил работу.

        Если в текущем состоянии уже имеется executor,
        фактический исполнитель должен совпадать с ним.

        Если работу выполнил другой сотрудник,
        сначала должно быть отдельное workflow-событие
        переназначения.
        """
        current_record = ticket.current_status_record()

        if not current_record.can_record_completed_work_for_review():
            raise DomainOperationError(
                "Completed work cannot be recorded for review "
                "from the current state"
            )

        if (
            ticket.has_executor()
            and ticket.current_executor_id() != executor_id
        ):
            raise DomainOperationError(
                "Completed work executor must match "
                "the current ticket executor"
            )

        record = (
            TicketStatusRecord
            .create_ready_for_review_retrospective(
                actor_employee_id=actor_employee_id,
                executor_id=executor_id,
                actual_started_at=actual_started_at,
                actual_finished_at=actual_finished_at,
                comment=comment,
            )
        )

        ticket.append_status(record)

        return record

    @staticmethod
    def _current_executor_for_actor_or_raise(
        *,
        ticket: Ticket,
        actor_employee_id: int,
    ) -> int:
        """
        Проверяет, что Ticket имеет current executor
        и что именно этот executor выполняет действие.

        Возвращает executor_id, чтобы вызывающий код
        не запрашивал его повторно.
        """
        executor_id = ticket.current_executor_id()

        if executor_id <= 0:
            raise DomainOperationError(
                "Ticket has no current executor"
            )

        if executor_id != actor_employee_id:
            raise DomainOperationError(
                "Only current executor can perform this action"
            )

        return executor_id