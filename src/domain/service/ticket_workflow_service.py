# src/domain/services/ticket_workflow_service.py

from __future__ import annotations

from datetime import datetime

from src.domain.exceptions import DomainOperationError
from src.domain.policy.ticket_workflow_actor_policy import (
    TicketWorkflowActorKind,
    TicketWorkflowActorPolicy,
)
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.statuses.ticket_status_record_factory import TicketStatusRecordFactory
from src.domain.ticket import Ticket


class TicketWorkflowService:
    """
    Domain service для workflow-операций над Ticket.

    Этот сервис:
    - создаёт TicketStatusRecord через factory;
    - проверяет actor-specific workflow rule;
    - добавляет status-record в Ticket.

    Этот сервис НЕ проверяет:
    - RBAC permissions;
    - существует ли actor в БД;
    - существует ли executor в БД;
    - enabled/disabled Admin;
    - enabled/disabled Department;
    - executor.department_id == ticket.department_id.

    Всё это должно проверяться выше — в application service.
    """

    # ----------------------------
    # Executor operations
    # ----------------------------

    @staticmethod
    def take_to_work(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Исполнитель начинает работу над заявкой.

        Допустимые статусы:
        - ASSIGNED
        - READY_TO_WORK

        Важно:
        actor должен быть текущим executor заявки.
        """

        TicketWorkflowService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecordFactory.at_work(
            actor_employee_id=actor_employee_id,
            executor_id=ticket.current_executor_id(),
            comment=comment,
        )

        TicketWorkflowService._append_executor_status(
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
        """
        Исполнитель временно приостанавливает работу.

        Допустимый переход:
        - AT_WORK -> PAUSED

        Важно:
        actor должен быть текущим executor заявки.
        """

        TicketWorkflowService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecordFactory.paused(
            actor_employee_id=actor_employee_id,
            executor_id=ticket.current_executor_id(),
            comment=comment,
        )

        TicketWorkflowService._append_executor_status(
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
        """
        Исполнитель возвращается к работе после паузы.

        Допустимый переход:
        - PAUSED -> AT_WORK

        Важно:
        actor должен быть текущим executor заявки.
        """

        TicketWorkflowService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecordFactory.at_work(
            actor_employee_id=actor_employee_id,
            executor_id=ticket.current_executor_id(),
            comment=comment,
        )

        TicketWorkflowService._append_executor_status(
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
        """
        Исполнитель вносит выполненную offline-работу задним числом.

        Допустимые переходы:
        - ASSIGNED -> OFFLINE_WORK
        - READY_TO_WORK -> OFFLINE_WORK

        Важно:
        - actor должен быть текущим executor заявки;
        - actual_started_at обязателен;
        - actual_finished_at обязателен.
        """

        TicketWorkflowService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        record = TicketStatusRecordFactory.offline_work(
            actor_employee_id=actor_employee_id,
            executor_id=ticket.current_executor_id(),
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
            comment=comment,
        )

        TicketWorkflowService._append_executor_status(
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
        """
        Исполнитель отправляет результат на проверку.

        Допустимые переходы:
        - AT_WORK -> READY_FOR_REVIEW
        - OFFLINE_WORK -> READY_FOR_REVIEW

        Важно:
        actor должен быть текущим executor заявки.
        """

        TicketWorkflowService._ensure_current_executor(
            ticket=ticket,
            actor_employee_id=actor_employee_id,
        )

        actual_finished_at = TicketWorkflowService._resolve_actual_finished_at(
            ticket=ticket,
        )

        record = TicketStatusRecordFactory.ready_for_review(
            actor_employee_id=actor_employee_id,
            executor_id=ticket.current_executor_id(),
            actual_finished_at=actual_finished_at,
            comment=comment,
        )

        TicketWorkflowService._append_executor_status(
            ticket=ticket,
            record=record,
        )

        return record

    # ----------------------------
    # Manager operations
    # ----------------------------

    @staticmethod
    def accept(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Manager принимает созданную заявку.

        Допустимый переход:
        - CREATED -> ACCEPTED
        """

        record = TicketStatusRecordFactory.accepted(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        TicketWorkflowService._append_manager_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def reject(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str,
    ) -> TicketStatusRecord:
        """
        Manager отклоняет заявку до принятия.

        Допустимый переход:
        - CREATED -> REJECTED

        comment обязателен.
        """

        record = TicketStatusRecordFactory.rejected(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        TicketWorkflowService._append_manager_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def defer(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str,
    ) -> TicketStatusRecord:
        """
        Manager откладывает заявку.

        Например:
        - нужны данные от клиента;
        - нужно согласование;
        - нужен доступ;
        - нужна управленческая пауза.

        comment обязателен.
        """

        record = TicketStatusRecordFactory.deferred(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        TicketWorkflowService._append_manager_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def schedule(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        planned_start_at: datetime,
        planned_finish_at: datetime | None = None,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Manager планирует заявку без назначения исполнителя.

        Создаёт статус:
        - SCHEDULED

        Смысл:
        - planned_start_at есть;
        - executor_id = 0.
        """

        record = TicketStatusRecordFactory.scheduled(
            actor_employee_id=actor_employee_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
        )

        TicketWorkflowService._append_manager_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def assign(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        executor_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Manager назначает исполнителя без планового времени.

        Создаёт статус:
        - ASSIGNED

        Смысл:
        - executor_id > 0;
        - planned_start_at отсутствует.
        """

        record = TicketStatusRecordFactory.assigned(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
        )

        TicketWorkflowService._append_manager_status(
            ticket=ticket,
            record=record,
        )

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
    ) -> TicketStatusRecord:
        """
        Manager назначает исполнителя и плановое время.

        Создаёт статус:
        - READY_TO_WORK

        Смысл:
        - executor_id > 0;
        - planned_start_at есть.
        """

        record = TicketStatusRecordFactory.ready_to_work(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
        )

        TicketWorkflowService._append_manager_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def cancel(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str,
    ) -> TicketStatusRecord:
        """
        Manager отменяет уже принятую заявку.

        Допустимые переходы определяются общим workflow-графом.

        Важно:
        - CREATED -> CANCELLED запрещён;
        - для CREATED есть REJECTED;
        - comment обязателен.
        """

        record = TicketStatusRecordFactory.cancelled(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        TicketWorkflowService._append_manager_status(
            ticket=ticket,
            record=record,
        )

        return record

    # ----------------------------
    # Internal helpers
    # ----------------------------

    @staticmethod
    def _append_executor_status(
        *,
        ticket: Ticket,
        record: TicketStatusRecord,
    ) -> None:
        """
        Проверяет executor actor-policy и добавляет статус в Ticket.

        ticket.append_status(record) отдельно проверит общий workflow graph.
        Actor-policy тоже вызывает общий graph, чтобы executor-rules
        не могли случайно расширить workflow.
        """

        TicketWorkflowActorPolicy.ensure_actor_can_change_status(
            actor_kind=TicketWorkflowActorKind.EXECUTOR,
            current_status=ticket.current_status(),
            new_status=record.status,
        )

        ticket.append_status(record)

    @staticmethod
    def _append_manager_status(
        *,
        ticket: Ticket,
        record: TicketStatusRecord,
    ) -> None:
        """
        Проверяет manager actor-policy и добавляет статус в Ticket.

        ticket.append_status(record) отдельно проверит общий workflow graph.
        Actor-policy тоже вызывает общий graph, чтобы manager-rules
        не могли случайно расширить workflow.
        """

        TicketWorkflowActorPolicy.ensure_actor_can_change_status(
            actor_kind=TicketWorkflowActorKind.MANAGER,
            current_status=ticket.current_status(),
            new_status=record.status,
        )

        ticket.append_status(record)

    @staticmethod
    def _ensure_current_executor(
        *,
        ticket: Ticket,
        actor_employee_id: int,
    ) -> None:
        """
        Executor operation может выполнить только текущий executor заявки.
        """

        if actor_employee_id <= 0:
            raise DomainOperationError("Actor employee ID must be positive")

        current_executor_id = ticket.current_executor_id()

        if current_executor_id == 0:
            raise DomainOperationError("Ticket has no current executor")

        if actor_employee_id != current_executor_id:
            raise DomainOperationError(
                f"Actor {actor_employee_id} is not current ticket executor"
            )

    @staticmethod
    def _resolve_actual_finished_at(
        *,
        ticket: Ticket,
    ) -> datetime | None:
        """
        Для AT_WORK actual_finished_at ставит factory автоматически.

        Для OFFLINE_WORK фактическое окончание уже известно,
        поэтому READY_FOR_REVIEW должен сохранить именно его,
        а не текущее время внесения записи.
        """

        current_record = ticket.current_status_record()

        if current_record.status == TicketStatus.OFFLINE_WORK:
            return current_record.actual_finished_at

        return None