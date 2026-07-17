from datetime import UTC, datetime

from src.domain.exceptions import ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket


class TicketManagementService:
    """
    Управленческие действия над заявкой.

    Здесь нет проверки RBAC, существования исполнителя,
    department и enabled/disabled состояния сотрудников.
    Это проверяют application services.
    """

    @staticmethod
    def accept(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
        date_created: datetime | None = None,
    ) -> TicketStatusRecord:
        if actor_employee_id <= 0:
            raise ItemValidationError("Actor employee id must be positive.")

        now = date_created or datetime.now(UTC)

        record = TicketStatusRecord(
            status_id=0,
            actor_employee_id=actor_employee_id,
            status=TicketStatus.ACCEPTED,
            date_created=now,
            executor_id=0,
            planned_start_at=None,
            planned_finish_at=None,
            actual_started_at=None,
            actual_finished_at=None,
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
        record = TicketStatusRecord(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.REJECTED,
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
        record = TicketStatusRecord(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.DEFERRED,
            comment=comment,
        )

        TicketManagementService._append_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def handle_client_disabled(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str,
    ) -> bool:
        """
        Применяет workflow-политику после отключения Client.

        CREATED / CREATED_FROM_TICKET_USER:
            -> REJECTED

        ACCEPTED / SCHEDULED / ASSIGNED / READY_TO_WORK:
            -> DEFERRED

        Остальные статусы:
            без изменений.

        Returns:
            True, если Ticket изменилась;
            False, если Ticket осталась без изменений.

        Для REJECTED и DEFERRED comment обязателен.
        """
        current_status = ticket.current_status()

        if current_status in {
            TicketStatus.CREATED,
            TicketStatus.CREATED_FROM_TICKET_USER,
        }:
            TicketManagementService.reject(
                ticket=ticket,
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
            return True

        if current_status in {
            TicketStatus.ACCEPTED,
            TicketStatus.SCHEDULED,
            TicketStatus.ASSIGNED,
            TicketStatus.READY_TO_WORK,
        }:
            TicketManagementService.defer(
                ticket=ticket,
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
            return True

        return False

    @staticmethod
    def schedule(
        *,
        ticket: Ticket,
        actor_employee_id: int,
        planned_start_at: datetime,
        planned_finish_at: datetime | None = None,
        comment: str = "",
    ) -> TicketStatusRecord:
        record = TicketStatusRecord(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.SCHEDULED,
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
        record = TicketStatusRecord(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.ASSIGNED,
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
        record = TicketStatusRecord(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.READY_TO_WORK,
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
        record = TicketStatusRecord(
            actor_employee_id=actor_employee_id,
            status=TicketStatus.CANCELLED,
            comment=comment,
        )

        TicketManagementService._append_status(
            ticket=ticket,
            record=record,
        )

        return record

    @staticmethod
    def cancel_by_user(
        *,
        ticket: Ticket,
        comment: str = "",
    ) -> TicketStatusRecord:
        """
        Снимает пользовательскую заявку до принятия Admin.

        Разрешённый переход:
            CREATED_FROM_TICKET_USER -> CANCELLED_BY_USER

        actor_employee_id = 0 означает:
            действие пришло из пользовательского workflow;
            конкретный User хранится в TicketUser history.
        """
        record = TicketStatusRecord(
            actor_employee_id=0,
            status=TicketStatus.CANCELLED_BY_USER,
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
        ticket.append_status(record)
