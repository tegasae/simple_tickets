import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.policies.ticket_user_ticket import TicketUserTicketPolicy
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser


def test_can_cancel_or_delete_when_no_admin_ticket_exists():
    user_ticket = TicketUser.create(ticket_id=1, client_id=1, user_id=10, description="Need help",text_of_ticket="text")

    TicketUserTicketPolicy.can_cancel_user_ticket(user_ticket, None)
    TicketUserTicketPolicy.can_delete_user_ticket(user_ticket, None)


def test_cannot_delete_user_ticket_when_admin_ticket_exists():
    user_ticket = TicketUser.create(ticket_id=1, client_id=1, user_id=10, description="Need help",text_of_ticket="text")
    ticket = Ticket.create(ticket_id=2, client_id=1, admin_id=20, text_of_ticket="Admin ticket")

    with pytest.raises(DomainOperationError):
        TicketUserTicketPolicy.can_delete_user_ticket(user_ticket, ticket)


def test_cannot_cancel_user_ticket_when_admin_ticket_is_active():
    user_ticket = TicketUser.create(ticket_id=1, client_id=1, user_id=10, description="Need help",text_of_ticket="text")
    ticket = Ticket.create(ticket_id=2, client_id=1, admin_id=20, text_of_ticket="Admin ticket")

    with pytest.raises(DomainOperationError):
        TicketUserTicketPolicy.can_cancel_user_ticket(user_ticket, ticket)
