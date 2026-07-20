import pytest

from src.domain.client import Client
from src.domain.employee import Admin, User
from src.domain.exceptions import DomainOperationError
from src.domain.policies.ticket import TicketPolicy
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser


def test_ticket_policy_accepts_valid_references():
    client = Client.create(client_id=1, name="Acme")
    admin = Admin.create(employee_id=1, first_name="John")
    user = User.create(employee_id=2, first_name="Alice", client_id=1)
    user_ticket = TicketUser.create(ticket_id=1, client_id=1, user_id=2, description="Need help")

    TicketPolicy.ensure_client_enabled(client)
    TicketPolicy.ensure_admin_enabled(admin)
    TicketPolicy.ensure_user_enabled(user)
    TicketPolicy.ensure_user_belongs_to_client(user, client)
    TicketPolicy.ensure_ticket_user_belongs_to_client(user_ticket, client)


def test_ticket_policy_rejects_disabled_client_admin_user():
    client = Client.create(client_id=1, name="Acme", enabled=False)
    admin = Admin.create(employee_id=1, first_name="John", enabled=False)
    user = User.create(employee_id=2, first_name="Alice", client_id=1, enabled=False)

    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_client_enabled(client)
    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_admin_enabled(admin)
    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_user_enabled(user)


def test_ticket_policy_rejects_user_for_different_client():
    client = Client.create(client_id=1, name="Acme")
    user = User.create(employee_id=2, first_name="Alice", client_id=2)

    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_user_belongs_to_client(user, client)


def test_ticket_policy_rejects_ticket_with_user_ticket():
    ticket = Ticket.create(
        ticket_id=1,
        client_id=1,
        admin_id=1,
        text_of_ticket="Problem",
        user_ticket_id=99,
    )

    with pytest.raises(DomainOperationError):
        TicketPolicy.ensure_ticket_does_not_have_ticket_user(ticket)
