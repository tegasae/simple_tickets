"""Synchronize workflow and shared data of a linked Ticket / TicketUser pair.

Ticket and TicketUser are independent domain aggregates. This service works
only with an existing linked pair; their creation, authorization, persistence,
and transactional coordination belong to the application layer.

A linked pair must satisfy:

    ticket.user_ticket_id == ticket_user.ticket_user_id
    ticket.client_id == ticket_user.client_id
    ticket.user_id == ticket_user.user_id
    ticket.contact_user_id == ticket_user.contact_user_id

The internal Ticket must originate from a user request
(CREATED_FROM_REQUEST_USER or CREATED_FROM_TICKET_USER). A standalone,
Admin-initiated Ticket (CREATED) has no user-facing workflow.

Synchronization is based on current states, not on replaying full histories.
The application layer must synchronize every change of the *mapped* user
state, rather than waiting until several distinct user-visible states have
been skipped. Transitions that map to the same TicketUser status do not
create duplicate history records.

Comments attached to corresponding status changes are independent; this
service never copies a comment from one aggregate to the other. In
particular, synchronization to CANCELLED_BY_ADMIN requires a valid separate
TicketUser-facing comment.

A completed operation must be persisted for both aggregates in one database
transaction. On failure, the application layer must discard or restore the
mutated in-memory aggregates as appropriate; database rollback alone does
not restore Python objects.
"""

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.mapping_statuses import TICKET_TO_TICKET_USER_STATUS
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_user_status import TicketUserStatus
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser


class TicketSyncService:
    """Coordinate state correspondence for an existing linked pair.

    Ticket -> TicketUser handles internal (Admin-side) workflow changes.
    TicketUser -> Ticket handles user confirmations and user cancellations.
    No generic reverse mapping is possible: several Ticket states map to one
    TicketUser state.

    Shared contact changes are performed on both aggregates. This service
    contains no repositories, transactions, RBAC or cross-aggregate lookups.
    """

    # ==================================================================
    # Pair consistency
    # ==================================================================

    @staticmethod
    def ensure_consistent(
        ticket: Ticket,
        ticket_user: TicketUser,
    ) -> None:
        """Validate permanent structural invariants of the linked pair.

        Workflow states are deliberately not compared here: one aggregate
        may temporarily be ahead of the other during synchronization.
        """
        if ticket.user_ticket_id <= 0:
            raise DomainOperationError(
                "Ticket is not linked to TicketUser"
            )

        if ticket_user.ticket_user_id <= 0:
            raise DomainOperationError(
                "Linked TicketUser must have positive ticket_user_id"
            )

        if ticket.user_ticket_id != ticket_user.ticket_user_id:
            raise DomainOperationError(
                "Ticket user_ticket_id does not match "
                "TicketUser ticket_user_id"
            )

        if ticket.client_id != ticket_user.client_id:
            raise DomainOperationError(
                "Ticket and TicketUser have different client_id"
            )

        if ticket.user_id != ticket_user.user_id:
            raise DomainOperationError(
                "Ticket and TicketUser have different user_id"
            )

        if ticket.contact_user_id != ticket_user.contact_user_id:
            raise DomainOperationError(
                "Ticket and TicketUser have different contact_user_id"
            )

        if ticket.statuses[0].status not in {
            TicketStatus.CREATED_FROM_REQUEST_USER,
            TicketStatus.CREATED_FROM_TICKET_USER,
        }:
            raise DomainOperationError(
                "Ticket origin does not support TicketUser synchronization"
            )

    # ==================================================================
    # Ticket -> TicketUser
    # ==================================================================

    def sync_from_ticket(
        self,
        ticket: Ticket,
        ticket_user: TicketUser,
        *,
        comment: str = "",
    ) -> None:
        """Project an internal workflow change onto TicketUser.

        If the projected status already matches, do not add a new record.
        User-originated confirmations/cancellations must be synchronized
        in the opposite direction.

        `comment` is a new TicketUser status comment. It is required when
        the target is CANCELLED_BY_ADMIN (e.g. Ticket REJECTED or CANCELLED).
        It is not copied automatically from the internal Ticket.
        """
        self.ensure_consistent(ticket, ticket_user)

        ticket_record = ticket.current_status_record()
        target_status = self._ticket_user_status_for(ticket)
        current_status = ticket_user.current_status()

        if current_status == target_status:
            return

        if target_status == TicketUserStatus.CREATED:
            raise DomainOperationError(
                "Cannot synchronize TicketUser back to CREATED"
            )

        if target_status in {
            TicketUserStatus.CONFIRMED_BY_USER,
            TicketUserStatus.CANCELLED_BY_USER,
        }:
            raise DomainOperationError(
                "User-originated Ticket state must be synchronized "
                "from TicketUser"
            )

        actor_employee_id = ticket_record.actor_employee_id

        if target_status == TicketUserStatus.IN_WORK:
            ticket_user.mark_in_work(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        elif target_status == TicketUserStatus.WAITING_FOR_CONFIRMATION:
            ticket_user.mark_waiting_for_confirmation(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        elif target_status == TicketUserStatus.SUSPENDED:
            ticket_user.suspend(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        elif target_status == TicketUserStatus.CONFIRMED_BY_ADMIN:
            ticket_user.confirm_by_admin(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        elif target_status == TicketUserStatus.CANCELLED_BY_ADMIN:
            ticket_user.cancel_by_admin(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )
        else:
            raise DomainOperationError(
                "Unsupported Ticket -> TicketUser synchronization: "
                f"{ticket_record.status.value} -> {target_status.value}"
            )

        self._ensure_workflow_consistent(ticket, ticket_user)

    # ==================================================================
    # TicketUser -> Ticket
    # ==================================================================

    def sync_from_ticket_user(
        self,
        ticket: Ticket,
        ticket_user: TicketUser,
        *,
        comment: str = "",
    ) -> None:
        """Apply an unambiguous user-originated workflow action to Ticket.

        CONFIRMED_BY_USER maps to READY_FOR_REVIEW -> CONFIRMED_BY_USER.
        CANCELLED_BY_USER originates from TicketUser.CREATED and maps to
        either CREATED_FROM_REQUEST_USER -> CANCELLED_BY_USER or
        CREATED_FROM_TICKET_USER -> CANCELLED_BY_USER.

        `comment` is a new internal Ticket status comment, not an automatic
        copy of the TicketUser status comment.
        """
        self.ensure_consistent(ticket, ticket_user)

        ticket_user_status = ticket_user.current_status()
        expected_ticket_user_status = self._ticket_user_status_for(ticket)

        if ticket_user_status == expected_ticket_user_status:
            return

        if ticket_user_status == TicketUserStatus.CONFIRMED_BY_USER:
            ticket.confirm_by_user(comment=comment)
        elif ticket_user_status == TicketUserStatus.CANCELLED_BY_USER:
            ticket.cancel_by_user(comment=comment)
        else:
            raise DomainOperationError(
                "TicketUser status cannot be synchronized to Ticket: "
                f"{ticket_user_status.value}"
            )

        self._ensure_workflow_consistent(ticket, ticket_user)

    # ==================================================================
    # Shared contact User
    # ==================================================================

    def change_contact_user(
        self,
        ticket: Ticket,
        ticket_user: TicketUser,
        *,
        actor_employee_id: int,
        contact_user_id: int,
    ) -> None:
        """Change contact User in both aggregates.

        contact_user_id > 0 sets the given contact; 0 resets it to the
        request owner's user_id. Both changes require a nonterminal
        TicketUser and a Ticket state that allows editing data.

        Precheck the known validation conditions before changing either
        aggregate. The application layer remains responsible for transactional
        persistence of the pair and disposing of state after a failure.
        """
        self.ensure_consistent(ticket, ticket_user)

        if type(actor_employee_id) is not int or actor_employee_id <= 0:
            raise DomainOperationError(
                "actor_employee_id must be a positive integer"
            )

        if type(contact_user_id) is not int or contact_user_id < 0:
            raise DomainOperationError(
                "contact_user_id must be a non-negative integer"
            )

        if ticket.user_id <= 0:
            raise DomainOperationError(
                "Linked Ticket must have positive user_id"
            )

        if not ticket.rule.can_change_data:
            raise DomainOperationError(
                "Cannot change contact User in current Ticket status "
                f"{ticket.current_status().value}"
            )

        if ticket_user.is_terminal():
            raise DomainOperationError(
                "Cannot change contact User of terminal TicketUser"
            )

        resolved_contact_user_id = (
            contact_user_id if contact_user_id > 0 else ticket.user_id
        )

        ticket.change_contact_user(
            contact_user_id=resolved_contact_user_id,
        )
        ticket_user.change_contact_user(
            actor_employee_id=actor_employee_id,
            contact_user_id=resolved_contact_user_id,
        )

        self.ensure_consistent(ticket, ticket_user)

    # ==================================================================
    # Internal helpers
    # ==================================================================

    @staticmethod
    def _ticket_user_status_for(ticket: Ticket) -> TicketUserStatus:
        """Return the user-facing status of a linked, user-originated Ticket.

        The mapping is intentionally partial. Admin-initiated CREATED is
        not mapped and must not be synchronized to a TicketUser.
        """
        ticket_status = ticket.current_status()

        try:
            return TICKET_TO_TICKET_USER_STATUS[ticket_status]
        except KeyError as exc:
            raise DomainOperationError(
                "Ticket status has no TicketUser status mapping: "
                f"{ticket_status.value}"
            ) from exc

    def _ensure_workflow_consistent(
        self,
        ticket: Ticket,
        ticket_user: TicketUser,
    ) -> None:
        """Check that both aggregates currently represent the same state."""
        expected_status = self._ticket_user_status_for(ticket)
        actual_status = ticket_user.current_status()

        if actual_status != expected_status:
            raise DomainOperationError(
                "Ticket and TicketUser workflow states are inconsistent: "
                f"Ticket status {ticket.current_status().value} "
                f"corresponds to TicketUser status {expected_status.value}, "
                f"but actual TicketUser status is {actual_status.value}"
            )
