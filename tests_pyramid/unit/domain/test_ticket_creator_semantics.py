from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.unit

from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket


CLIENT_ID = 10
CREATOR_ADMIN_ID = 101
ACCEPTOR_ADMIN_ID = 102
USER_ID = 201
CONTACT_USER_ID = 202
TICKET_USER_ID = 5001
TICKET_ID = 1001

BASE_TIME = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)


def test_admin_created_ticket_keeps_creator_admin_in_first_status() -> None:
    ticket = Ticket.create(
        client_id=CLIENT_ID,
        admin_id=CREATOR_ADMIN_ID,
        text_of_ticket="Need help",
        date_created=BASE_TIME,
    )

    first = ticket.statuses[0]

    assert ticket.admin_id == CREATOR_ADMIN_ID
    assert first.status == TicketStatus.CREATED
    assert first.actor_employee_id == CREATOR_ADMIN_ID


def test_ticket_created_from_ticket_user_has_no_creator_admin() -> None:
    ticket = Ticket.create_from_ticket_user(
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        user_ticket_id=TICKET_USER_ID,
        text_of_ticket="Need help",
        date_created=BASE_TIME,
    )

    first = ticket.statuses[0]

    assert ticket.admin_id == 0
    assert first.status == TicketStatus.CREATED_FROM_TICKET_USER
    assert first.actor_employee_id == 0


def test_accept_admin_created_ticket_does_not_change_creator_admin() -> None:
    ticket = Ticket.create(
        client_id=CLIENT_ID,
        admin_id=CREATOR_ADMIN_ID,
        text_of_ticket="Need help",
        date_created=BASE_TIME,
    )

    TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=ACCEPTOR_ADMIN_ID,
        date_created=BASE_TIME + timedelta(minutes=1),
    )

    assert ticket.admin_id == CREATOR_ADMIN_ID
    assert [record.status for record in ticket.statuses] == [
        TicketStatus.CREATED,
        TicketStatus.ACCEPTED,
    ]
    assert ticket.statuses[-1].actor_employee_id == ACCEPTOR_ADMIN_ID


def test_accept_ticket_created_from_user_keeps_admin_id_zero() -> None:
    ticket = Ticket.create_from_ticket_user(
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        user_ticket_id=TICKET_USER_ID,
        text_of_ticket="Need help",
        date_created=BASE_TIME,
    )

    TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=ACCEPTOR_ADMIN_ID,
        date_created=BASE_TIME + timedelta(minutes=1),
    )

    assert ticket.admin_id == 0
    assert [record.status for record in ticket.statuses] == [
        TicketStatus.CREATED_FROM_TICKET_USER,
        TicketStatus.ACCEPTED,
    ]
    assert ticket.statuses[-1].actor_employee_id == ACCEPTOR_ADMIN_ID


def test_rehydrate_rejects_creator_admin_mismatch_for_admin_created_ticket() -> None:
    statuses = [
        TicketStatusRecord.create_new(
            actor_employee_id=CREATOR_ADMIN_ID,
            date_created=BASE_TIME,
        ),
    ]

    with pytest.raises(DomainOperationError):
        Ticket.rehydrate(
            ticket_id=TICKET_ID,
            client_id=CLIENT_ID,
            admin_id=ACCEPTOR_ADMIN_ID,
            text_of_ticket="Need help",
            statuses=statuses,
            date_created=BASE_TIME,
        )


def test_rehydrate_rejects_nonzero_admin_for_ticket_created_from_user() -> None:
    statuses = [
        TicketStatusRecord.create_from_ticket_user(
            date_created=BASE_TIME,
        ),
    ]

    with pytest.raises(DomainOperationError):
        Ticket.rehydrate(
            ticket_id=TICKET_ID,
            client_id=CLIENT_ID,
            admin_id=CREATOR_ADMIN_ID,
            text_of_ticket="Need help",
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
            user_ticket_id=TICKET_USER_ID,
            statuses=statuses,
            date_created=BASE_TIME,
        )
