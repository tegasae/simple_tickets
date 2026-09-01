# src/domain/services/ticket_user_sync_service.py

from __future__ import annotations

from typing import Final

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket
from src.domain.ticket_user import (
    TicketUser,
    TicketUserStatus,
)


_TICKET_TO_TICKET_USER_STATUS: Final[
    dict[TicketStatus, TicketUserStatus]
] = {
    TicketStatus.ACCEPTED:
        TicketUserStatus.CONFIRMED_BY_ADMIN,

    TicketStatus.DEFERRED:
        TicketUserStatus.IN_WORK,
    TicketStatus.SCHEDULED:
        TicketUserStatus.IN_WORK,
    TicketStatus.ASSIGNED:
        TicketUserStatus.IN_WORK,
    TicketStatus.READY_TO_WORK:
        TicketUserStatus.IN_WORK,
    TicketStatus.AT_WORK:
        TicketUserStatus.IN_WORK,
    TicketStatus.PAUSED:
        TicketUserStatus.IN_WORK,

    TicketStatus.READY_FOR_REVIEW:
        TicketUserStatus.WAITING_FOR_CONFIRMATION,

    TicketStatus.EXECUTED:
        TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN,

    TicketStatus.REJECTED:
        TicketUserStatus.CANCELLED_BY_ADMIN,
    TicketStatus.CANCELLED:
        TicketUserStatus.CANCELLED_BY_ADMIN,
}


class TicketUserSyncService:
    """
    Синхронизация пользовательского workflow TicketUser
    после изменения внутренней Ticket.

    Это cross-aggregate domain service.

    Он знает оба workflow, потому что именно это является
    его предметной ответственностью:

        Ticket state -> TicketUser state

    Не отвечает за:
    - RBAC;
    - permissions;
    - repository;
    - UnitOfWork;
    - загрузку aggregates;
    - сохранение aggregates;
    - enabled/disabled Employee/Client.

    Пользовательские события идут в противоположном направлении:

        TicketUser -> Ticket

    Поэтому CANCELLED_BY_USER здесь не синхронизируется.
    """

    @staticmethod
    def sync_from_ticket(
        *,
        ticket: Ticket,
        ticket_user: TicketUser,
        actor_employee_id: int,
        comment: str = "",
    ) -> bool:
        """
        Приводит TicketUser к состоянию,
        соответствующему текущему состоянию Ticket.

        Returns:
            True:
                TicketUser была изменена.

            False:
                изменение не требуется.

        Terminal TicketUser никогда не изменяется.

        В частности, это защищает:

            EXECUTION_CONFIRMED_BY_USER

        от последующего изменения на:

            EXECUTION_CONFIRMED_BY_ADMIN.
        """
        TicketUserSyncService._ensure_linked(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        if ticket_user.is_terminal():
            return False

        target_status = (
            TicketUserSyncService.target_status_for_ticket(
                ticket=ticket,
            )
        )

        if target_status is None:
            return False

        if ticket_user.current_status() == target_status:
            return False

        TicketUserSyncService._apply_target_status(
            ticket_user=ticket_user,
            target_status=target_status,
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        return True

    @staticmethod
    def target_status_for_ticket(
        *,
        ticket: Ticket,
    ) -> TicketUserStatus | None:
        """
        Возвращает состояние TicketUser,
        соответствующее текущему состоянию Ticket.

        None означает, что синхронизация не требуется.

        Начальные состояния Ticket:

            CREATED
            CREATED_FROM_TICKET_USER

        здесь не обрабатываются.

        Начальное состояние TicketUser создаётся
        явно соответствующим use case.
        """
        ticket_status = (
            ticket.current_status_record().status
        )

        return _TICKET_TO_TICKET_USER_STATUS.get(
            ticket_status
        )

    @staticmethod
    def _apply_target_status(
        *,
        ticket_user: TicketUser,
        target_status: TicketUserStatus,
        actor_employee_id: int,
        comment: str,
    ) -> None:
        if actor_employee_id <= 0:
            raise DomainOperationError(
                "Actor employee id must be positive"
            )

        if target_status == TicketUserStatus.CONFIRMED_BY_ADMIN:
            ticket_user.confirm_by_admin(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
            return

        if target_status == TicketUserStatus.IN_WORK:
            ticket_user.mark_in_work(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
            return

        if (
            target_status
            == TicketUserStatus.WAITING_FOR_CONFIRMATION
        ):
            ticket_user.mark_waiting_for_confirmation(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
            return

        if (
            target_status
            == TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN
        ):
            ticket_user.confirm_execution_by_admin(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
            return

        if target_status == TicketUserStatus.CANCELLED_BY_ADMIN:
            ticket_user.cancel_by_admin(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
            return

        raise DomainOperationError(
            "Unsupported TicketUser sync target status: "
            f"{target_status.value}"
        )

    @staticmethod
    def _ensure_linked(
        *,
        ticket: Ticket,
        ticket_user: TicketUser,
    ) -> None:
        """
        Проверяет только необходимые для sync связи.

        Обычные изменяемые данные Ticket/TicketUser
        здесь намеренно не сравниваются.
        """
        if ticket.user_ticket_id == 0:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} "
                "is not linked to TicketUser"
            )

        if ticket.user_ticket_id != ticket_user.ticket_id:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} is linked to "
                f"TicketUser {ticket.user_ticket_id}, "
                f"not {ticket_user.ticket_id}"
            )

        if ticket.client_id != ticket_user.client_id:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} and TicketUser "
                f"{ticket_user.ticket_id} belong to "
                "different clients"
            )

        if ticket.user_id != ticket_user.user_id:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} and TicketUser "
                f"{ticket_user.ticket_id} belong to "
                "different users"
            )