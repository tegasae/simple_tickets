import pytest

from src.application.dto.ticket_dto import TicketDTO
from src.application.services.ticket_service import TicketApplicationService
from src.domain.exceptions import DomainOperationError
from src.domain.ticket import Ticket, TicketStatus
from src.domain.ticket_user import StatusTicketOfClient


def test_create_ticket_saves_ticket(uow, admin_with_all_permissions, client):
    service = TicketApplicationService(uow)

    dto = TicketDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        client_id=client.client_id,
        text_of_ticket="Broken printer",
    )

    result = service.create_ticket(ticket_dto=dto)

    assert result.ticket_id == 1
    saved_ticket = uow.tickets.get(result.ticket_id)
    assert saved_ticket.ticket_id == result.ticket_id
    saved_ticket = uow.tickets.get(result.ticket_id)
    assert saved_ticket.ticket_id == result.ticket_id


def test_create_ticket_from_user_ticket_saves_both(uow, admin_with_all_permissions, client, user_ticket):
    uow.user_tickets.items[user_ticket.ticket_id] = user_ticket
    service = TicketApplicationService(uow)

    dto = TicketDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        client_id=client.client_id,
        text_of_ticket="Admin created ticket",
        user_ticket_id=user_ticket.ticket_id,
    )

    result = service.create_ticket(ticket_dto=dto)

    assert result.user_ticket_id == user_ticket.ticket_id

    saved_ticket = uow.tickets.get(result.ticket_id)
    saved_user_ticket = uow.user_tickets.get(user_ticket.ticket_id)

    assert saved_ticket.user_ticket_id == user_ticket.ticket_id
    assert saved_user_ticket.ticket_id == user_ticket.ticket_id


def test_create_ticket_rejects_disabled_client(uow, admin_with_all_permissions, client):
    client.disable()
    service = TicketApplicationService(uow)

    dto = TicketDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        client_id=client.client_id,
        text_of_ticket="Broken printer",
    )

    with pytest.raises(DomainOperationError, match="disabled client"):
        service.create_ticket(ticket_dto=dto)


def test_at_work_updates_ticket_and_related_user_ticket(uow, admin_with_all_permissions, other_admin, client, user_ticket):
    ticket = Ticket.create(
        ticket_id=1,
        client_id=client.client_id,
        admin_id=admin_with_all_permissions.employee_id,
        text_of_ticket="Broken printer",
        user_ticket_id=user_ticket.ticket_id,
    )
    user_ticket.confirm(actor_employee_id=admin_with_all_permissions.employee_id)
    uow.tickets.items[ticket.ticket_id] = ticket
    uow.user_tickets.items[user_ticket.ticket_id] = user_ticket
    service = TicketApplicationService(uow)

    dto = TicketDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        ticket_id=ticket.ticket_id,
        client_id=client.client_id,
        executor_id=other_admin.employee_id,
    )


    result = service.at_work(ticket_dto=dto)

    assert result.statuses[-1]["status"] == TicketStatus.AT_WORK.value

    saved_user_ticket = uow.user_tickets.get(user_ticket.ticket_id)

    assert saved_user_ticket.current_status() == StatusTicketOfClient.AT_WORK
    assert saved_user_ticket.ticket_id == user_ticket.ticket_id


def test_execute_updates_ticket_and_related_user_ticket(uow, admin_with_all_permissions, other_admin, client, user_ticket):
    ticket = Ticket.create(
        ticket_id=1,
        client_id=client.client_id,
        admin_id=admin_with_all_permissions.employee_id,
        text_of_ticket="Broken printer",
        user_ticket_id=user_ticket.ticket_id,
    )
    user_ticket.confirm(actor_employee_id=admin_with_all_permissions.employee_id)
    ticket.at_work(actor_employee_id=admin_with_all_permissions.employee_id, executor_id=other_admin.employee_id)
    user_ticket.start_work(actor_employee_id=other_admin.employee_id)
    uow.tickets.items[ticket.ticket_id] = ticket
    uow.user_tickets.items[user_ticket.ticket_id] = user_ticket
    service = TicketApplicationService(uow)

    dto = TicketDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        admin_id=other_admin.employee_id,
        ticket_id=ticket.ticket_id,
        client_id=client.client_id,
        comment="Done",
    )

    result = service.execute(ticket_dto=dto)

    assert result.statuses[-1]["status"] == TicketStatus.EXECUTED.value
    assert user_ticket.current_status() == StatusTicketOfClient.EXECUTED


def test_cancel_requires_comment(uow, admin_with_all_permissions, client):
    ticket = Ticket.create(
        ticket_id=1,
        client_id=client.client_id,
        admin_id=admin_with_all_permissions.employee_id,
        text_of_ticket="Broken printer",
    )
    uow.tickets.items[ticket.ticket_id] = ticket
    service = TicketApplicationService(uow)

    dto = TicketDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        ticket_id=ticket.ticket_id,
        client_id=client.client_id,
        comment="   ",
    )

    with pytest.raises(DomainOperationError, match="Comment cannot be empty"):
        service.cancel(ticket_dto=dto)


def test_get_by_id_returns_dto(uow, admin_with_all_permissions, client):
    ticket = Ticket.create(
        ticket_id=1,
        client_id=client.client_id,
        admin_id=admin_with_all_permissions.employee_id,
        text_of_ticket="Broken printer",
    )
    uow.tickets.items[ticket.ticket_id] = ticket
    service = TicketApplicationService(uow)

    dto = TicketDTO(
        actor_admin_id=admin_with_all_permissions.employee_id,
        ticket_id=ticket.ticket_id,
        client_id=client.client_id,
    )

    result = service.get_by_id(ticket_dto=dto)

    assert result.ticket_id == ticket.ticket_id
    assert result.text_of_ticket == ticket.text_of_ticket
