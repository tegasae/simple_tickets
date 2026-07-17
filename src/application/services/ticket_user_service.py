# src/application/services/ticket_user_application_service.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.policy.ticket import TicketPolicy
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.services.ticket_user_sync_service import TicketUserSyncService
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from src.domain.uow.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class TicketUserApplicationResult:
    ticket: Ticket
    ticket_user: TicketUser
    ticket_user_changed: bool


class TicketUserApplicationService:
    """
    Application service для пользовательских заявок.

    Координирует две связанные сущности:

        TicketUser — внешний пользовательский workflow.
        Ticket     — внутренний workflow заявки.

    Здесь есть:
    - загрузка агрегатов через UnitOfWork;
    - проверка связей между агрегатами;
    - вызов domain services;
    - сохранение Ticket и TicketUser в одной транзакции.

    Здесь нет:
    - ручного изменения status history;
    - workflow-графа статусов;
    - SQL;
    - repository-логики.

    RBAC можно добавить сюда позже через Authorizer.
    """

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self._uow = uow

    def create_from_user(
        self,
        *,
        ticket_id: int,
        ticket_user_id: int,
        client_id: int,
        actor_user_id: int,
        text_of_ticket: str,
        contact_user_id: int = 0,
        department_id: int = 0,
        is_remote: bool = False,
        description: str = "",
        urgency_level: int = 0,
        comment: str = "",
    ) -> TicketUserApplicationResult:
        """
        User создаёт пользовательскую заявку.

        В одной транзакции создаются:

            TicketUser.CREATED

        и связанная внутренняя:

            Ticket.CREATED_FROM_TICKET_USER

        В Ticket:

            admin_id = 0
            user_ticket_id = TicketUser.ticket_id
            TicketStatusRecord.actor_employee_id = 0

        В TicketUser:

            StatusRecordTicketUser.actor_employee_id = actor_user_id
        """
        now = datetime.now(timezone.utc)

        with self._uow:
            client = self._uow.clients.get(client_id)
            user = self._uow.users.get(actor_user_id)

            TicketPolicy.ensure_client_enabled(client)
            TicketPolicy.ensure_user_enabled(user)
            TicketPolicy.ensure_user_belongs_to_client(
                user=user,
                client=client,
            )

            self._ensure_contact_user_valid(
                contact_user_id=contact_user_id,
                client=client,
                main_user=user,
            )

            self._ensure_department_valid(
                department_id=department_id,
            )

            ticket_user = TicketUser.create(
                ticket_id=ticket_user_id,
                client_id=client_id,
                user_id=actor_user_id,
                contact_user_id=contact_user_id,
                text_of_ticket=text_of_ticket,
                description=description,
                urgency_level=urgency_level,
                comment=comment,
                date_created=now,
            )

            ticket = Ticket.create_from_ticket_user(
                ticket_id=ticket_id,
                client_id=client_id,
                user_id=actor_user_id,
                contact_user_id=contact_user_id,
                text_of_ticket=text_of_ticket,
                user_ticket_id=ticket_user_id,
                department_id=department_id,
                is_remote=is_remote,
                description=description,
                urgency_level=urgency_level,
                date_created=now,
            )

            TicketPolicy.ensure_ticket_matches_ticket_user(
                ticket=ticket,
                ticket_user=ticket_user,
            )

            self._uow.user_tickets.save(ticket_user)
            self._uow.tickets.save(ticket)
            self._uow.commit()

            return TicketUserApplicationResult(
                ticket=ticket,
                ticket_user=ticket_user,
                ticket_user_changed=True,
            )

    def cancel_by_user(
        self,
        *,
        ticket_id: int,
        ticket_user_id: int,
        actor_user_id: int,
        comment: str = "",
    ) -> TicketUserApplicationResult:
        """
        User снимает свою заявку до принятия Admin.

        Ticket:

            CREATED_FROM_TICKET_USER -> CANCELLED_BY_USER
            TicketStatusRecord.actor_employee_id = 0

        TicketUser:

            CREATED -> CANCELLED_BY_USER
            StatusRecordTicketUser.actor_employee_id = actor_user_id
        """
        with self._uow:
            ticket = self._uow.tickets.get(ticket_id)
            ticket_user = self._uow.user_tickets.get(ticket_user_id)
            user = self._uow.users.get(actor_user_id)

            TicketPolicy.ensure_user_enabled(user)
            TicketPolicy.ensure_user_matches_ticket_user(
                user=user,
                ticket_user=ticket_user,
            )
            TicketPolicy.ensure_user_matches_ticket(
                user=user,
                ticket=ticket,
            )
            TicketPolicy.ensure_ticket_matches_ticket_user(
                ticket=ticket,
                ticket_user=ticket_user,
            )
            TicketPolicy.ensure_ticket_has_no_admin_yet(
                ticket=ticket,
            )

            TicketManagementService.cancel_by_user(
                ticket=ticket,
                comment=comment,
            )

            ticket_user_changed = TicketUserSyncService.sync_from_ticket(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor_user_id,
                comment=comment,
            )

            self._uow.user_tickets.save(ticket_user)
            self._uow.tickets.save(ticket)
            self._uow.commit()

            return TicketUserApplicationResult(
                ticket=ticket,
                ticket_user=ticket_user,
                ticket_user_changed=ticket_user_changed,
            )

    def accept_user_ticket(
        self,
        *,
        ticket_id: int,
        ticket_user_id: int,
        actor_admin_id: int,
        comment: str = "",
    ) -> TicketUserApplicationResult:
        """
        Admin принимает пользовательскую заявку.

        Ticket:

            CREATED_FROM_TICKET_USER -> ACCEPTED
            TicketStatusRecord.actor_employee_id = actor_admin_id
            ticket.admin_id = actor_admin_id

        TicketUser:

            CREATED -> CONFIRMED_BY_ADMIN
            StatusRecordTicketUser.actor_employee_id = actor_admin_id
        """
        with self._uow:
            ticket = self._uow.tickets.get(ticket_id)
            ticket_user = self._uow.user_tickets.get(ticket_user_id)
            admin = self._uow.admins.get(actor_admin_id)

            self._ensure_admin_can_manage_user_ticket(
                admin=admin,
                ticket=ticket,
                ticket_user=ticket_user,
            )

            TicketPolicy.ensure_ticket_has_no_admin_yet(
                ticket=ticket,
            )

            TicketManagementService.accept(
                ticket=ticket,
                actor_employee_id=actor_admin_id,
                comment=comment,
            )

            ticket_user_changed = TicketUserSyncService.sync_from_ticket(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor_admin_id,
                comment=comment,
            )

            self._uow.user_tickets.save(ticket_user)
            self._uow.tickets.save(ticket)
            self._uow.commit()

            return TicketUserApplicationResult(
                ticket=ticket,
                ticket_user=ticket_user,
                ticket_user_changed=ticket_user_changed,
            )

    def reject_user_ticket(
        self,
        *,
        ticket_id: int,
        ticket_user_id: int,
        actor_admin_id: int,
        comment: str,
    ) -> TicketUserApplicationResult:
        """
        Admin отклоняет пользовательскую заявку до принятия.

        Ticket:

            CREATED_FROM_TICKET_USER -> REJECTED
            TicketStatusRecord.actor_employee_id = actor_admin_id

        TicketUser:

            CREATED -> CANCELLED_BY_ADMIN
            StatusRecordTicketUser.actor_employee_id = actor_admin_id

        comment обязателен, потому что REJECTED требует comment.
        """
        if not comment.strip():
            raise DomainOperationError(
                "Reject user ticket requires comment",
            )

        with self._uow:
            ticket = self._uow.tickets.get(ticket_id)
            ticket_user = self._uow.user_tickets.get(ticket_user_id)
            admin = self._uow.admins.get(actor_admin_id)

            self._ensure_admin_can_manage_user_ticket(
                admin=admin,
                ticket=ticket,
                ticket_user=ticket_user,
            )

            TicketPolicy.ensure_ticket_has_no_admin_yet(
                ticket=ticket,
            )

            TicketManagementService.reject(
                ticket=ticket,
                actor_employee_id=actor_admin_id,
                comment=comment,
            )

            ticket_user_changed = TicketUserSyncService.sync_from_ticket(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor_admin_id,
                comment=comment,
            )

            self._uow.user_tickets.save(ticket_user)
            self._uow.tickets.save(ticket)
            self._uow.commit()

            return TicketUserApplicationResult(
                ticket=ticket,
                ticket_user=ticket_user,
                ticket_user_changed=ticket_user_changed,
            )

    def sync_ticket_user_after_ticket_change(
        self,
        *,
        ticket_id: int,
        ticket_user_id: int,
        actor_employee_id: int,
        comment: str = "",
    ) -> TicketUserApplicationResult:
        """
        Синхронизирует TicketUser после изменения внутренней Ticket.

        Этот метод не меняет Ticket.
        Он только читает её текущий статус и обновляет TicketUser.

        Примеры внутренних статусов Ticket:

            ACCEPTED
            ASSIGNED
            READY_TO_WORK
            AT_WORK
            READY_FOR_REVIEW
            EXECUTED
            CANCELLED
        """
        if actor_employee_id <= 0:
            raise DomainOperationError(
                "Actor employee id must be positive",
            )

        with self._uow:
            ticket = self._uow.tickets.get(ticket_id)
            ticket_user = self._uow.user_tickets.get(ticket_user_id)

            TicketPolicy.ensure_ticket_matches_ticket_user(
                ticket=ticket,
                ticket_user=ticket_user,
            )

            ticket_user_changed = TicketUserSyncService.sync_from_ticket(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=actor_employee_id,
                comment=comment,
            )

            if ticket_user_changed:
                self._uow.user_tickets.save(ticket_user)

            self._uow.commit()

            return TicketUserApplicationResult(
                ticket=ticket,
                ticket_user=ticket_user,
                ticket_user_changed=ticket_user_changed,
            )

    def _ensure_admin_can_manage_user_ticket(
        self,
        *,
        admin: Admin,
        ticket: Ticket,
        ticket_user: TicketUser,
    ) -> None:
        TicketPolicy.ensure_admin_enabled(admin)

        client = self._uow.clients.get(ticket_user.client_id)
        user = self._uow.users.get(ticket_user.user_id)

        TicketPolicy.ensure_client_enabled(client)
        TicketPolicy.ensure_user_enabled(user)
        TicketPolicy.ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

        TicketPolicy.ensure_ticket_matches_ticket_user(
            ticket=ticket,
            ticket_user=ticket_user,
        )

    def _ensure_contact_user_valid(
        self,
        *,
        contact_user_id: int,
        client: Client,
        main_user: User,
    ) -> None:
        if contact_user_id == 0:
            return

        if contact_user_id == main_user.employee_id:
            return

        contact_user = self._uow.users.get(contact_user_id)

        TicketPolicy.ensure_user_enabled(contact_user)
        TicketPolicy.ensure_contact_user_belongs_to_client(
            contact_user=contact_user,
            client=client,
        )

    def _ensure_department_valid(
        self,
        *,
        department_id: int,
    ) -> None:
        if department_id == 0:
            return

        self._uow.departments.get(department_id)