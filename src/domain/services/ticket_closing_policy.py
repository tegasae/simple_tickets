# src/domain/services/ticket_closing_policy.py

from typing import Iterable

from src.domain.ticket import Ticket, TicketStatus
from src.domain.ticket_user import TicketUser


class TicketClosingPolicy:
    """
    Domain service responsible for closing UserTicket
    based on related AdminTickets.
    """

    @staticmethod
    def can_close(admin_tickets: Iterable[Ticket]) -> bool:
        """
        Check if UserTicket can be closed.

        Rule:
            All admin tickets must be in terminal state.
        """

        if not admin_tickets:
            return False  # or True depending on your business rule

        for ticket in admin_tickets:
            if ticket.current_status() not in (
                TicketStatus.EXECUTED,
                TicketStatus.CANCELLED,
            ):
                return False

        return True

    @staticmethod
    def close_if_possible(
        user_ticket: TicketUser,
        admin_tickets: Iterable[Ticket],
        actor_employee_id: int,
    ) -> bool:
        """
        Close UserTicket if rule is satisfied.

        Returns:
            True if closed
            False otherwise
        """

        if not TicketClosingPolicy.can_close(admin_tickets):
            return False

        # prevent double closing
        if user_ticket.is_closed:
            return False

        user_ticket.execute(actor_employee_id)

        return True