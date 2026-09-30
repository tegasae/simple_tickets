# src/application/services/ticket_user_application_service.py

from __future__ import annotations

from src.application.assemblers.assembler import TicketUserAssembler
from src.application.dto.ticket_dto import (
    TicketUserDTO,
    TicketUserResponseDTO,
)
from src.application.helper.actor_helper import EmployeeActorHelper

from src.domain.employee import User
from src.domain.exceptions import DomainOperationError
from src.domain.rbac.permissions import UserPermission
from src.domain.services.ticket_service import TicketService
from src.domain.services.ticket_sync_service import TicketSyncService
from src.domain.services.ticket_user_service import TicketUserService
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from src.domain.uow.unit_of_work import UnitOfWork


class TicketUserApplicationService:
    """
    Application service for User-side TicketUser use cases.

    Responsibilities:
    - RBAC;
    - UnitOfWork / transaction;
    - aggregate loading;
    - access scope: own Ticket vs organization Tickets;
    - validation of external references;
    - optimistic concurrency guards;
    - calling TicketUserService / TicketService;
    - persistence;
    - DTO assembly.

    Does not contain:
    - Ticket workflow rules;
    - TicketUser workflow rules;
    - status-record construction;
    - Ticket / TicketUser synchronization rules;
    - SQL;
    - repository business logic.

    User-originated workflow:

        TicketUserApplicationService
            -> TicketUserService
            -> TicketUser
            -> TicketSyncService
            -> Ticket

    Admin-originated workflow remains in TicketApplicationService.
    """

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

        self.actor = EmployeeActorHelper(
            self.uow
        )

        self.ticket_sync_service = TicketSyncService()

        self.ticket_user_service = TicketUserService(
            ticket_sync_service=self.ticket_sync_service,
        )

        self.ticket_service = TicketService(
            ticket_sync_service=self.ticket_sync_service,
        )

    # ==================================================================
    # Creation
    # ==================================================================

    def create_from_user(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
        """
        User creates a new TicketUser.

        Required permission:

            TICKET_OPERATION

        In the same transaction:

            TicketUser.CREATED

        is created first and persisted to obtain ticket_user_id.

        Then linked internal Ticket is created:

            Ticket.CREATED_FROM_TICKET_USER

        TicketUser stores real User actor id.

        Internal Ticket represents User-originated workflow actor as 0.
        """

        with self.uow:
            actor = self.actor.require_actor_user(
                actor_user_id=ticket_user_dto.actor_user_id,
                permission=UserPermission.TICKET_OPERATION,
            )

            if ticket_user_dto.ticket_user_id != 0:
                raise DomainOperationError(
                    "create_from_user requires ticket_user_id = 0"
                )

            if (
                ticket_user_dto.user_id != 0
                and ticket_user_dto.user_id != actor.employee_id
            ):
                raise DomainOperationError(
                    "User cannot create TicketUser "
                    "for another User"
                )

            self._validate_create_references(
                actor=actor,
                ticket_user_dto=ticket_user_dto,
            )

            # ----------------------------------------------------------
            # Create TicketUser first.
            # ----------------------------------------------------------

            ticket_user = self.ticket_user_service.create(
                client_id=ticket_user_dto.client_id,
                user_id=actor.employee_id,
                text_of_ticket=ticket_user_dto.text_of_ticket,
                contact_user_id=ticket_user_dto.contact_user_id,
                description=ticket_user_dto.description,
                comment=ticket_user_dto.comment,
            )

            saved_ticket_user = self.uow.user_tickets.save(
                ticket_user
            )

            if saved_ticket_user is None:
                saved_ticket_user = ticket_user

            if saved_ticket_user.ticket_user_id <= 0:
                raise DomainOperationError(
                    "TicketUser repository must assign "
                    "ticket_user_id before creating linked Ticket"
                )

            # ----------------------------------------------------------
            # Create linked internal Ticket.
            #
            # Use normalized values from TicketUser, especially
            # contact_user_id: TicketUser.create() may replace 0
            # with user_id.
            # ----------------------------------------------------------

            ticket = self.ticket_service.create_from_ticket_user(
                client_id=saved_ticket_user.client_id,
                user_id=saved_ticket_user.user_id,
                user_ticket_id=saved_ticket_user.ticket_user_id,
                text_of_ticket=saved_ticket_user.text_of_ticket,
                contact_user_id=(
                    saved_ticket_user.contact_user_id
                ),
                description=ticket_user_dto.description,
                department_id=ticket_user_dto.department_id,
                remote_work_recommended=(
                    ticket_user_dto.remote_work_recommended
                ),
                urgency=ticket_user_dto.urgency,
            )

            self.ticket_sync_service.ensure_consistent(
                ticket,
                saved_ticket_user,
            )

            self.uow.tickets.save(
                ticket
            )

            self.uow.commit()

            return TicketUserAssembler.to_dto(
                saved_ticket_user
            )

    # ==================================================================
    # TicketUser data
    # ==================================================================

    def add_comment(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
        with self.uow:
            ticket_user = self._get_ticket_user(
                ticket_user_dto.ticket_user_id,
            )

            actor = self._require_operation_access(
                actor_user_id=ticket_user_dto.actor_user_id,
                ticket_user=ticket_user,
            )

            self.ticket_user_service.add_comment(
                ticket_user=ticket_user,
                employee_id=actor.employee_id,
                comment=ticket_user_dto.comment,
            )

            return self._save_ticket_user(
                ticket_user=ticket_user,
            )

    def update_description(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
        """
        TicketUser.description is independent from Ticket.description.
        """

        with self.uow:
            ticket_user = self._get_ticket_user(
                ticket_user_dto.ticket_user_id,
            )

            actor = self._require_operation_access(
                actor_user_id=ticket_user_dto.actor_user_id,
                ticket_user=ticket_user,
            )

            self.ticket_user_service.update_description(
                ticket_user=ticket_user,
                actor_employee_id=actor.employee_id,
                description=ticket_user_dto.description,
            )

            return self._save_ticket_user(
                ticket_user=ticket_user,
            )

    def change_contact_user(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
        """
        Change shared contact_user_id in both aggregates.

        Ticket.contact_user_id
            ==
        TicketUser.contact_user_id
        """

        with self.uow:
            ticket_user = self._get_ticket_user(
                ticket_user_dto.ticket_user_id,
            )

            actor = self._require_operation_access(
                actor_user_id=ticket_user_dto.actor_user_id,
                ticket_user=ticket_user,
            )

            self._validate_contact_user(
                contact_user_id=ticket_user_dto.contact_user_id,
                client_id=ticket_user.client_id,
                main_user_id=ticket_user.user_id,
            )

            ticket = self._get_linked_ticket(
                ticket_user=ticket_user,
            )

            self.ticket_user_service.change_contact_user(
                ticket_user=ticket_user,
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                contact_user_id=ticket_user_dto.contact_user_id,
            )

            return self._save_pair(
                ticket_user=ticket_user,
                ticket=ticket,
            )

    # ==================================================================
    # User workflow
    # ==================================================================

    def confirm_by_user(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
        """
        User confirms completed work.

        Required permission:

            owner:
                TICKET_OPERATION
                OR TICKET_OPERATION_ALL

            another User in the same Client:
                TICKET_OPERATION_ALL

        TicketUser:

            WAITING_FOR_CONFIRMATION
                -> CONFIRMED_BY_USER

        Ticket:

            READY_FOR_REVIEW
                -> CONFIRMED_BY_USER
        """

        with self.uow:
            ticket_user = self._get_ticket_user(
                ticket_user_dto.ticket_user_id,
            )

            actor = self._require_operation_access(
                actor_user_id=ticket_user_dto.actor_user_id,
                ticket_user=ticket_user,
            )

            ticket = self._get_linked_ticket(
                ticket_user=ticket_user,
            )

            self.ticket_user_service.confirm_by_user(
                ticket_user=ticket_user,
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_user_dto.comment,
            )

            return self._save_pair(
                ticket_user=ticket_user,
                ticket=ticket,
            )

    def cancel_by_user(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
        """
        User cancels TicketUser.

        Required permission:

            owner:
                TICKET_OPERATION
                OR TICKET_OPERATION_ALL

            another User in the same Client:
                TICKET_OPERATION_ALL

        TicketUser:

            -> CANCELLED_BY_USER

        Linked Ticket:

            -> CANCELLED_BY_USER

        Exact workflow validity is checked by aggregates.
        """

        with self.uow:
            ticket_user = self._get_ticket_user(
                ticket_user_dto.ticket_user_id,
            )

            actor = self._require_operation_access(
                actor_user_id=ticket_user_dto.actor_user_id,
                ticket_user=ticket_user,
            )

            ticket = self._get_linked_ticket(
                ticket_user=ticket_user,
            )

            self.ticket_user_service.cancel_by_user(
                ticket_user=ticket_user,
                ticket=ticket,
                actor_employee_id=actor.employee_id,
                comment=ticket_user_dto.comment,
            )

            return self._save_pair(
                ticket_user=ticket_user,
                ticket=ticket,
            )

    # ==================================================================
    # Queries
    # ==================================================================

    def get_by_id(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> TicketUserResponseDTO:
        with self.uow:
            ticket_user = self._get_ticket_user(
                ticket_user_dto.ticket_user_id,
            )

            self._require_view_access(
                actor_user_id=ticket_user_dto.actor_user_id,
                ticket_user=ticket_user,
            )

            return TicketUserAssembler.to_dto(
                ticket_user
            )

    def get_by_user_id(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> list[TicketUserResponseDTO]:
        """
        Return TicketUser records belonging to target User.

        Own records require:

            TICKET_VIEW
                OR
            TICKET_VIEW_ALL

        Another User's records require:

            TICKET_VIEW_ALL

        Actor and target User must belong to the same Client.
        """

        with self.uow:
            if ticket_user_dto.user_id <= 0:
                raise DomainOperationError(
                    "get_by_user_id requires user_id > 0"
                )

            target_user = self.uow.users.get(
                ticket_user_dto.user_id,
            )

            if (
                ticket_user_dto.actor_user_id
                == target_user.employee_id
            ):
                actor = self.actor.require_actor_user_any(
                    actor_user_id=ticket_user_dto.actor_user_id,
                    permissions=(
                        UserPermission.TICKET_VIEW,
                        UserPermission.TICKET_VIEW_ALL,
                    ),
                )
            else:
                actor = self.actor.require_actor_user(
                    actor_user_id=ticket_user_dto.actor_user_id,
                    permission=UserPermission.TICKET_VIEW_ALL,
                )

            self._ensure_same_client(
                actor=actor,
                client_id=target_user.client_id,
            )

            ticket_users = self.uow.user_tickets.get_all()

            return self._to_dto_list(
                [
                    ticket_user
                    for ticket_user in ticket_users
                    if (
                        ticket_user.client_id
                        == target_user.client_id
                        and ticket_user.user_id
                        == target_user.employee_id
                    )
                ]
            )

    def get_all(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> list[TicketUserResponseDTO]:
        """
        Return all TicketUser records for actor's Client.

        Requires:

            TICKET_VIEW_ALL
        """

        with self.uow:
            actor = self.actor.require_actor_user(
                actor_user_id=ticket_user_dto.actor_user_id,
                permission=UserPermission.TICKET_VIEW_ALL,
            )

            if (
                ticket_user_dto.client_id > 0
                and ticket_user_dto.client_id != actor.client_id
            ):
                raise DomainOperationError(
                    "User cannot view TicketUser records "
                    "of another Client"
                )

            ticket_users = self.uow.user_tickets.get_all()

            return self._to_dto_list(
                [
                    ticket_user
                    for ticket_user in ticket_users
                    if ticket_user.client_id == actor.client_id
                ]
            )

    def get_open(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> list[TicketUserResponseDTO]:
        """
        Return open TicketUser records visible to actor.

        TICKET_VIEW_ALL:
            all open TicketUser records of actor's Client.

        TICKET_VIEW:
            actor's own open TicketUser records.
        """

        with self.uow:
            actor = self.actor.require_actor_user_any(
                actor_user_id=ticket_user_dto.actor_user_id,
                permissions=(
                    UserPermission.TICKET_VIEW,
                    UserPermission.TICKET_VIEW_ALL,
                ),
            )

            view_all = self.actor.has_user_permission(
                actor_user_id=actor.employee_id,
                permission=UserPermission.TICKET_VIEW_ALL,
            )

            ticket_users = self.uow.user_tickets.get_all()

            if view_all:
                ticket_users = [
                    ticket_user
                    for ticket_user in ticket_users
                    if (
                        ticket_user.client_id == actor.client_id
                        and not ticket_user.is_closed
                    )
                ]
            else:
                ticket_users = [
                    ticket_user
                    for ticket_user in ticket_users
                    if (
                        ticket_user.client_id == actor.client_id
                        and ticket_user.user_id == actor.employee_id
                        and not ticket_user.is_closed
                    )
                ]

            return self._to_dto_list(
                ticket_users
            )

    def get_closed(
        self,
        *,
        ticket_user_dto: TicketUserDTO,
    ) -> list[TicketUserResponseDTO]:
        """
        Return closed TicketUser records visible to actor.

        TICKET_VIEW_ALL:
            all closed TicketUser records of actor's Client.

        TICKET_VIEW:
            actor's own closed TicketUser records.
        """

        with self.uow:
            actor = self.actor.require_actor_user_any(
                actor_user_id=ticket_user_dto.actor_user_id,
                permissions=(
                    UserPermission.TICKET_VIEW,
                    UserPermission.TICKET_VIEW_ALL,
                ),
            )

            view_all = self.actor.has_user_permission(
                actor_user_id=actor.employee_id,
                permission=UserPermission.TICKET_VIEW_ALL,
            )

            ticket_users = self.uow.user_tickets.get_all()

            if view_all:
                ticket_users = [
                    ticket_user
                    for ticket_user in ticket_users
                    if (
                        ticket_user.client_id == actor.client_id
                        and ticket_user.is_closed
                    )
                ]
            else:
                ticket_users = [
                    ticket_user
                    for ticket_user in ticket_users
                    if (
                        ticket_user.client_id == actor.client_id
                        and ticket_user.user_id == actor.employee_id
                        and ticket_user.is_closed
                    )
                ]

            return self._to_dto_list(
                ticket_users
            )

    # ==================================================================
    # Access scope
    # ==================================================================

    def _require_operation_access(
        self,
        *,
        actor_user_id: int,
        ticket_user: TicketUser,
    ) -> User:
        """
        Owner:
            TICKET_OPERATION OR TICKET_OPERATION_ALL

        Another User:
            TICKET_OPERATION_ALL

        In both cases actor must belong to TicketUser Client.

        Actual permission checking and actor caching are delegated
        to EmployeeActorHelper.
        """

        if actor_user_id == ticket_user.user_id:
            actor = self.actor.require_actor_user_any(
                actor_user_id=actor_user_id,
                permissions=(
                    UserPermission.TICKET_OPERATION,
                    UserPermission.TICKET_OPERATION_ALL,
                ),
            )
        else:
            actor = self.actor.require_actor_user(
                actor_user_id=actor_user_id,
                permission=UserPermission.TICKET_OPERATION_ALL,
            )

        self._ensure_same_client(
            actor=actor,
            client_id=ticket_user.client_id,
        )

        return actor

    def _require_view_access(
        self,
        *,
        actor_user_id: int,
        ticket_user: TicketUser,
    ) -> User:
        """
        Owner:
            TICKET_VIEW OR TICKET_VIEW_ALL

        Another User:
            TICKET_VIEW_ALL

        Actor must belong to TicketUser Client.
        """

        if actor_user_id == ticket_user.user_id:
            actor = self.actor.require_actor_user_any(
                actor_user_id=actor_user_id,
                permissions=(
                    UserPermission.TICKET_VIEW,
                    UserPermission.TICKET_VIEW_ALL,
                ),
            )
        else:
            actor = self.actor.require_actor_user(
                actor_user_id=actor_user_id,
                permission=UserPermission.TICKET_VIEW_ALL,
            )

        self._ensure_same_client(
            actor=actor,
            client_id=ticket_user.client_id,
        )

        return actor

    # ==================================================================
    # External reference validation
    # ==================================================================

    def _validate_create_references(
        self,
        *,
        actor: User,
        ticket_user_dto: TicketUserDTO,
    ) -> None:
        if ticket_user_dto.client_id <= 0:
            raise DomainOperationError(
                "client_id must be positive"
            )

        client = self.uow.clients.get(
            ticket_user_dto.client_id,
        )

        if not client.enabled:
            raise DomainOperationError(
                "Cannot create TicketUser for disabled Client"
            )

        self._ensure_same_client(
            actor=actor,
            client_id=client.client_id,
        )

        self._validate_contact_user(
            contact_user_id=ticket_user_dto.contact_user_id,
            client_id=client.client_id,
            main_user_id=actor.employee_id,
        )

        department = None

        if ticket_user_dto.department_id < 0:
            raise DomainOperationError(
                "department_id cannot be negative"
            )

        if ticket_user_dto.department_id > 0:
            department = self.uow.departments.get(
                ticket_user_dto.department_id,
            )

            department.ensure_enabled()

        # --------------------------------------------------------------
        # Optimistic concurrency guards
        # --------------------------------------------------------------

        self.uow.clients.touch(
            client
        )

        if department is not None:
            self.uow.departments.touch(
                department
            )

    def _validate_contact_user(
        self,
        *,
        contact_user_id: int,
        client_id: int,
        main_user_id: int,
    ) -> None:
        """
        contact_user_id == 0 means main User.

        A separate contact User must:
        - exist;
        - be enabled;
        - belong to the same Client.
        """

        if contact_user_id < 0:
            raise DomainOperationError(
                "contact_user_id cannot be negative"
            )

        if (
            contact_user_id == 0
            or contact_user_id == main_user_id
        ):
            return

        contact_user = self.uow.users.get(
            contact_user_id,
        )

        contact_user.can_do_operation()

        if contact_user.client_id != client_id:
            raise DomainOperationError(
                "Contact User does not belong "
                "to TicketUser Client"
            )

        self.uow.users.touch(
            contact_user
        )

    @staticmethod
    def _ensure_same_client(
        *,
        actor: User,
        client_id: int,
    ) -> None:
        if actor.client_id != client_id:
            raise DomainOperationError(
                "User does not belong to TicketUser Client"
            )

    # ==================================================================
    # Loading
    # ==================================================================

    def _get_ticket_user(
        self,
        ticket_user_id: int,
    ) -> TicketUser:
        if ticket_user_id <= 0:
            raise DomainOperationError(
                "ticket_user_id must be positive"
            )

        return self.uow.user_tickets.get(
            ticket_user_id
        )

    def _get_linked_ticket(
        self,
        *,
        ticket_user: TicketUser,
    ) -> Ticket:
        if ticket_user.ticket_user_id <= 0:
            raise DomainOperationError(
                "Linked TicketUser must have "
                "positive ticket_user_id"
            )

        return self.uow.tickets.get_by_user_ticket_id(
            ticket_user.ticket_user_id
        )

    # ==================================================================
    # Persistence
    # ==================================================================

    def _save_ticket_user(
        self,
        *,
        ticket_user: TicketUser,
    ) -> TicketUserResponseDTO:
        saved_ticket_user = self.uow.user_tickets.save(
            ticket_user
        )

        self.uow.commit()

        if saved_ticket_user is None:
            saved_ticket_user = ticket_user

        return TicketUserAssembler.to_dto(
            saved_ticket_user
        )

    def _save_pair(
        self,
        *,
        ticket_user: TicketUser,
        ticket: Ticket,
    ) -> TicketUserResponseDTO:
        saved_ticket_user = self.uow.user_tickets.save(
            ticket_user
        )

        self.uow.tickets.save(
            ticket
        )

        self.uow.commit()

        if saved_ticket_user is None:
            saved_ticket_user = ticket_user

        return TicketUserAssembler.to_dto(
            saved_ticket_user
        )

    @staticmethod
    def _to_dto_list(
        ticket_users: list[TicketUser],
    ) -> list[TicketUserResponseDTO]:
        return [
            TicketUserAssembler.to_dto(ticket_user)
            for ticket_user in ticket_users
        ]