
# src/domain/services/ticket_user_service.py

"""Domain facade for user-facing TicketUser operations.

The application layer handles loading, authorization, locking, persistence,
transactions and the creation of the linked internal Ticket.

Commands mutate the supplied aggregates in place and return None. The create
factory returns the newly constructed TicketUser.

Before a User-side workflow operation, the linked Ticket/TicketUser pair must
be structurally and workflow-consistent. TicketSyncService performs the
cross-aggregate synchronization after the TicketUser command.

If an operation fails after mutating an aggregate, the application layer must
roll back the transaction and discard or restore the in-memory aggregates.
"""

from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_sync_service import TicketSyncService
from src.domain.ticket import Ticket
from src.domain.ticket_components import Comment
from src.domain.ticket_user import TicketUser
from src.domain.value_objects import CommonComment


class TicketUserService:
    """Provide a domain entry point for user-facing TicketUser operations."""

    def __init__(self, ticket_sync_service: TicketSyncService) -> None:
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
        """Create a User-initiated TicketUser with initial status CREATED.

        The application layer coordinates creation and persistence of the
        related internal Ticket after TicketUser receives its identifier.
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
    # TicketUser-local data
    # ==================================================================

    @staticmethod
    def add_comment(
        *,
        ticket_user: TicketUser,
        employee_id: int,
        comment: str,
    ) -> None:
        """Add an ordinary TicketUser comment; do not synchronize it."""
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
        """Update description without changing the current contact User.

        TicketUser.update_details() replaces both fields, so pass the
        existing contact_user_id explicitly.
        """
        ticket_user.update_details(
            actor_employee_id=actor_employee_id,
            description=description,
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
    ) -> None:
        """Change the shared contact in both linked aggregates in place.

        Structural consistency is required before modification. Editing
        contact data does not itself require a workflow transition.
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
    ) -> None:
        """Synchronize User confirmation to the internal Ticket.

        TicketUser: WAITING_FOR_CONFIRMATION -> CONFIRMED_BY_USER.
        Ticket: READY_FOR_REVIEW -> CONFIRMED_BY_USER.
        """
        self._require_linked_ticket(
            ticket_user=ticket_user,
            ticket=ticket,
        )

        self._ticket_sync_service.ensure_workflow_consistent(
            ticket,
            ticket_user,
        )

        ticket_user.confirm_by_user(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        # Preserve the existing comment-handling contract for now.
        self._ticket_sync_service.sync_from_ticket_user(
            ticket,
            ticket_user,
            comment=comment,
        )

    def cancel_by_user(
        self,
        *,
        ticket_user: TicketUser,
        ticket: Ticket,
        actor_employee_id: int,
        comment: str = "",
    ) -> None:
        """Synchronize cancellation of a newly created User request.

        TicketUser: CREATED -> CANCELLED_BY_USER only.
        Ticket: CREATED_FROM_REQUEST_USER or CREATED_FROM_TICKET_USER
                -> CANCELLED_BY_USER, subject to Ticket's own rules.
        """
        self._require_linked_ticket(
            ticket_user=ticket_user,
            ticket=ticket,
        )

        self._ticket_sync_service.ensure_workflow_consistent(
            ticket,
            ticket_user,
        )

        ticket_user.cancel_by_user(
            actor_employee_id=actor_employee_id,
            comment=comment,
        )

        # Preserve the existing comment-handling contract for now.
        self._ticket_sync_service.sync_from_ticket_user(
            ticket,
            ticket_user,
            comment=comment,
        )

    # ==================================================================
    # Internal helpers
    # ==================================================================

    def _require_linked_ticket(
        self,
        *,
        ticket_user: TicketUser,
        ticket: Ticket,
    ) -> None:
        """Validate the structural relationship before shared operations."""

        if ticket_user.ticket_user_id <= 0:
            raise DomainOperationError(
                "Existing linked TicketUser must have positive ticket_user_id"
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
