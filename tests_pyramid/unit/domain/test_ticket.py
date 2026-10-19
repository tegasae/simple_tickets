from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.services.ticket_execution_service import TicketExecutionService
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.services.ticket_review_service import TicketReviewService
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Comment, Ticket

pytestmark = pytest.mark.unit
BASE = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)


def make_created() -> Ticket:
    return Ticket.create(
        client_id=10,
        admin_id=100,
        text_of_ticket="Need help",
        department_id=5,
        date_created=BASE,
    )


def make_accepted() -> Ticket:
    ticket = make_created()
    TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=101,
        date_created=BASE + timedelta(minutes=1),
    )
    return ticket


def test_create_requires_new_id_positive_admin_and_nonempty_text() -> None:
    with pytest.raises(ItemValidationError):
        Ticket.create(ticket_id=1, client_id=10, admin_id=1, text_of_ticket="x")
    with pytest.raises(ItemValidationError):
        Ticket.create(client_id=10, admin_id=0, text_of_ticket="x")
    with pytest.raises(DomainOperationError):
        Ticket.create(client_id=10, admin_id=1, text_of_ticket="   ")


def test_create_adds_optional_initial_comment() -> None:
    ticket = Ticket.create(
        client_id=10,
        admin_id=100,
        text_of_ticket="Need help",
        comment="  note  ",
        date_created=BASE,
    )
    assert len(ticket.comments) == 1
    assert ticket.comments[0].employee_id == 100
    assert ticket.comments[0].comment == "note"


def test_create_from_ticket_user_validates_ids() -> None:
    with pytest.raises(ItemValidationError):
        Ticket.create_from_ticket_user(
            client_id=10,
            user_id=0,
            contact_user_id=0,
            user_ticket_id=1,
            text_of_ticket="Need help",
        )
    with pytest.raises(ItemValidationError):
        Ticket.create_from_ticket_user(
            client_id=10,
            user_id=1,
            contact_user_id=0,
            user_ticket_id=0,
            text_of_ticket="Need help",
        )


def test_rehydrate_requires_persisted_id_and_history() -> None:
    record = TicketStatusRecord.create_new(actor_employee_id=100, date_created=BASE)
    with pytest.raises(DomainOperationError):
        Ticket.rehydrate(
            ticket_id=0,
            client_id=10,
            admin_id=100,
            text_of_ticket="Need help",
            statuses=[record],
            date_created=BASE,
        )
    with pytest.raises(DomainOperationError):
        Ticket.rehydrate(
            ticket_id=1,
            client_id=10,
            admin_id=100,
            text_of_ticket="Need help",
            statuses=[],
            date_created=BASE,
        )


def test_rehydrate_rejects_invalid_transition_history() -> None:
    statuses = [
        TicketStatusRecord.create_new(actor_employee_id=100, date_created=BASE),
        TicketStatusRecord.create_executed(actor_employee_id=101, date_created=BASE + timedelta(minutes=1)),
    ]
    with pytest.raises(DomainOperationError):
        Ticket.rehydrate(
            ticket_id=1,
            client_id=10,
            admin_id=100,
            text_of_ticket="Need help",
            statuses=statuses,
            date_created=BASE,
        )


def test_current_executor_is_only_from_latest_record() -> None:
    ticket = make_accepted()
    TicketManagementService.assign(
        ticket=ticket,
        actor_employee_id=101,
        executor_id=200,
        date_created=BASE + timedelta(minutes=2),
    )
    assert ticket.current_executor_id() == 200
    assert ticket.has_executor()

    TicketManagementService.defer(
        ticket=ticket,
        actor_employee_id=101,
        comment="later",
        date_created=BASE + timedelta(minutes=3),
    )
    assert ticket.current_executor_id() == 0
    assert not ticket.has_executor()


def test_invalid_transition_is_rejected_without_changing_history() -> None:
    ticket = make_created()
    record = TicketStatusRecord.create_assigned(
        actor_employee_id=101,
        executor_id=200,
        date_created=BASE + timedelta(minutes=1),
    )
    with pytest.raises(DomainOperationError):
        ticket.append_status(record)
    assert len(ticket.statuses) == 1


def test_terminal_state_sets_derived_closed_state_and_date() -> None:
    ticket = make_created()
    finished = BASE + timedelta(minutes=1)
    TicketManagementService.reject(
        ticket=ticket,
        actor_employee_id=101,
        comment="invalid",
        date_created=finished,
    )
    assert ticket.is_closed
    assert ticket.date_finished == finished


def test_add_comment_trims_and_rejects_blank_or_terminal() -> None:
    ticket = make_created()
    ticket.add_comment(Comment(employee_id=1, comment="  hello  ", date_created=BASE))
    assert ticket.comments[-1].comment == "hello"
    with pytest.raises(DomainOperationError):
        ticket.add_comment(Comment(employee_id=1, comment="   ", date_created=BASE))

    TicketManagementService.reject(
        ticket=ticket,
        actor_employee_id=1,
        comment="reason",
        date_created=BASE + timedelta(minutes=1),
    )
    with pytest.raises(DomainOperationError):
        ticket.add_comment(Comment(employee_id=1, comment="late", date_created=BASE))


def test_change_department_allowed_before_lock_and_forbidden_while_assigned() -> None:
    ticket = make_accepted()
    ticket.change_department(department_id=6)
    assert ticket.department_id == 6

    TicketManagementService.assign(
        ticket=ticket,
        actor_employee_id=101,
        executor_id=200,
        date_created=BASE + timedelta(minutes=2),
    )
    with pytest.raises(DomainOperationError):
        ticket.change_department(department_id=7)


def test_update_details_validates_actor_terminal_and_contact_id() -> None:
    ticket = make_created()
    with pytest.raises(DomainOperationError):
        ticket.update_details(actor_employee_id=0)
    with pytest.raises(DomainOperationError):
        ticket.update_details(actor_employee_id=1, contact_user_id=-1)

    ticket.update_details(
        actor_employee_id=1,
        description="  desc  ",
        contact_user_id=20,
        is_remote=True,
    )
    assert ticket.description == "desc"
    assert ticket.contact_user_id == 20
    assert ticket.is_remote


def test_ticket_text_update_depends_on_current_state() -> None:
    ticket = make_created()
    ticket.update_ticket_text(text_of_ticket="new")
    assert ticket.text_of_ticket == "new"
    with pytest.raises(DomainOperationError):
        ticket.update_ticket_text(text_of_ticket="   ")

    TicketManagementService.accept(ticket=ticket, actor_employee_id=101, date_created=BASE + timedelta(minutes=1))
    TicketManagementService.assign(ticket=ticket, actor_employee_id=101, executor_id=200, date_created=BASE + timedelta(minutes=2))
    with pytest.raises(DomainOperationError):
        ticket.update_ticket_text(text_of_ticket="not allowed")


def test_update_description_forbids_empty_and_terminal() -> None:
    ticket = make_created()
    with pytest.raises(DomainOperationError):
        ticket.update_description(description="  ")
    ticket.update_description(description="  details ")
    assert ticket.description == "details"
    TicketManagementService.reject(ticket=ticket, actor_employee_id=1, comment="reason", date_created=BASE + timedelta(minutes=1))
    with pytest.raises(DomainOperationError):
        ticket.update_description(description="late")


def test_working_time_counts_online_interval_once() -> None:
    ticket = make_accepted()
    TicketManagementService.assign(ticket=ticket, actor_employee_id=101, executor_id=200, date_created=BASE + timedelta(minutes=2))

    # ExecutionService uses current real time for AT_WORK, so for deterministic
    # aggregate test append explicit records instead.
    at_work = TicketStatusRecord.create_at_work(
        actor_employee_id=200,
        executor_id=200,
        date_created=BASE + timedelta(minutes=3),
    )
    ticket.append_status(at_work)
    review = TicketStatusRecord.create_ready_for_review_from_work(
        actor_employee_id=200,
        executor_id=200,
        date_created=BASE + timedelta(minutes=13),
    )
    ticket.append_status(review)
    assert ticket.working_time() == 600


def test_working_time_counts_retrospective_interval() -> None:
    ticket = make_accepted()
    TicketManagementService.assign(ticket=ticket, actor_employee_id=101, executor_id=200, date_created=BASE + timedelta(minutes=2))
    review = TicketStatusRecord.create_ready_for_review_retrospective(
        actor_employee_id=101,
        executor_id=200,
        actual_started_at=BASE + timedelta(minutes=3),
        actual_finished_at=BASE + timedelta(minutes=8),
        date_created=BASE + timedelta(minutes=10),
    )
    ticket.append_status(review)
    assert ticket.working_time() == 300


def test_belong_checks_creator_status_actor_executor_and_comment() -> None:
    ticket = make_accepted()
    TicketManagementService.assign(ticket=ticket, actor_employee_id=101, executor_id=200, date_created=BASE + timedelta(minutes=2))
    ticket.add_comment(Comment(employee_id=300, comment="note", date_created=BASE))
    assert ticket.belong(100)
    assert ticket.belong(101)
    assert ticket.belong(200)
    assert ticket.belong(300)
    assert not ticket.belong(0)
    assert not ticket.belong(999)


def test_is_in_work_only_for_at_work_state() -> None:
    ticket = make_accepted()
    TicketManagementService.assign(ticket=ticket, actor_employee_id=101, executor_id=200, date_created=BASE + timedelta(minutes=2))
    assert not ticket.is_in_work()
    TicketExecutionService.take_to_work(ticket=ticket, actor_employee_id=200)
    assert ticket.current_status_record().status is TicketStatus.AT_WORK
    assert ticket.is_in_work()


def test_belong_returns_true_for_user_id() -> None:
    ticket = Ticket.create(
        client_id=1,
        admin_id=10,
        user_id=20,
        text_of_ticket="x",
    )

    assert ticket.belong(20) is True


def test_belong_returns_true_for_contact_user_id() -> None:
    ticket = Ticket.create(
        client_id=1,
        admin_id=10,
        contact_user_id=30,
        text_of_ticket="x",
    )

    assert ticket.belong(30) is True