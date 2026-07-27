# src/application/services/ticket_user_application_service.py

from __future__ import annotations

from datetime import datetime, timezone

from src.application.assemblers.assembler import TicketUserAssembler
from src.application.dto.ticket_dto import TicketUserDTO, TicketUserResponseDTO
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
    - admin-side workflow внутренней Ticket;
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

    # --------------------------------
    # Commands
    # --------------------------------

    def create_from_user(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
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

        if ticket_user_dto.ticket_user_id != 0:
            raise DomainOperationError(
                "create_from_user requires ticket_user_id = 0",
            )

        now = datetime.now(timezone.utc)

        with self._uow:
            user = self._require_user_operation(
                actor_user_id=ticket_user_dto.actor_user_id,
            )

            client = self._get_client(ticket_user_dto.client_id)

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

            self._uow.tickets.save(ticket)
            self._uow.commit()

            return TicketUserAssembler.to_dto(saved_ticket_user)

    def cancel_by_user(
            self,
            *,
            ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
        """
        User снимает свою заявку до принятия Admin.

        Права:

            владелец заявки:
                UserPermission.TICKET_OPERATION

            пользователь той же организации:
                UserPermission.TICKET_OPERATION_ALL

        Внутренний переход:

            Ticket.CREATED_FROM_TICKET_USER -> Ticket.CANCELLED_BY_USER

        Пользовательский переход:

            TicketUser.CREATED -> TicketUser.CANCELLED_BY_USER

        Важно:
            application service не проверяет workflow-статус напрямую.
            Это делает TicketManagementService.cancel_by_user().
        """
        with self._uow:
            ticket = self._uow.tickets.get_by_user_ticket_id(ticket_user_dto.ticket_user_id)
            ticket_user = self._uow.user_tickets.get(
                ticket_user_dto.ticket_user_id,
            )

            TicketPolicy.ensure_ticket_matches_ticket_user(
                ticket=ticket,
                ticket_user=ticket_user,
            )

            self._require_user_operation_for_ticket_user(
                actor_user_id=ticket_user_dto.actor_user_id,
                ticket_user=ticket_user,
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

            return TicketUserAssembler.to_dto(ticket_user)

    def confirm_execution_by_user(
            self,
            *,
            ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
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
            получится EXECUTION_CONFIRMED_BY_ADMIN.
        """
        with self._uow:
            ticket = self._uow.tickets.get_by_user_ticket_id(ticket_user_dto.ticket_user_id)
            ticket_user = self._uow.user_tickets.get(
                ticket_user_dto.ticket_user_id,
            )

            TicketPolicy.ensure_ticket_matches_ticket_user(
                ticket=ticket,
                ticket_user=ticket_user,
            )

            self._require_user_operation_for_ticket_user(
                actor_user_id=ticket_user_dto.actor_user_id,
                ticket_user=ticket_user,
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

            return TicketUserAssembler.to_dto(ticket_user)

    # --------------------------------
    # Queries
    # --------------------------------

    def get_all(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> list[TicketUserResponseDTO]:
        """
        Возвращает все пользовательские заявки клиента.

        Право:

            UserPermission.TICKET_VIEW_ALL

        Ограничение:

            actor_user должен принадлежать этому client.
        """
        with self._uow:
            client = self._get_client(ticket_user_dto.client_id)

            self._require_user_view_all_for_client(
                actor_user_id=ticket_user_dto.actor_user_id,
                client=client,
            )

            ticket_users = self._uow.user_tickets.get_all()

            return [
                TicketUserAssembler.to_dto(ticket_user)
                for ticket_user in ticket_users
                if ticket_user.client_id == ticket_user_dto.client_id
            ]

    def get_by_user(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> list[TicketUserResponseDTO]:
        """
        Возвращает пользовательские заявки конкретного user внутри client.

        Права:

            если actor_user_id == user_id:
                UserPermission.TICKET_VIEW

            если actor_user_id != user_id:
                UserPermission.TICKET_VIEW_ALL

        В обоих случаях actor_user должен принадлежать client.
        """
        target_user_id = self._required_positive_dto_attr(
            ticket_user_dto,
            "user_id",
        )

        with self._uow:
            client = self._get_client(ticket_user_dto.client_id)
            target_user = self._uow.users.get(target_user_id)

            TicketPolicy.ensure_user_enabled(target_user)
            TicketPolicy.ensure_user_belongs_to_client(
                user=target_user,
                client=client,
            )

            self._require_user_view_for_user(
                actor_user_id=ticket_user_dto.actor_user_id,
                target_user=target_user,
                client=client,
            )

            ticket_users = self._uow.user_tickets.get_all()

            return [
                TicketUserAssembler.to_dto(ticket_user)
                for ticket_user in ticket_users
                if (
                    ticket_user.client_id == ticket_user_dto.client_id
                    and ticket_user.user_id == target_user_id
                )
            ]

    def get_by_id(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
        """
        Возвращает пользовательскую заявку по ticket_user_id.

        Права:

            владелец заявки:
                UserPermission.TICKET_VIEW

            пользователь той же организации:
                UserPermission.TICKET_VIEW_ALL
        """
        with self._uow:
            ticket_user = self._uow.user_tickets.get(
                ticket_user_dto.ticket_user_id,
            )

            self._require_user_view_for_ticket_user(
                actor_user_id=ticket_user_dto.actor_user_id,
                ticket_user=ticket_user,
            )

            return TicketUserAssembler.to_dto(ticket_user)

    # --------------------------------
    # Permission helpers: operations
    # --------------------------------

    def _require_user_operation(
        self,
        *,
        actor_user_id: int,
    ) -> User:
        user = self.actor.require_actor_user(
            actor_user_id=actor_user_id,
            permission=UserPermission.TICKET_OPERATION,
        )

        TicketPolicy.ensure_user_enabled(user)

        return user

    def _require_user_operation_all(
        self,
        *,
        actor_user_id: int,
    ) -> User:
        user = self.actor.require_actor_user(
            actor_user_id=actor_user_id,
            permission=UserPermission.TICKET_OPERATION_ALL,
        )

        TicketPolicy.ensure_user_enabled(user)

        return user

    def _require_user_operation_for_ticket_user(
            self,
            *,
            actor_user_id: int,
            ticket_user: TicketUser,
    ) -> User:
        if actor_user_id == ticket_user.user_id:
            user = self._require_user_operation(
                actor_user_id=actor_user_id,
            )
        else:
            user = self._require_user_operation_all(
                actor_user_id=actor_user_id,
            )

        client = self._get_ticket_user_client(ticket_user)

        TicketPolicy.ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

        return user
    # --------------------------------
    # Permission helpers: views
    # --------------------------------

    def _require_user_view(
        self,
        *,
        actor_user_id: int,
    ) -> User:
        user = self.actor.require_actor_user(
            actor_user_id=actor_user_id,
            permission=UserPermission.TICKET_VIEW,
        )

        TicketPolicy.ensure_user_enabled(user)

        return user

    def _require_user_view_all(
        self,
        *,
        actor_user_id: int,
    ) -> User:
        user = self.actor.require_actor_user(
            actor_user_id=actor_user_id,
            permission=UserPermission.TICKET_VIEW_ALL,
        )

        TicketPolicy.ensure_user_enabled(user)

        return user

    def _require_user_view_all_for_client(
        self,
        *,
        actor_user_id: int,
        client: Client,
    ) -> User:
        user = self._require_user_view_all(
            actor_user_id=actor_user_id,
        )

        TicketPolicy.ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

        return user

    def _require_user_view_for_user(
        self,
        *,
        actor_user_id: int,
        target_user: User,
        client: Client,
    ) -> User:
        if actor_user_id == target_user.employee_id:
            user = self._require_user_view(
                actor_user_id=actor_user_id,
            )
        else:
            user = self._require_user_view_all(
                actor_user_id=actor_user_id,
            )

        TicketPolicy.ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

        return user

    def _require_user_view_for_ticket_user(
        self,
        *,
        actor_user_id: int,
        ticket_user: TicketUser,
    ) -> User:
        if actor_user_id == ticket_user.user_id:
            user = self._require_user_view(
                actor_user_id=actor_user_id,
            )
        else:
            user = self._require_user_view_all(
                actor_user_id=actor_user_id,
            )

        client = self._get_ticket_user_client(ticket_user)

        TicketPolicy.ensure_user_belongs_to_client(
            user=user,
            client=client,
        )

        return user

    # --------------------------------
    # Validation helpers
    # --------------------------------

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

    def _get_client(
        self,
        client_id: int,
    ) -> Client:
        client = self._uow.clients.get(client_id)

        TicketPolicy.ensure_client_enabled(client)

        return client

    def _get_ticket_user_client(
        self,
        ticket_user: TicketUser,
    ) -> Client:
        return self._get_client(ticket_user.client_id)

    @staticmethod
    def _required_positive_dto_attr(
        ticket_user_dto: TicketUserDTO,
        name: str,
    ) -> int:
        value = getattr(
            ticket_user_dto,
            name,
            None,
        )

        if not isinstance(value, int) or value <= 0:
            raise DomainOperationError(
                f"TicketUserDTO.{name} must be positive integer",
            )

        return value