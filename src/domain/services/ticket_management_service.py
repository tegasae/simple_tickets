from __future__ import annotations

from datetime import datetime

from src.domain.policy.ticket_workflow_actor_policy import (
    TicketWorkflowActorKind,
    TicketWorkflowActorPolicy,
)
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.statuses.ticket_status_record_factory import TicketStatusRecordFactory
from src.domain.ticket import Ticket


class TicketManagementService:
    """
    Управленческие действия над заявкой.

    Здесь нет проверки RBAC, существования исполнителя,
    department и enabled/disabled состояния сотрудников.
    Это будет проверять application services.
    """

    @staticmethod
    def accept(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketStatusRecord:
        record = TicketStatusRecordFactory.accepted(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        TicketManagementService._append_status(
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
        record = TicketStatusRecordFactory.rejected(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        TicketManagementService._append_status(
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
        record = TicketStatusRecordFactory.deferred(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        TicketManagementService._append_status(
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
        record = TicketStatusRecordFactory.scheduled(
            actor_employee_id=actor_employee_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
        )

        TicketManagementService._append_status(
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
        record = TicketStatusRecordFactory.assigned(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            comment=comment,
        )

        TicketManagementService._append_status(
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
        record = TicketStatusRecordFactory.ready_to_work(
            actor_employee_id=actor_employee_id,
            executor_id=executor_id,
            planned_start_at=planned_start_at,
            planned_finish_at=planned_finish_at,
            comment=comment,
        )

        TicketManagementService._append_status(
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
        record = TicketStatusRecordFactory.cancelled(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        TicketManagementService._append_status(
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
        TicketWorkflowActorPolicy.ensure_actor_can_change_status(
            actor_kind=TicketWorkflowActorKind.MANAGER,
            current_status=ticket.current_status(),
            new_status=record.status,
        )

        ticket.append_status(record)