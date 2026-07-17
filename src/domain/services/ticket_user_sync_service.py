# src/domain/services/ticket_user_sync_service.py

from __future__ import annotations

from typing import Final

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser, TicketUserStatus


_TICKET_TO_TICKET_USER_STATUS: Final[dict[TicketStatus, TicketUserStatus]] = {
    TicketStatus.ACCEPTED: TicketUserStatus.CONFIRMED_BY_ADMIN,

    TicketStatus.DEFERRED: TicketUserStatus.IN_WORK,
    TicketStatus.SCHEDULED: TicketUserStatus.IN_WORK,
    TicketStatus.ASSIGNED: TicketUserStatus.IN_WORK,
    TicketStatus.READY_TO_WORK: TicketUserStatus.IN_WORK,
    TicketStatus.AT_WORK: TicketUserStatus.IN_WORK,
    TicketStatus.PAUSED: TicketUserStatus.IN_WORK,

    TicketStatus.READY_FOR_REVIEW: TicketUserStatus.WAITING_FOR_CONFIRMATION,

    TicketStatus.EXECUTED: TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN,

    TicketStatus.REJECTED: TicketUserStatus.CANCELLED_BY_ADMIN,
    TicketStatus.CANCELLED: TicketUserStatus.CANCELLED_BY_ADMIN,
    TicketStatus.CANCELLED_BY_USER: TicketUserStatus.CANCELLED_BY_USER,
}


class TicketUserSyncService:
    """
    Синхронизирует пользовательскую TicketUser с внутренней Ticket.

    Этот сервис не отвечает за:
    - RBAC;
    - загрузку из repository;
    - сохранение в repository;
    - открытие транзакции;
    - проверку enabled/disabled сотрудников;
    - проверку существования Admin/User/Client.

    Application service должен:
    - загрузить Ticket;
    - загрузить TicketUser;
    - изменить Ticket;
    - вызвать этот sync-service;
    - сохранить обе сущности в одной UnitOfWork.
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
        Применяет состояние внутренней Ticket к связанной TicketUser.

        Returns:
            True, если TicketUser была изменена;
            False, если изменение не потребовалось.

        Важное правило:
            если TicketUser уже terminal, мы её не трогаем.

        Это защищает, например, состояние:

            EXECUTION_CONFIRMED_BY_USER

        от последующего перезаписывания на:

            EXECUTION_CONFIRMED_BY_ADMIN
        """
        TicketUserSyncService._ensure_linked(
            ticket=ticket,
            ticket_user=ticket_user,
        )

        if ticket_user.is_terminal():
            return False

        target_status = TicketUserSyncService.target_status_for_ticket(
            ticket=ticket,
        )

        if target_status is None:
            return False

        current_status = ticket_user.current_status()

        if current_status == target_status:
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
        Возвращает TicketUserStatus, соответствующий текущему TicketStatus.

        None означает:
            для этого TicketStatus синхронизация TicketUser не нужна.

        Например:
            Ticket.CREATED
            Ticket.CREATED_FROM_TICKET_USER

        не синхронизируются здесь, потому что начальное состояние TicketUser
        создаётся явно в application service.
        """
        ticket_status = ticket.current_status()

        return _TICKET_TO_TICKET_USER_STATUS.get(ticket_status)

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
                "Actor employee id must be positive",
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

        if target_status == TicketUserStatus.WAITING_FOR_CONFIRMATION:
            ticket_user.mark_waiting_for_confirmation(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
            return

        if target_status == TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN:
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

        if target_status == TicketUserStatus.CANCELLED_BY_USER:
            ticket_user.cancel_by_user(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
            return

        raise DomainOperationError(
            f"Unsupported TicketUser sync target status: {str(target_status)}",
        )

    @staticmethod
    def _ensure_linked(
        *,
        ticket: Ticket,
        ticket_user: TicketUser,
    ) -> None:
        if ticket.user_ticket_id == 0:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} is not linked to TicketUser",
            )

        if ticket.user_ticket_id != ticket_user.ticket_id:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} is linked to TicketUser "
                f"{ticket.user_ticket_id}, not {ticket_user.ticket_id}",
            )

        if ticket.client_id != ticket_user.client_id:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} and TicketUser "
                f"{ticket_user.ticket_id} belong to different clients",
            )

        if ticket.user_id != ticket_user.user_id:
            raise DomainOperationError(
                f"Ticket {ticket.ticket_id} and TicketUser "
                f"{ticket_user.ticket_id} belong to different users",
            )