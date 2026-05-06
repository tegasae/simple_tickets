from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.ticket_user import TicketUser
from src.domain.ticket import Ticket

class TicketPolicy:
    """
    Domain policy for ticket creation rules.
    """
    """
     проверка, что client enabled
    """
    @staticmethod
    def ensure_client_enabled(client: Client) -> None:
        if not client.enabled:
            raise DomainOperationError(
                f"Cannot create a ticket for disabled client {client.client_id}"
            )

    """
     проверка, что admin enabled
    """
    @staticmethod
    def ensure_admin_enabled(admin: Admin) -> None:
        if not admin.enabled:
            raise DomainOperationError(
                f"Cannot create a ticket with disabled admin {admin.employee_id}"
            )

    """
     проверка, что user enabled
    """
    @staticmethod
    def ensure_user_enabled(user: User) -> None:

        if not user.enabled:
            raise DomainOperationError(
                f"User {user.employee_id} is disabled"
            )

    """
     проверка, что user принадлежит client
    """
    @staticmethod
    def ensure_user_belongs_to_client(user: User, client: Client) -> None:
        if user.client_id != client.client_id:
            raise DomainOperationError(
                f"User {user.employee_id} does not belong to client {client.client_id}"
            )

    """
    Проверка, что ticket_user принадлежит client
    """
    @staticmethod
    def ensure_ticket_user_belongs_to_client(ticket_user:TicketUser,client:Client)->None:
        if ticket_user.client_id!=client.client_id:
            raise DomainOperationError(
                f"TicketUser {ticket_user.ticket_id} does not belong to client {client.client_id}"
            )

    """
        Проверка, что у ticket ticket_user_id нулевой 
    """
    @staticmethod
    def ensure_ticket_does_not_have_ticket_user(ticket: Ticket) -> None:
        if ticket.user_ticket_id:
            raise DomainOperationError(
                f"Ticket  {ticket.ticket_id} has a ticket user {ticket.user_ticket_id}"
            )


