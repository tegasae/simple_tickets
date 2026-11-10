"""Synchronize the linked Ticket and TicketUser aggregates.

Ticket -> TicketUser:
    - contact_user_id always comes from Ticket;
    - the user-facing status changes only when Ticket's mapped status changes;
    - status actor and comment come from Ticket's current status record.

TicketUser -> Ticket:
    - only user confirmation and cancellation are projected back to Ticket;
    - contact_user_id still comes from Ticket;
    - the new Ticket status comment comes from TicketUser's current record.

The service checks *relationships between* aggregates, not the internal
validity of either aggregate. Each aggregate validates its own operations.
Persistence and transaction management belong to the application layer.
"""

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.mapping_statuses import TICKET_TO_TICKET_USER_STATUS
from src.domain.statuses.ticket_user_status import TicketUserStatus
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from src.domain.value_objects import CommonComment


class TicketSyncService:
    """Synchronize two aggregates in an explicitly chosen direction."""

    def sync_from_ticket(
            self,
            ticket: Ticket,
            ticket_user: TicketUser | None,
    ) -> None:
        """Synchronize contact and user-facing workflow from Ticket."""

        linked = self._linked_ticket_user(ticket, ticket_user)
        if linked is None:
            return

        target_status = self._ticket_user_status_for(ticket)
        current_status = linked.current_status()

        actions = {
            TicketUserStatus.IN_WORK: linked.mark_in_work,
            TicketUserStatus.WAITING_FOR_CONFIRMATION:
                linked.mark_waiting_for_confirmation,
            TicketUserStatus.SUSPENDED: linked.suspend,
            TicketUserStatus.CONFIRMED_BY_ADMIN: linked.confirm_by_admin,
            TicketUserStatus.CANCELLED_BY_ADMIN: linked.cancel_by_admin,
        }

        if target_status != current_status:
            if target_status not in actions:
                raise DomainOperationError(
                    "Ticket status cannot be synchronized from Ticket: "
                    f"{ticket.current_status().value}"
                )

        # Сначала контакт, затем возможный терминальный статус.
        self._sync_contact(ticket, linked)

        if target_status != current_status:
            record = ticket.current_status_record()

            actions[target_status](
                actor_employee_id=record.actor_employee_id,
                comment=self._comment_text(record.comment),
            )

        self._ensure_synchronized(ticket, linked)

    def sync_from_ticket_user(
        self,
        ticket: Ticket,
        ticket_user: TicketUser,
    ) -> None:
        """Apply user confirmation/cancellation to Ticket; align contact."""
        linked = self._linked_ticket_user(ticket, ticket_user)
        if linked is None:
            raise DomainOperationError("TicketUser has to have Ticket")

        user_status = linked.current_status()
        expected_status = self._ticket_user_status_for(ticket)

        if user_status != expected_status and user_status not in {
            TicketUserStatus.CONFIRMED_BY_USER,
            TicketUserStatus.CANCELLED_BY_USER,
        }:
            raise DomainOperationError(
                "TicketUser status cannot be synchronized to Ticket: "
                f"{user_status.value}"
            )

        # Contact remains unidirectional even when workflow flows in reverse.
        #self._sync_contact(ticket, linked)

        if user_status != expected_status:
            comment = self._comment_text(linked.current_status_record().comment)
            if user_status == TicketUserStatus.CONFIRMED_BY_USER:
                ticket.confirm_by_user(comment=comment)
            else:
                ticket.cancel_by_user(comment=comment)

        self._ensure_synchronized(ticket, linked)

    @staticmethod
    def _linked_ticket_user(
        ticket: Ticket,
        ticket_user: TicketUser | None,
    ) -> TicketUser | None:
        """Check only pair linkage/ownership; allow standalone Tickets."""
        if ticket.user_ticket_id == 0:
            if ticket_user is not None:
                raise DomainOperationError(
                    "Standalone Ticket must not have TicketUser"
                )
            return None

        if ticket_user is None:
            raise DomainOperationError("Linked Ticket requires TicketUser")

        if ticket.user_ticket_id != ticket_user.ticket_user_id:
            raise DomainOperationError(
                "Ticket.user_ticket_id does not match TicketUser.ticket_user_id"
            )
        if ticket.client_id != ticket_user.client_id:
            raise DomainOperationError(
                "Ticket and TicketUser have different client_id"
            )
        if ticket.user_id != ticket_user.user_id:
            raise DomainOperationError(
                "Ticket and TicketUser have different user_id"
            )

        return ticket_user

    @staticmethod
    def _sync_contact(ticket: Ticket, ticket_user: TicketUser) -> None:
        if ticket.contact_user_id != ticket_user.contact_user_id:
            ticket_user.change_contact_user(
                contact_user_id=ticket.contact_user_id,
            )

    @staticmethod
    def _comment_text(comment: object) -> str:
        return comment.value if isinstance(comment, CommonComment) else ""

    @staticmethod
    def _ticket_user_status_for(ticket: Ticket) -> TicketUserStatus:
        try:
            return TICKET_TO_TICKET_USER_STATUS[ticket.current_status()]
        except KeyError as exc:
            raise DomainOperationError(
                "Ticket status has no TicketUser mapping: "
                f"{ticket.current_status().value}"
            ) from exc

    def _ensure_synchronized(
        self,
        ticket: Ticket,
        ticket_user: TicketUser,
    ) -> None:
        """Check only cross-aggregate correspondence after synchronization."""
        if ticket.contact_user_id != ticket_user.contact_user_id:
            raise DomainOperationError(
                "Ticket and TicketUser contacts are not synchronized"
            )

        if self._ticket_user_status_for(ticket) != ticket_user.current_status():
            raise DomainOperationError(
                "Ticket and TicketUser workflow states are not synchronized"
            )
