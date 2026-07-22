# src/application/services/ticket_user_application_service.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from src.application.dto.ticket_dto import TicketUserDTO
from src.application.helper.actor_helper import EmployeeActorHelper
from src.domain.client import Client
from src.domain.employee import User
from src.domain.exceptions import DomainOperationError
from src.domain.policies.ticket import TicketPolicy
from src.domain.rbac.permissions import UserPermission
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.services.ticket_review_service import TicketReviewService
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
    - RBAC checks;
    - загрузка агрегатов через UnitOfWork;
    - cross-aggregate validation;
    - вызов domain services;
    - сохранение Ticket и TicketUser в одной транзакции.

    Здесь нет:
    - ручного изменения status history внутренней Ticket;
    - workflow-графа статусов;
    - SQL;
    - repository-логики.
    """

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self._uow = uow
        self.actor = EmployeeActorHelper(self._uow)

    def create_from_user(
        self,
        *,
        ticket_user_dto: TicketUserDTO
    ) -> TicketUserApplicationResult:
        """
        User создаёт пользовательскую заявку.

        В одной транзакции создаются:

            TicketUser.CREATED

        и связанная внутренняя:

            Ticket.CREATED_FROM_TICKET_USER

        В Ticket:

            admin_id = 0
            user_ticket_id = saved TicketUser.ticket_id
            TicketStatusRecord.actor_employee_id = 0

        В TicketUser:

            StatusRecordTicketUser.actor_employee_id = actor_user_id

        ID для новых сущностей генерирует repository.
        Поэтому ticket_id и ticket_user_id должны быть 0.
        """
        if ticket_user_dto.ticket_id != 0:
            raise DomainOperationError(
                "create_from_user requires ticket_id = 0",
            )

        if ticket_user_dto.ticket_user_id != 0:
            raise DomainOperationError(
                "create_from_user requires ticket_user_id = 0",
            )

        now = datetime.now(timezone.utc)

        with self._uow:
            user = self._require_user_operation_for_ticket_user(
                actor_user_id=ticket_user_dto.actor_user_id
            )
            client = self._uow.clients.get(ticket_user_dto.client_id)
            TicketPolicy.ensure_client_enabled(client)
            TicketPolicy.ensure_user_belongs_to_client(
                user=user,
                client=client,
            )

            self._ensure_contact_user_valid(
                contact_user_id=ticket_user_dto.contact_user_id,
                client=client,
                main_user=user,
            )

            self._ensure_department_valid(
                department_id=ticket_user_dto.department_id,
            )

            ticket_user = TicketUser.create(
                ticket_id=0,
                client_id=ticket_user_dto.client_id,
                user_id=ticket_user_dto.actor_user_id,
                contact_user_id=ticket_user_dto.contact_user_id,
                text_of_ticket=ticket_user_dto.text_of_ticket,
                description=ticket_user_dto.description,
                urgency_level=ticket_user_dto.urgency_level,
                comment=ticket_user_dto.comment,
                date_created=now,
            )

            saved_ticket_user = self._uow.user_tickets.save(ticket_user)

            if saved_ticket_user is None:
                saved_ticket_user = ticket_user

            if saved_ticket_user.ticket_id == 0:
                raise DomainOperationError(
                    "TicketUser repository must assign ticket_id before "
                    "creating linked Ticket",
                )

            ticket = Ticket.create_from_ticket_user(
                ticket_id=0,
                client_id=ticket_user_dto.client_id,
                user_id=ticket_user_dto.actor_user_id,
                contact_user_id=ticket_user_dto.contact_user_id,
                text_of_ticket=ticket_user_dto.text_of_ticket,
                user_ticket_id=saved_ticket_user.ticket_id,
                department_id=ticket_user_dto.department_id,
                is_remote=ticket_user_dto.is_remote,
                description=ticket_user_dto.description,
                urgency_level=ticket_user_dto.urgency_level,
                date_created=now,
            )

            TicketPolicy.ensure_ticket_matches_ticket_user(
                ticket=ticket,
                ticket_user=saved_ticket_user,
            )

            saved_ticket = self._uow.tickets.save(ticket)

            if saved_ticket is None:
                saved_ticket = ticket

            self._uow.commit()

            return TicketUserApplicationResult(
                ticket=saved_ticket,
                ticket_user=saved_ticket_user,
                ticket_user_changed=True,
            )

    def cancel_by_user(
        self,
        *,
        ticket_user_dto:TicketUserDTO
    ) -> TicketUserApplicationResult:
        """
        User снимает свою заявку до принятия Admin.

        Разрешено только для заявки, созданной пользователем:

            Ticket.CREATED_FROM_TICKET_USER
            TicketUser.CREATED

        Не разрешено для заявки, которую Admin создал со слов пользователя:

            Ticket.CREATED
            TicketUser.CREATED

        Права:

            владелец заявки:
                UserPermission.TICKET_OPERATION

            пользователь той же организации:
                UserPermission.TICKET_OPERATION_ALL
        """
        with self._uow:
            user=self._require_user_operation_for_ticket_user(actor_user_id=ticket_user_dto.actor_user_id,user_id=ticket_user_dto.ticket_user_id)
            ticket = self._uow.tickets.get(ticket_user_dto.ticket_id)
            ticket_user = self._uow.user_tickets.get(ticket_user_dto.ticket_user_id)

            TicketPolicy.ensure_ticket_matches_ticket_user(
                ticket=ticket,
                ticket_user=ticket_user,
            )



            TicketPolicy.ensure_user_belongs_to_client(
                user=user,
                client=self._get_ticket_user_client(ticket_user),
            )

            TicketPolicy.ensure_ticket_has_no_admin_yet(
                ticket=ticket,
            )

            TicketManagementService.cancel_by_user(
                ticket=ticket,
                comment=ticket_user_dto.comment,
            )

            ticket_user_changed = TicketUserSyncService.sync_from_ticket(
                ticket=ticket,
                ticket_user=ticket_user,
                actor_employee_id=ticket_user_dto.actor_user_id,
                comment=ticket_user_dto.comment,
            )

            if ticket_user_changed:
                self._uow.user_tickets.save(ticket_user)

            self._uow.tickets.save(ticket)
            self._uow.commit()

            return TicketUserApplicationResult(
                ticket=ticket,
                ticket_user=ticket_user,
                ticket_user_changed=ticket_user_changed,
            )



    def confirm_execution_by_user(
        self,
        *,
        ticket_user_dto:TicketUserDTO
    ) -> TicketUserApplicationResult:
        """
        User подтверждает выполнение заявки.

        Права:

            владелец заявки:
                UserPermission.TICKET_OPERATION

            пользователь той же организации:
                UserPermission.TICKET_OPERATION_ALL

        TicketUser:

            WAITING_FOR_CONFIRMATION -> EXECUTION_CONFIRMED_BY_USER

        Ticket:

            READY_FOR_REVIEW -> EXECUTED

        Важно:
            здесь sync_from_ticket не используется,
            потому что инициатором является пользовательская сторона.
            Если синхронизировать от Ticket.EXECUTED,
            получится EXECUTION_CONFIRMED_BY_ADMIN, а это неверно.
        """
        with self._uow:
            ticket = self._uow.tickets.get(ticket_user_dto.ticket_id)
            ticket_user = self._uow.user_tickets.get(ticket_user_dto.ticket_user_id)

            TicketPolicy.ensure_ticket_matches_ticket_user(
                ticket=ticket,
                ticket_user=ticket_user,
            )

            user = self._require_user_operation_for_ticket_user(
                actor_user_id=ticket_user_dto.actor_user_id,
                user_id=ticket_user_dto.ticket_user_id,
            )

            TicketPolicy.ensure_user_belongs_to_client(
                user=user,
                client=self._get_ticket_user_client(ticket_user),
            )

            ticket_user.confirm_execution_by_user(
                actor_employee_id=ticket_user_dto.actor_user_id,
                comment=ticket_user_dto.comment,
            )

            TicketReviewService.confirm_execution(
                ticket=ticket,
                actor_employee_id=ticket_user_dto.actor_user_id,
                comment=ticket_user_dto.comment,
            )

            self._uow.user_tickets.save(ticket_user)
            self._uow.tickets.save(ticket)
            self._uow.commit()

            return TicketUserApplicationResult(
                ticket=ticket,
                ticket_user=ticket_user,
                ticket_user_changed=True,
            )




    def _require_user_operation_for_ticket_user(
        self,
        *,
        actor_user_id: int,
        user_id:int=0
    ) -> User:

        if actor_user_id == user_id or not user_id:
            user = self.actor.require_actor_user(
                actor_user_id=actor_user_id,
                permission=UserPermission.TICKET_OPERATION,
            )
        else:
            user = self.actor.require_actor_user(
                actor_user_id=actor_user_id,
                permission=UserPermission.TICKET_OPERATION_ALL,
            )

        return user



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

    def _get_ticket_user_client(
        self,
        ticket_user: TicketUser,
    ) -> Client:
        client = self._uow.clients.get(ticket_user.client_id)

        TicketPolicy.ensure_client_enabled(client)

        return client