# tests/domain/test_ticket_user.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.ticket_components import Comment
from src.domain.ticket_user import (
    StatusRecordTicketUser,
    TicketUser,
    TicketUserStatus,
)


CLIENT_ID = 10
USER_ID = 101
CONTACT_USER_ID = 102
ADMIN_ID = 201
OTHER_EMPLOYEE_ID = 301

TICKET_USER_ID = 5001

BASE_TIME = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)


def minutes_after(minutes: int) -> datetime:
    return BASE_TIME + timedelta(minutes=minutes)


def make_status_record(
    status: TicketUserStatus,
    *,
    actor_employee_id: int,
    comment: str = "",
    date_created: datetime = BASE_TIME,
) -> StatusRecordTicketUser:
    return StatusRecordTicketUser(
        actor_employee_id=actor_employee_id,
        status=status,
        comment=comment,
        date_created=date_created,
    )


def make_created_ticket_user() -> TicketUser:
    return TicketUser.create(
        ticket_id=0,
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="Need help",
        date_created=BASE_TIME,
    )


def make_confirmed_ticket_user() -> TicketUser:
    return TicketUser.rehydrate(
        ticket_id=TICKET_USER_ID,
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="Need help",
        statuses=[
            make_status_record(
                TicketUserStatus.CREATED,
                actor_employee_id=USER_ID,
                date_created=BASE_TIME,
            ),
            make_status_record(
                TicketUserStatus.CONFIRMED_BY_ADMIN,
                actor_employee_id=ADMIN_ID,
                date_created=minutes_after(1),
            ),
        ],
        date_created=BASE_TIME,
    )


def make_in_work_ticket_user() -> TicketUser:
    return TicketUser.rehydrate(
        ticket_id=TICKET_USER_ID,
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="Need help",
        statuses=[
            make_status_record(
                TicketUserStatus.CREATED,
                actor_employee_id=USER_ID,
                date_created=BASE_TIME,
            ),
            make_status_record(
                TicketUserStatus.CONFIRMED_BY_ADMIN,
                actor_employee_id=ADMIN_ID,
                date_created=minutes_after(1),
            ),
            make_status_record(
                TicketUserStatus.IN_WORK,
                actor_employee_id=ADMIN_ID,
                date_created=minutes_after(2),
            ),
        ],
        date_created=BASE_TIME,
    )


def make_waiting_for_confirmation_ticket_user() -> TicketUser:
    return TicketUser.rehydrate(
        ticket_id=TICKET_USER_ID,
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="Need help",
        statuses=[
            make_status_record(
                TicketUserStatus.CREATED,
                actor_employee_id=USER_ID,
                date_created=BASE_TIME,
            ),
            make_status_record(
                TicketUserStatus.CONFIRMED_BY_ADMIN,
                actor_employee_id=ADMIN_ID,
                date_created=minutes_after(1),
            ),
            make_status_record(
                TicketUserStatus.IN_WORK,
                actor_employee_id=ADMIN_ID,
                date_created=minutes_after(2),
            ),
            make_status_record(
                TicketUserStatus.WAITING_FOR_CONFIRMATION,
                actor_employee_id=ADMIN_ID,
                date_created=minutes_after(3),
            ),
        ],
        date_created=BASE_TIME,
    )


def test_create_allows_zero_ticket_id() -> None:
    ticket_user = TicketUser.create(
        ticket_id=0,
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="  Need help  ",
        description="  Description  ",
        urgency_level=2,
        comment="  Initial comment  ",
        date_created=BASE_TIME,
    )

    assert ticket_user.ticket_id == 0
    assert ticket_user.client_id == CLIENT_ID
    assert ticket_user.user_id == USER_ID
    assert ticket_user.contact_user_id == CONTACT_USER_ID
    assert ticket_user.text_of_ticket == "Need help"
    assert ticket_user.description == "Description"
    assert ticket_user.urgency_level == 2
    assert ticket_user.current_status() == TicketUserStatus.CREATED
    assert ticket_user.current_status_record().actor_employee_id == USER_ID

    assert len(ticket_user.comments) == 1
    assert ticket_user.comments[0].employee_id == USER_ID
    assert ticket_user.comments[0].comment == "Initial comment"




def test_create_rejects_zero_client_id() -> None:
    with pytest.raises(DomainOperationError):
        TicketUser.create(
            ticket_id=0,
            client_id=0,
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
            text_of_ticket="Need help",
        )


def test_create_rejects_zero_user_id() -> None:
    with pytest.raises(ItemValidationError):
        TicketUser.create(
            ticket_id=0,
            client_id=CLIENT_ID,
            user_id=0,
            contact_user_id=CONTACT_USER_ID,
            text_of_ticket="Need help",
        )


def test_create_rejects_empty_text() -> None:
    with pytest.raises(ItemValidationError):
        TicketUser.create(
            ticket_id=0,
            client_id=CLIENT_ID,
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
            text_of_ticket="   ",
        )


def test_create_confirmed_by_admin_allows_zero_ticket_id() -> None:
    ticket_user = TicketUser.create_confirmed_by_admin(
        ticket_id=0,
        client_id=CLIENT_ID,
        user_id=USER_ID,
        actor_admin_id=ADMIN_ID,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="Need help",
        comment="Confirmed by admin",
        date_created=BASE_TIME,
    )

    assert ticket_user.ticket_id == 0
    assert ticket_user.current_status() == TicketUserStatus.CONFIRMED_BY_ADMIN
    assert ticket_user.current_status_record().actor_employee_id == ADMIN_ID
    assert ticket_user.current_status_record().comment == "Confirmed by admin"



def test_create_confirmed_by_admin_rejects_zero_actor_admin_id() -> None:
    with pytest.raises(ItemValidationError):
        TicketUser.create_confirmed_by_admin(
            ticket_id=0,
            client_id=CLIENT_ID,
            user_id=USER_ID,
            actor_admin_id=0,
            contact_user_id=CONTACT_USER_ID,
            text_of_ticket="Need help",
        )


def test_rehydrate_requires_positive_ticket_id() -> None:
    with pytest.raises(DomainOperationError):
        TicketUser.rehydrate(
            ticket_id=0,
            client_id=CLIENT_ID,
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
            text_of_ticket="Need help",
            statuses=[
                make_status_record(
                    TicketUserStatus.CREATED,
                    actor_employee_id=USER_ID,
                ),
            ],
            date_created=BASE_TIME,
        )


def test_rehydrate_rejects_empty_status_history() -> None:
    with pytest.raises(DomainOperationError):
        TicketUser.rehydrate(
            ticket_id=TICKET_USER_ID,
            client_id=CLIENT_ID,
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
            text_of_ticket="Need help",
            statuses=[],
            date_created=BASE_TIME,
        )


def test_rehydrate_rejects_invalid_first_status() -> None:
    with pytest.raises(DomainOperationError):
        TicketUser.rehydrate(
            ticket_id=TICKET_USER_ID,
            client_id=CLIENT_ID,
            user_id=USER_ID,
            contact_user_id=CONTACT_USER_ID,
            text_of_ticket="Need help",
            statuses=[
                make_status_record(
                    TicketUserStatus.IN_WORK,
                    actor_employee_id=ADMIN_ID,
                ),
            ],
            date_created=BASE_TIME,
        )


def test_rehydrate_restores_persisted_ticket_user() -> None:
    ticket_user = TicketUser.rehydrate(
        ticket_id=TICKET_USER_ID,
        client_id=CLIENT_ID,
        user_id=USER_ID,
        contact_user_id=CONTACT_USER_ID,
        text_of_ticket="  Need help  ",
        description="  Description  ",
        urgency_level=3,
        statuses=[
            make_status_record(
                TicketUserStatus.CREATED,
                actor_employee_id=USER_ID,
            ),
        ],
        date_created=BASE_TIME,
        version=7,
    )

    assert ticket_user.ticket_id == TICKET_USER_ID
    assert ticket_user.text_of_ticket == "Need help"
    assert ticket_user.description == "Description"
    assert ticket_user.urgency_level == 3
    assert ticket_user.version == 7
    assert ticket_user.current_status() == TicketUserStatus.CREATED
    assert ticket_user.is_closed is False
    assert ticket_user.date_finished is None


def test_confirm_by_admin_from_created() -> None:
    ticket_user = make_created_ticket_user()

    ticket_user.confirm_by_admin(
        actor_employee_id=ADMIN_ID,
        comment="Confirmed",
    )

    assert ticket_user.current_status() == TicketUserStatus.CONFIRMED_BY_ADMIN
    assert ticket_user.current_status_record().actor_employee_id == ADMIN_ID
    assert ticket_user.current_status_record().comment == "Confirmed"
    assert ticket_user.is_closed is False


def test_mark_in_work_from_confirmed_by_admin() -> None:
    ticket_user = make_confirmed_ticket_user()

    ticket_user.mark_in_work(
        actor_employee_id=ADMIN_ID,
        comment="Started",
    )

    assert ticket_user.current_status() == TicketUserStatus.IN_WORK
    assert ticket_user.current_status_record().actor_employee_id == ADMIN_ID
    assert ticket_user.current_status_record().comment == "Started"


def test_mark_waiting_for_confirmation_from_in_work() -> None:
    ticket_user = make_in_work_ticket_user()

    ticket_user.mark_waiting_for_confirmation(
        actor_employee_id=ADMIN_ID,
        comment="Please confirm",
    )

    assert ticket_user.current_status() == TicketUserStatus.WAITING_FOR_CONFIRMATION
    assert ticket_user.current_status_record().actor_employee_id == ADMIN_ID
    assert ticket_user.current_status_record().comment == "Please confirm"


def test_confirm_execution_by_user_from_waiting_for_confirmation() -> None:
    ticket_user = make_waiting_for_confirmation_ticket_user()

    ticket_user.confirm_execution_by_user(
        actor_employee_id=USER_ID,
        comment="Looks good",
    )

    assert ticket_user.current_status() == TicketUserStatus.EXECUTION_CONFIRMED_BY_USER
    assert ticket_user.current_status_record().actor_employee_id == USER_ID
    assert ticket_user.current_status_record().comment == "Looks good"
    assert ticket_user.is_closed is True
    assert ticket_user.date_finished == ticket_user.current_status_record().date_created


def test_confirm_execution_by_admin_from_waiting_for_confirmation() -> None:
    ticket_user = make_waiting_for_confirmation_ticket_user()

    ticket_user.confirm_execution_by_admin(
        actor_employee_id=ADMIN_ID,
        comment="Closed by admin",
    )

    assert ticket_user.current_status() == TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN
    assert ticket_user.current_status_record().actor_employee_id == ADMIN_ID
    assert ticket_user.current_status_record().comment == "Closed by admin"
    assert ticket_user.is_closed is True


def test_cancel_by_user_from_created() -> None:
    ticket_user = make_created_ticket_user()

    ticket_user.cancel_by_user(
        actor_employee_id=USER_ID,
        comment="No longer needed",
    )

    assert ticket_user.current_status() == TicketUserStatus.CANCELLED_BY_USER
    assert ticket_user.current_status_record().actor_employee_id == USER_ID
    assert ticket_user.current_status_record().comment == "No longer needed"
    assert ticket_user.is_closed is True


def test_cancel_by_admin_from_created() -> None:
    ticket_user = make_created_ticket_user()

    ticket_user.cancel_by_admin(
        actor_employee_id=ADMIN_ID,
        comment="Rejected",
    )

    assert ticket_user.current_status() == TicketUserStatus.CANCELLED_BY_ADMIN
    assert ticket_user.current_status_record().actor_employee_id == ADMIN_ID
    assert ticket_user.current_status_record().comment == "Rejected"
    assert ticket_user.is_closed is True


def test_invalid_transition_is_rejected() -> None:
    ticket_user = make_created_ticket_user()

    with pytest.raises(DomainOperationError):
        ticket_user.mark_in_work(
            actor_employee_id=ADMIN_ID,
        )


def test_cannot_change_status_after_terminal_status() -> None:
    ticket_user = make_created_ticket_user()

    ticket_user.cancel_by_user(
        actor_employee_id=USER_ID,
        comment="Cancel",
    )

    with pytest.raises(DomainOperationError):
        ticket_user.confirm_by_admin(
            actor_employee_id=ADMIN_ID,
        )


def test_add_comment() -> None:
    ticket_user = make_created_ticket_user()

    ticket_user.add_comment(
        Comment(
            employee_id=USER_ID,
            comment="  Useful comment  ",
            date_created=minutes_after(1),
        ),
    )

    assert len(ticket_user.comments) == 1
    assert ticket_user.comments[0].employee_id == USER_ID
    assert ticket_user.comments[0].comment == "Useful comment"


def test_add_comment_rejects_empty_comment() -> None:
    ticket_user = make_created_ticket_user()

    with pytest.raises(DomainOperationError):
        ticket_user.add_comment(
            Comment(
                employee_id=USER_ID,
                comment="   ",
            ),
        )


def test_add_comment_rejects_terminal_ticket_user() -> None:
    ticket_user = make_created_ticket_user()

    ticket_user.cancel_by_user(
        actor_employee_id=USER_ID,
        comment="Cancel",
    )

    with pytest.raises(DomainOperationError):
        ticket_user.add_comment(
            Comment(
                employee_id=USER_ID,
                comment="Too late",
            ),
        )


def test_belong_counts_user_contact_status_actor_and_comment_author() -> None:
    ticket_user = make_created_ticket_user()

    ticket_user.confirm_by_admin(
        actor_employee_id=ADMIN_ID,
        comment="Confirmed",
    )

    ticket_user.add_comment(
        Comment(
            employee_id=OTHER_EMPLOYEE_ID,
            comment="Comment",
            date_created=minutes_after(1),
        ),
    )

    assert ticket_user.belong(USER_ID) is True
    assert ticket_user.belong(CONTACT_USER_ID) is True
    assert ticket_user.belong(ADMIN_ID) is True
    assert ticket_user.belong(OTHER_EMPLOYEE_ID) is True


def test_belong_returns_false_for_non_positive_employee_id() -> None:
    ticket_user = make_created_ticket_user()

    assert ticket_user.belong(0) is False
    assert ticket_user.belong(-1) is False