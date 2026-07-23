# tests/domain/test_ticket.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Comment, Ticket


CLIENT_ID = 10
ADMIN_ID = 101
OTHER_ADMIN_ID = 102
USER_ID = 201
CONTACT_USER_ID = 202
EXECUTOR_ID = 301

TICKET_ID = 1001
TICKET_USER_ID = 5001

BASE_TIME = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)


def minutes_after(minutes: int) -> datetime:
    return BASE_TIME + timedelta(minutes=minutes)


def make_status_record(
    status: TicketStatus,
    *,
    actor_employee_id: int = ADMIN_ID,
    executor_id: int = 0,
    planned_start_at: datetime | None = None,
    planned_finish_at: datetime | None = None,
    actual_started_at: datetime | None = None,
    actual_finished_at: datetime | None = None,
    comment: str = "",
    date_created: datetime = BASE_TIME,
) -> TicketStatusRecord:
    return TicketStatusRecord(
        actor_employee_id=actor_employee_id,
        status=status,
        date_created=date_created,
        executor_id=executor_id,
        planned_start_at=planned_start_at,
        planned_finish_at=planned_finish_at,
        actual_started_at=actual_started_at,
        actual_finished_at=actual_finished_at,
        comment=comment,
    )


def make_created_ticket() -> Ticket:
    return Ticket.create(
        ticket_id=0,
        client_id=CLIENT_ID,
        admin_id=ADMIN_ID,
        text_of_ticket="Need help",
        date_created=BASE_TIME,
    )


def make_ticket_from_user() -> Ticket:
    return Ticket.create_from_ticket_user(
        ticket_id=0,
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        user_ticket_id=TICKET_USER_ID,
        text_of_ticket="Need help",
        date_created=BASE_TIME,
    )


def test_create_requires_zero_ticket_id() -> None:
    ticket = Ticket.create(
        ticket_id=0,
        client_id=CLIENT_ID,
        admin_id=ADMIN_ID,
        text_of_ticket="Need help",
        date_created=BASE_TIME,
    )

    assert ticket.ticket_id == 0
    assert ticket.is_new() is True
    assert ticket.current_status() == TicketStatus.CREATED
    assert ticket.current_status_record().actor_employee_id == ADMIN_ID


def test_create_rejects_nonzero_ticket_id() -> None:
    with pytest.raises(ItemValidationError):
        Ticket.create(
            ticket_id=TICKET_ID,
            client_id=CLIENT_ID,
            admin_id=ADMIN_ID,
            text_of_ticket="Need help",
        )


def test_create_rejects_zero_client_id() -> None:
    with pytest.raises(DomainOperationError):
        Ticket.create(
            ticket_id=0,
            client_id=0,
            admin_id=ADMIN_ID,
            text_of_ticket="Need help",
        )


def test_create_rejects_zero_admin_id() -> None:
    with pytest.raises(ItemValidationError):
        Ticket.create(
            ticket_id=0,
            client_id=CLIENT_ID,
            admin_id=0,
            text_of_ticket="Need help",
        )


def test_create_rejects_empty_text() -> None:
    with pytest.raises(DomainOperationError):
        Ticket.create(
            ticket_id=0,
            client_id=CLIENT_ID,
            admin_id=ADMIN_ID,
            text_of_ticket="   ",
        )


def test_create_adds_initial_comment() -> None:
    ticket = Ticket.create(
        ticket_id=0,
        client_id=CLIENT_ID,
        admin_id=ADMIN_ID,
        text_of_ticket="Need help",
        comment="  Initial comment  ",
        date_created=BASE_TIME,
    )

    assert len(ticket.comments) == 1
    assert ticket.comments[0].employee_id == ADMIN_ID
    assert ticket.comments[0].comment == "Initial comment"


def test_create_from_ticket_user_requires_zero_ticket_id() -> None:
    ticket = Ticket.create_from_ticket_user(
        ticket_id=0,
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        user_ticket_id=TICKET_USER_ID,
        text_of_ticket="Need help",
        date_created=BASE_TIME,
    )

    assert ticket.ticket_id == 0
    assert ticket.is_new() is True
    assert ticket.admin_id == 0
    assert ticket.user_id == USER_ID
    assert ticket.contact_user_id == CONTACT_USER_ID
    assert ticket.user_ticket_id == TICKET_USER_ID
    assert ticket.current_status() == TicketStatus.CREATED_FROM_TICKET_USER
    assert ticket.current_status_record().actor_employee_id == 0


def test_create_from_ticket_user_rejects_nonzero_ticket_id() -> None:
    with pytest.raises(ItemValidationError):
        Ticket.create_from_ticket_user(
            ticket_id=TICKET_ID,
            client_id=CLIENT_ID,
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
            user_ticket_id=TICKET_USER_ID,
            text_of_ticket="Need help",
        )


def test_create_from_ticket_user_rejects_zero_user_id() -> None:
    with pytest.raises(ItemValidationError):
        Ticket.create_from_ticket_user(
            ticket_id=0,
            client_id=CLIENT_ID,
            user_id=0,
            contact_user_id=CONTACT_USER_ID,
            user_ticket_id=TICKET_USER_ID,
            text_of_ticket="Need help",
        )


def test_create_from_ticket_user_rejects_zero_user_ticket_id() -> None:
    with pytest.raises(ItemValidationError):
        Ticket.create_from_ticket_user(
            ticket_id=0,
            client_id=CLIENT_ID,
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
            user_ticket_id=0,
            text_of_ticket="Need help",
        )


def test_rehydrate_requires_positive_ticket_id() -> None:
    with pytest.raises(DomainOperationError):
        Ticket.rehydrate(
            ticket_id=0,
            client_id=CLIENT_ID,
            admin_id=ADMIN_ID,
            text_of_ticket="Need help",
            statuses=[
                make_status_record(TicketStatus.CREATED),
            ],
            date_created=BASE_TIME,
        )


def test_rehydrate_restores_persisted_ticket() -> None:
    ticket = Ticket.rehydrate(
        ticket_id=TICKET_ID,
        client_id=CLIENT_ID,
        admin_id=ADMIN_ID,
        text_of_ticket="  Need help  ",
        statuses=[
            make_status_record(TicketStatus.CREATED),
        ],
        date_created=BASE_TIME,
        version=3,
    )

    assert ticket.ticket_id == TICKET_ID
    assert ticket.is_new() is False
    assert ticket.text_of_ticket == "Need help"
    assert ticket.current_status() == TicketStatus.CREATED
    assert ticket.version == 3


def test_rehydrate_rejects_empty_status_history() -> None:
    with pytest.raises(DomainOperationError):
        Ticket.rehydrate(
            ticket_id=TICKET_ID,
            client_id=CLIENT_ID,
            admin_id=ADMIN_ID,
            text_of_ticket="Need help",
            statuses=[],
            date_created=BASE_TIME,
        )


def test_accept_created_ticket() -> None:
    ticket = make_created_ticket()

    ticket.append_status(
        make_status_record(
            TicketStatus.ACCEPTED,
            actor_employee_id=ADMIN_ID,
            date_created=minutes_after(1),
        ),
    )

    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert ticket.admin_id == ADMIN_ID
    assert ticket.is_closed is False


def test_accept_ticket_created_from_user_sets_admin_id() -> None:
    ticket = make_ticket_from_user()

    assert ticket.admin_id == 0

    ticket.append_status(
        make_status_record(
            TicketStatus.ACCEPTED,
            actor_employee_id=ADMIN_ID,
            date_created=minutes_after(1),
        ),
    )

    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert ticket.admin_id == ADMIN_ID


def test_invalid_transition_is_rejected() -> None:
    ticket = make_created_ticket()

    with pytest.raises(DomainOperationError):
        ticket.append_status(
            make_status_record(
                TicketStatus.EXECUTED,
                actor_employee_id=ADMIN_ID,
                date_created=minutes_after(1),
            ),
        )


def test_terminal_status_closes_ticket() -> None:
    ticket = make_created_ticket()
    finished_at = minutes_after(1)

    ticket.append_status(
        make_status_record(
            TicketStatus.REJECTED,
            actor_employee_id=ADMIN_ID,
            comment="Rejected",
            date_created=finished_at,
        ),
    )

    assert ticket.current_status() == TicketStatus.REJECTED
    assert ticket.is_closed is True
    assert ticket.date_finished == finished_at


def test_cannot_change_status_after_terminal_status() -> None:
    ticket = make_created_ticket()

    ticket.append_status(
        make_status_record(
            TicketStatus.REJECTED,
            actor_employee_id=ADMIN_ID,
            comment="Rejected",
            date_created=minutes_after(1),
        ),
    )

    with pytest.raises(DomainOperationError):
        ticket.append_status(
            make_status_record(
                TicketStatus.ACCEPTED,
                actor_employee_id=ADMIN_ID,
                date_created=minutes_after(2),
            ),
        )


def test_add_comment() -> None:
    ticket = make_created_ticket()

    ticket.add_comment(
        Comment(
            employee_id=ADMIN_ID,
            comment="  Useful comment  ",
            date_created=minutes_after(1),
        ),
    )

    assert len(ticket.comments) == 1
    assert ticket.comments[0].employee_id == ADMIN_ID
    assert ticket.comments[0].comment == "Useful comment"


def test_add_comment_rejects_empty_comment() -> None:
    ticket = make_created_ticket()

    with pytest.raises(DomainOperationError):
        ticket.add_comment(
            Comment(
                employee_id=ADMIN_ID,
                comment="   ",
            ),
        )


def test_add_comment_rejects_terminal_ticket() -> None:
    ticket = make_created_ticket()

    ticket.append_status(
        make_status_record(
            TicketStatus.REJECTED,
            actor_employee_id=ADMIN_ID,
            comment="Rejected",
            date_created=minutes_after(1),
        ),
    )

    with pytest.raises(DomainOperationError):
        ticket.add_comment(
            Comment(
                employee_id=ADMIN_ID,
                comment="Too late",
            ),
        )


def test_change_department() -> None:
    ticket = make_created_ticket()

    ticket.change_department(department_id=77)

    assert ticket.department_id == 77


def test_change_department_rejects_negative_id() -> None:
    ticket = make_created_ticket()

    with pytest.raises(DomainOperationError):
        ticket.change_department(department_id=-1)


def test_belong_counts_admin_status_actor_executor_and_comment_author() -> None:
    ticket = make_created_ticket()

    ticket.append_status(
        make_status_record(
            TicketStatus.ACCEPTED,
            actor_employee_id=OTHER_ADMIN_ID,
            date_created=minutes_after(1),
        ),
    )

    ticket.append_status(
        make_status_record(
            TicketStatus.ASSIGNED,
            actor_employee_id=OTHER_ADMIN_ID,
            executor_id=EXECUTOR_ID,
            date_created=minutes_after(2),
        ),
    )

    ticket.add_comment(
        Comment(
            employee_id=999,
            comment="Comment",
            date_created=minutes_after(3),
        ),
    )

    assert ticket.belong(ADMIN_ID) is True
    assert ticket.belong(OTHER_ADMIN_ID) is True
    assert ticket.belong(EXECUTOR_ID) is True
    assert ticket.belong(999) is True


def test_belong_does_not_count_user_or_contact_user() -> None:
    ticket = Ticket.create(
        ticket_id=0,
        client_id=CLIENT_ID,
        admin_id=ADMIN_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="Need help",
        date_created=BASE_TIME,
    )

    assert ticket.belong(USER_ID) is False
    assert ticket.belong(CONTACT_USER_ID) is False


def test_belong_rejects_non_positive_employee_id() -> None:
    ticket = make_created_ticket()

    assert ticket.belong(0) is False
    assert ticket.belong(-1) is False