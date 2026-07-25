from src.domain.exceptions import DomainOperationError
from src.domain.ticket import Ticket, TicketStatus
from src.domain.ticket_user import TicketUser


class TicketUserTicketPolicy:
    """
    Domain policies for ticket and ticket_user.
    """
    """
     Можно ли снять заявку
    """
    @staticmethod
    def can_cancel_user_ticket(user_ticket:TicketUser,ticket:Ticket|None) -> None:
        if ticket and ticket.current_status():
            raise DomainOperationError(
                f"Cannot cancel a user ticket {user_ticket.ticket_id} with an active ticket {ticket.ticket_id}"
            )

    @staticmethod
    def can_delete_user_ticket(user_ticket: TicketUser, ticket: Ticket | None) -> None:
        if ticket:
            raise DomainOperationError(
                f"Cannot delete a user ticket {user_ticket.ticket_id} with an active ticket {ticket.ticket_id}"
            )
