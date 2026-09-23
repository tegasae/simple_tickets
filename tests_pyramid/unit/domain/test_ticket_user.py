from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.ticket_components import Comment
from src.domain.ticket_user import (
    StatusRecordTicketUser,
    TicketUser,
    TicketUserStatus,
    _validate_ticket_user_transitions,
)

pytestmark = pytest.mark.unit
BASE = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


def make_ticket_user() -> TicketUser:
    return TicketUser.create(
        client_id=10,
        user_id=20,
        contact_user_id=21,
        text_of_ticket="Need help",
        date_created=BASE,
    )


def test_ticket_user_transition_table_is_complete_and_terminals_have_no_transitions() -> None:
    _validate_ticket_user_transitions()
    for status in TicketUserStatus:
        if TicketUserStatus.is_terminal(status):
            assert not any(TicketUserStatus.can_transition(status, target) for target in TicketUserStatus)


def test_ticket_user_first_statuses() -> None:
    assert TicketUserStatus.is_first_status(TicketUserStatus.CREATED)
    assert TicketUserStatus.is_first_status(TicketUserStatus.CONFIRMED_BY_ADMIN)
    assert not TicketUserStatus.is_first_status(TicketUserStatus.IN_WORK)


def test_status_record_requires_positive_actor_and_normalizes_comment_and_timezone() -> None:
    with pytest.raises(ItemValidationError):
        StatusRecordTicketUser(
            actor_employee_id=0,
            status=TicketUserStatus.CREATED,
            date_created=BASE,
        )
    record = StatusRecordTicketUser(
        actor_employee_id=1,
        status=TicketUserStatus.CREATED,
        date_created=datetime(2025, 1, 1, 12, 0),
        status_comment="  hello  ",
    )
    assert record.date_created.tzinfo is timezone.utc
    assert record.status_comment == "hello"


def test_status_record_rejects_future_time_and_too_long_comment() -> None:
    with pytest.raises(ItemValidationError):
        StatusRecordTicketUser(
            actor_employee_id=1,
            status=TicketUserStatus.CREATED,
            date_created=datetime.now(timezone.utc) + timedelta(days=1),
        )
    with pytest.raises(ItemValidationError):
        StatusRecordTicketUser(
            actor_employee_id=1,
            status=TicketUserStatus.CREATED,
            date_created=BASE,
            status_comment="x" * 1001,
        )


def test_user_creation_records_user_as_actor_and_initial_comment() -> None:
    ticket_user = TicketUser.create(
        client_id=10,
        user_id=20,
        text_of_ticket="Need help",
        comment="  note  ",
        date_created=BASE,
    )
    assert ticket_user.current_status() is TicketUserStatus.CREATED
    assert ticket_user.current_status_record().actor_employee_id == 20
    assert ticket_user.comments[0].employee_id == 20
    assert ticket_user.comments[0].comment == "note"


def test_admin_confirmed_creation_records_admin_actor() -> None:
    ticket_user = TicketUser.create_confirmed_by_admin(
        client_id=10,
        user_id=20,
        actor_admin_id=100,
        text_of_ticket="Need help",
        date_created=BASE,
    )
    assert ticket_user.current_status() is TicketUserStatus.CONFIRMED_BY_ADMIN
    assert ticket_user.current_status_record().actor_employee_id == 100


def test_new_factories_reject_nonzero_ticket_id_and_invalid_admin_actor() -> None:
    with pytest.raises(ItemValidationError):
        TicketUser.create(ticket_id=1, client_id=10, user_id=20, text_of_ticket="x")
    with pytest.raises(ItemValidationError):
        TicketUser.create_confirmed_by_admin(
            ticket_id=0,
            client_id=10,
            user_id=20,
            actor_admin_id=0,
            text_of_ticket="x",
        )


def test_rehydrate_requires_id_history_and_valid_transition_chain() -> None:
    record = StatusRecordTicketUser(
        actor_employee_id=20,
        status=TicketUserStatus.CREATED,
        date_created=BASE,
    )
    with pytest.raises(DomainOperationError):
        TicketUser.rehydrate(
            ticket_id=0,
            client_id=10,
            user_id=20,
            text_of_ticket="x",
            statuses=[record],
            date_created=BASE,
        )
    bad = [
        record,
        StatusRecordTicketUser(
            actor_employee_id=1,
            status=TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN,
            date_created=BASE + timedelta(minutes=1),
        ),
    ]
    with pytest.raises(DomainOperationError):
        TicketUser.rehydrate(
            ticket_id=1,
            client_id=10,
            user_id=20,
            text_of_ticket="x",
            statuses=bad,
            date_created=BASE,
        )


def test_happy_workflow_to_user_confirmation_updates_closed_state() -> None:
    ticket_user = make_ticket_user()
    ticket_user.confirm_by_admin(actor_employee_id=100)
    ticket_user.mark_in_work(actor_employee_id=100)
    ticket_user.mark_waiting_for_confirmation(actor_employee_id=100)
    terminal = ticket_user.confirm_execution_by_user(actor_employee_id=20)
    assert terminal.status is TicketUserStatus.EXECUTION_CONFIRMED_BY_USER
    assert ticket_user.is_closed
    assert ticket_user.date_finished == terminal.date_created


def test_terminal_ticket_user_cannot_transition_update_or_add_comment() -> None:
    ticket_user = make_ticket_user()
    ticket_user.cancel_by_user(actor_employee_id=20)
    with pytest.raises(DomainOperationError):
        ticket_user.confirm_by_admin(actor_employee_id=100)
    with pytest.raises(DomainOperationError):
        ticket_user.update_details(actor_employee_id=20, description="x")
    with pytest.raises(DomainOperationError):
        ticket_user.add_comment(Comment(employee_id=20, comment="late"))


def test_invalid_transition_is_rejected() -> None:
    ticket_user = make_ticket_user()
    with pytest.raises(DomainOperationError):
        ticket_user.mark_in_work(actor_employee_id=100)


def test_update_details_validates_actor_and_contact_id() -> None:
    ticket_user = make_ticket_user()
    with pytest.raises(DomainOperationError):
        ticket_user.update_details(actor_employee_id=0)
    with pytest.raises(DomainOperationError):
        ticket_user.update_details(actor_employee_id=20, contact_user_id=-1)
    ticket_user.update_details(
        actor_employee_id=20,
        description="  changed  ",
        contact_user_id=22,
    )
    assert ticket_user.description == "changed"
    assert ticket_user.contact_user_id == 22


def test_add_comment_trims_blank_and_new_lists() -> None:
    ticket_user = make_ticket_user()
    ticket_user.add_comment(Comment(employee_id=20, comment="  hello  ", date_created=BASE))
    assert ticket_user.comments[-1].comment == "hello"
    assert ticket_user.new_comments() == ticket_user.comments
    assert ticket_user.new_statuses() == ticket_user.statuses
    with pytest.raises(DomainOperationError):
        ticket_user.add_comment(Comment(employee_id=20, comment="   ", date_created=BASE))


