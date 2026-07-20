# tests/domain/test_ticket_user.py

from __future__ import annotations

import pytest

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.ticket_components import Comment
from src.domain.ticket_user import (
    StatusRecordTicketUser,
    StatusTicketOfClient,
    TicketUser,
    TicketUserStatus,
)


def test_create_ticket_user_creates_created_status() -> None:
    ticket_user = TicketUser.create(
        ticket_id=1,
        client_id=10,
        user_id=100,
        contact_user_id=0,
        text_of_ticket="Need help with printer",
        description="Printer does not work",
        urgency_level=2,
    )

    assert ticket_user.ticket_id == 1
    assert ticket_user.client_id == 10
    assert ticket_user.user_id == 100
    assert ticket_user.contact_user_id == 0
    assert ticket_user.text_of_ticket == "Need help with printer"
    assert ticket_user.description == "Printer does not work"
    assert ticket_user.urgency_level == 2

    assert ticket_user.current_status() == TicketUserStatus.CREATED
    assert ticket_user.current_status_record().actor_employee_id == 100

    assert not ticket_user.is_closed
    assert ticket_user.date_finished is None


def test_create_ticket_user_strips_text_and_description() -> None:
    ticket_user = TicketUser.create(
        ticket_id=1,
        client_id=10,
        user_id=100,
        text_of_ticket="  Need help  ",
        description="  Details  ",
    )

    assert ticket_user.text_of_ticket == "Need help"
    assert ticket_user.description == "Details"


def test_create_ticket_user_rejects_empty_text() -> None:
    with pytest.raises(ItemValidationError):
        TicketUser.create(
            ticket_id=1,
            client_id=10,
            user_id=100,
            text_of_ticket="   ",
        )


def test_create_ticket_user_rejects_invalid_ids() -> None:
    with pytest.raises(ItemValidationError):
        TicketUser.create(
            ticket_id=0,
            client_id=10,
            user_id=100,
            text_of_ticket="Need help",
        )

    with pytest.raises(ItemValidationError):
        TicketUser.create(
            ticket_id=1,
            client_id=0,
            user_id=100,
            text_of_ticket="Need help",
        )

    with pytest.raises(ItemValidationError):
        TicketUser.create(
            ticket_id=1,
            client_id=10,
            user_id=0,
            text_of_ticket="Need help",
        )

    with pytest.raises(ItemValidationError):
        TicketUser.create(
            ticket_id=1,
            client_id=10,
            user_id=100,
            contact_user_id=-1,
            text_of_ticket="Need help",
        )


def test_create_confirmed_by_admin_creates_confirmed_by_admin_status() -> None:
    ticket_user = TicketUser.create_confirmed_by_admin(
        ticket_id=1,
        client_id=10,
        user_id=100,
        actor_admin_id=500,
        text_of_ticket="Need help",
        description="Created by admin",
    )

    assert ticket_user.current_status() == TicketUserStatus.CONFIRMED_BY_ADMIN
    assert ticket_user.current_status_record().actor_employee_id == 500

    assert not ticket_user.is_closed
    assert ticket_user.date_finished is None


def test_create_confirmed_by_admin_rejects_invalid_actor_admin_id() -> None:
    with pytest.raises(ItemValidationError):
        TicketUser.create_confirmed_by_admin(
            ticket_id=1,
            client_id=10,
            user_id=100,
            actor_admin_id=0,
            text_of_ticket="Need help",
        )


def test_status_record_ticket_user_rejects_zero_actor() -> None:
    with pytest.raises(ItemValidationError):
        StatusRecordTicketUser(
            actor_employee_id=0,
            status=TicketUserStatus.CREATED,
        )


def test_status_record_ticket_user_rejects_negative_status_id() -> None:
    with pytest.raises(ItemValidationError):
        StatusRecordTicketUser(
            status_id=-1,
            actor_employee_id=100,
            status=TicketUserStatus.CREATED,
        )


def test_status_record_ticket_user_strips_comment() -> None:
    record = StatusRecordTicketUser(
        actor_employee_id=100,
        status=TicketUserStatus.CREATED,
        comment="  hello  ",
    )

    assert record.comment == "hello"


def test_created_can_be_cancelled_by_user() -> None:
    ticket_user = TicketUser.create(
        ticket_id=1,
        client_id=10,
        user_id=100,
        text_of_ticket="Need help",
    )

    record = ticket_user.cancel_by_user(
        actor_employee_id=100,
        comment="No longer needed",
    )

    assert record.status == TicketUserStatus.CANCELLED_BY_USER
    assert record.actor_employee_id == 100

    assert ticket_user.current_status() == TicketUserStatus.CANCELLED_BY_USER
    assert ticket_user.is_closed
    assert ticket_user.date_finished == record.date_created


def test_created_can_be_cancelled_by_admin() -> None:
    ticket_user = TicketUser.create(
        ticket_id=1,
        client_id=10,
        user_id=100,
        text_of_ticket="Need help",
    )

    record = ticket_user.cancel_by_admin(
        actor_employee_id=500,
        comment="Rejected",
    )

    assert record.status == TicketUserStatus.CANCELLED_BY_ADMIN
    assert record.actor_employee_id == 500

    assert ticket_user.current_status() == TicketUserStatus.CANCELLED_BY_ADMIN
    assert ticket_user.is_closed
    assert ticket_user.date_finished == record.date_created


def test_created_can_be_confirmed_by_admin() -> None:
    ticket_user = TicketUser.create(
        ticket_id=1,
        client_id=10,
        user_id=100,
        text_of_ticket="Need help",
    )

    record = ticket_user.confirm_by_admin(
        actor_employee_id=500,
        comment="Accepted",
    )

    assert record.status == TicketUserStatus.CONFIRMED_BY_ADMIN
    assert record.actor_employee_id == 500

    assert ticket_user.current_status() == TicketUserStatus.CONFIRMED_BY_ADMIN
    assert not ticket_user.is_closed
    assert ticket_user.date_finished is None


def test_confirmed_by_admin_cannot_be_cancelled_by_user() -> None:
    ticket_user = TicketUser.create(
        ticket_id=1,
        client_id=10,
        user_id=100,
        text_of_ticket="Need help",
    )

    ticket_user.confirm_by_admin(
        actor_employee_id=500,
    )

    with pytest.raises(DomainOperationError):
        ticket_user.cancel_by_user(
            actor_employee_id=100,
        )


def test_confirmed_by_admin_can_move_to_in_work() -> None:
    ticket_user = TicketUser.create_confirmed_by_admin(
        ticket_id=1,
        client_id=10,
        user_id=100,
        actor_admin_id=500,
        text_of_ticket="Need help",
    )

    record = ticket_user.mark_in_work(
        actor_employee_id=500,
    )

    assert record.status == TicketUserStatus.IN_WORK
    assert ticket_user.current_status() == TicketUserStatus.IN_WORK
    assert not ticket_user.is_closed


def test_in_work_can_move_to_waiting_for_confirmation() -> None:
    ticket_user = TicketUser.create_confirmed_by_admin(
        ticket_id=1,
        client_id=10,
        user_id=100,
        actor_admin_id=500,
        text_of_ticket="Need help",
    )

    ticket_user.mark_in_work(
        actor_employee_id=500,
    )

    record = ticket_user.mark_waiting_for_confirmation(
        actor_employee_id=500,
    )

    assert record.status == TicketUserStatus.WAITING_FOR_CONFIRMATION
    assert ticket_user.current_status() == TicketUserStatus.WAITING_FOR_CONFIRMATION
    assert not ticket_user.is_closed


def test_waiting_for_confirmation_can_be_confirmed_by_user() -> None:
    ticket_user = TicketUser.create_confirmed_by_admin(
        ticket_id=1,
        client_id=10,
        user_id=100,
        actor_admin_id=500,
        text_of_ticket="Need help",
    )

    ticket_user.mark_in_work(
        actor_employee_id=500,
    )
    ticket_user.mark_waiting_for_confirmation(
        actor_employee_id=500,
    )

    record = ticket_user.confirm_execution_by_user(
        actor_employee_id=100,
        comment="Done",
    )

    assert record.status == TicketUserStatus.EXECUTION_CONFIRMED_BY_USER
    assert record.actor_employee_id == 100

    assert ticket_user.current_status() == (
        TicketUserStatus.EXECUTION_CONFIRMED_BY_USER
    )
    assert ticket_user.is_closed
    assert ticket_user.date_finished == record.date_created


def test_waiting_for_confirmation_can_be_confirmed_by_admin() -> None:
    ticket_user = TicketUser.create_confirmed_by_admin(
        ticket_id=1,
        client_id=10,
        user_id=100,
        actor_admin_id=500,
        text_of_ticket="Need help",
    )

    ticket_user.mark_in_work(
        actor_employee_id=500,
    )
    ticket_user.mark_waiting_for_confirmation(
        actor_employee_id=500,
    )

    record = ticket_user.confirm_execution_by_admin(
        actor_employee_id=500,
        comment="Confirmed by admin",
    )

    assert record.status == TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN
    assert record.actor_employee_id == 500

    assert ticket_user.current_status() == (
        TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN
    )
    assert ticket_user.is_closed
    assert ticket_user.date_finished == record.date_created


def test_terminal_ticket_user_rejects_new_status() -> None:
    ticket_user = TicketUser.create(
        ticket_id=1,
        client_id=10,
        user_id=100,
        text_of_ticket="Need help",
    )

    ticket_user.cancel_by_user(
        actor_employee_id=100,
    )

    with pytest.raises(DomainOperationError):
        ticket_user.confirm_by_admin(
            actor_employee_id=500,
        )


def test_terminal_ticket_user_rejects_new_comment() -> None:
    ticket_user = TicketUser.create(
        ticket_id=1,
        client_id=10,
        user_id=100,
        text_of_ticket="Need help",
    )

    ticket_user.cancel_by_user(
        actor_employee_id=100,
    )

    with pytest.raises(DomainOperationError):
        ticket_user.add_comment(
            Comment(
                employee_id=100,
                comment="Late comment",
            ),
        )


def test_rehydrate_recomputes_closed_state() -> None:
    created_record = StatusRecordTicketUser(
        status_id=1,
        actor_employee_id=100,
        status=TicketUserStatus.CREATED,
    )
    cancelled_record = StatusRecordTicketUser(
        status_id=2,
        actor_employee_id=100,
        status=TicketUserStatus.CANCELLED_BY_USER,
    )

    ticket_user = TicketUser.rehydrate(
        ticket_id=1,
        client_id=10,
        user_id=100,
        text_of_ticket="Need help",
        statuses=[
            created_record,
            cancelled_record,
        ],
        is_closed=False,
        date_finished=None,
        date_created=created_record.date_created,
    )

    assert ticket_user.is_closed
    assert ticket_user.date_finished == cancelled_record.date_created


def test_rehydrate_rejects_invalid_status_history() -> None:
    created_record = StatusRecordTicketUser(
        status_id=1,
        actor_employee_id=100,
        status=TicketUserStatus.CREATED,
    )
    in_work_record = StatusRecordTicketUser(
        status_id=2,
        actor_employee_id=500,
        status=TicketUserStatus.IN_WORK,
    )

    with pytest.raises(DomainOperationError):
        TicketUser.rehydrate(
            ticket_id=1,
            client_id=10,
            user_id=100,
            text_of_ticket="Need help",
            statuses=[
                created_record,
                in_work_record,
            ],
            date_created=created_record.date_created,
        )


def test_status_ticket_of_client_alias_points_to_ticket_user_status() -> None:
    assert StatusTicketOfClient is TicketUserStatus


def test_belong_returns_true_for_user_contact_status_actor_and_comment_author() -> None:
    ticket_user = TicketUser.create(
        ticket_id=1,
        client_id=10,
        user_id=100,
        contact_user_id=101,
        text_of_ticket="Need help",
    )

    ticket_user.confirm_by_admin(
        actor_employee_id=500,
    )

    ticket_user.add_comment(
        Comment(
            employee_id=600,
            comment="Internal note",
        ),
    )

    assert ticket_user.belong(100)
    assert ticket_user.belong(101)
    assert ticket_user.belong(500)
    assert ticket_user.belong(600)

    assert not ticket_user.belong(0)
    assert not ticket_user.belong(-1)
    assert not ticket_user.belong(999)