# src/domain/services/ticket_user_service.py

from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_sync_service import TicketSyncService
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment
from src.domain.ticket_user import TicketUser
from src.domain.value_objects import CommonComment


class TicketUserService:
    """
    Domain facade for TicketUser operations.

    Responsibilities:
    - provides a single domain entry point for User-side TicketUser use cases;
    - invokes TicketUser aggregate commands;
    - validates linked Ticket / TicketUser pair before shared operations;
    - synchronizes User-originated TicketUser workflow changes to Ticket;
    - coordinates shared contact_user_id.

    Does not handle:
    - repositories;
    - UnitOfWork;
    - persistence;
    - transactions;
    - RBAC;
    - permissions;
    - loading aggregates;
    - actor role checks.

    Application layer decides whether an actor is allowed to invoke
    a particular operation.

    TicketUser remains responsible for:
    - its workflow;
    - transition validity;
    - aggregate invariants;
    - status-record payload.

    TicketSyncService remains responsible for:
    - Ticket / TicketUser structural consistency;
    - TicketUser -> Ticket workflow synchronization;
    - shared contact_user_id.

    Admin-originated TicketUser workflow changes are intentionally not
    exposed here.

    They originate from Ticket and are synchronized through TicketService:

        Ticket -> TicketUser

    User-originated terminal actions originate here:

        TicketUser -> Ticket
    """

    def __init__(
        self,
        ticket_sync_service: TicketSyncService,
    ) -> None:
        self._ticket_sync_service = ticket_sync_service

    # ==================================================================
    # Creation
    # ==================================================================

    @staticmethod
    def create(
        *,
        client_id: int,
        user_id: int,
        text_of_ticket: str,
        contact_user_id: int = 0,
        description: str = "",
        comment: str = "",
    ) -> TicketUser:
        """
        Create a new TicketUser initiated by User.

        Initial workflow:

            CREATED

        The internal Ticket is not created here because its
        user_ticket_id can be assigned only after TicketUser persistence
        has generated ticket_user_id.

        Application layer therefore coordinates:

            TicketUserService.create(...)
            repository.save(ticket_user)
            TicketService.create_from_ticket_user(...)
        """

        return TicketUser.create(
            client_id=client_id,
            user_id=user_id,
            text_of_ticket=text_of_ticket,
            contact_user_id=contact_user_id,
            description=description,
            comment=comment,
        )

    # ==================================================================
    # TicketUser data
    # ==================================================================

    @staticmethod
    def add_comment(
        *,
        ticket_user: TicketUser,
        employee_id: int,
        comment: str,
    ) -> None:
        """
        Add ordinary TicketUser comment.

        employee_id is the real User/Admin employee id.

        No synchronization with internal Ticket is performed because
        ordinary comments of Ticket and TicketUser are independent.
        """

        ticket_user.add_comment(
            Comment(
                employee_id=employee_id,
                comment=CommonComment(comment),
            )
        )

    @staticmethod
    def update_description(
        *,
        ticket_user: TicketUser,
        actor_employee_id: int,
        description: str,
    ) -> None:
        """
        Change TicketUser description.

        Ticket.description and TicketUser.description are independent,
        therefore internal Ticket is not changed.
        """

        ticket_user.update_details(
            actor_employee_id=actor_employee_id,
            description=description,

            # Preserve current contact User.
            contact_user_id=ticket_user.contact_user_id,
        )

    # ==================================================================
    # Shared Ticket / TicketUser data
    # ==================================================================

    def change_contact_user(
        self,
        *,
        ticket_user: TicketUser,
        ticket: Ticket,
        actor_employee_id: int,
        contact_user_id: int,
    ) -> Ticket:
        """
        Change shared contact_user_id.

        contact_user_id is a permanent cross-aggregate invariant:

            Ticket.contact_user_id
                ==
            TicketUser.contact_user_id

        Therefore the change is delegated to TicketSyncService.

        Returns modified Ticket so application layer knows that both
        aggregates must be persisted.
        """

        self._require_linked_ticket(
            ticket_user=ticket_user,
            ticket=ticket,
        )

        self._ticket_sync_service.change_contact_user(
            ticket,
            ticket_user,
            actor_employee_id=actor_employee_id,
            contact_user_id=contact_user_id,
        )

        return ticket

    # ==================================================================
    # User workflow
    # ==================================================================

    def confirm_by_user(
        self,
        *,
        ticket_user: TicketUser,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> Ticket:
        """
        User confirms completed work.

        TicketUser:

            WAITING_FOR_CONFIRMATION
                -> CONFIRMED_BY_USER

        Internal Ticket is then synchronized:

            READY_FOR_REVIEW
                -> CONFIRMED_BY_USER

        TicketUser stores the real User actor id.

        Internal Ticket uses its own User-action actor convention,
        which is handled by TicketSyncService / Ticket.
        """

        self._require_linked_ticket(
            ticket_user=ticket_user,
            ticket=ticket,
        )

        ticket_user.confirm_by_user(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        self._ticket_sync_service.sync_from_ticket_user(
            ticket,
            ticket_user,
            comment=comment,
        )

        return ticket

    def cancel_by_user(
        self,
        *,
        ticket_user: TicketUser,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> Ticket:
        """
        User cancels the request.

        TicketUser:

            allowed non-terminal state
                -> CANCELLED_BY_USER

        Internal Ticket is synchronized:

            -> CANCELLED_BY_USER
        """

        self._require_linked_ticket(
            ticket_user=ticket_user,
            ticket=ticket,
        )

        ticket_user.cancel_by_user(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        self._ticket_sync_service.sync_from_ticket_user(
            ticket,
            ticket_user,
            comment=comment,
        )

        return ticket

    # ==================================================================
    # Internal helpers
    # ==================================================================

    def _require_linked_ticket(
        self,
        *,
        ticket_user: TicketUser,
        ticket: Ticket,
    ) -> Ticket:
        """
        Validate Ticket / TicketUser structural consistency before
        TicketUser is mutated.

        Existing TicketUser is expected to have a corresponding
        internal Ticket.
        """

        if ticket_user.ticket_user_id <= 0:
            raise DomainOperationError(
                "Existing linked TicketUser must have "
                "positive ticket_user_id"
            )

        if ticket.user_ticket_id <= 0:
            raise DomainOperationError(
                f"TicketUser {ticket_user.ticket_user_id} "
                "does not have linked internal Ticket"
            )

        self._ticket_sync_service.ensure_consistent(
            ticket,
            ticket_user,
        )

        return ticket