from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.ticket import Ticket, TicketStatus, TicketStatusRecord
from src.domain.ticket_components import Comment, ExecutorAssignment


def make_ticket() -> Ticket:
    return Ticket.create(ticket_id=1, client_id=10, admin_id=100, text_of_ticket="Broken printer")


def test_ticket_create_adds_created_status_only_once():
    ticket = make_ticket()

    assert ticket.current_status() == TicketStatus.CREATED
    assert len(ticket.statuses) == 1


def test_ticket_constructor_does_not_create_status_history():
    ticket = Ticket(ticket_id=1, client_id=10, admin_id=100, text_of_ticket="Plain construction")

    assert ticket.statuses == []
    with pytest.raises(DomainOperationError):
        ticket.current_status()


def test_ticket_rehydrate_requires_status_history():
    with pytest.raises(DomainOperationError):
        Ticket.rehydrate(
            ticket_id=1,
            client_id=10,
            admin_id=100,
            text_of_ticket="Loaded",
            statuses=[],
            date_created=datetime.now(timezone.utc),
        )


def test_ticket_rehydrate_recomputes_closed_state_from_status_history():
    finished_at = datetime.now(timezone.utc)
    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=10,
        admin_id=100,
        text_of_ticket="Loaded",
        statuses=[TicketStatusRecord(actor_employee_id=100, status=TicketStatus.EXECUTED, date_created=finished_at)],
        date_created=finished_at - timedelta(hours=1),
    )

    assert ticket.is_closed is True
    assert ticket.date_finished == finished_at


#@pytest.mark.xfail(reason="Current uploaded code has reversed status_is_frozen() logic. Remove xfail after fixing it.")
def test_ticket_allows_workflow_until_closed_and_rejects_mutation_after_close():
    ticket = make_ticket()

    ticket.add_executor(ExecutorAssignment(admin_id=100, executor_id=200))
    ticket.at_work(executor_id=100)
    ticket.execute(actor_employee_id=200, comment="Done")

    assert ticket.current_status() == TicketStatus.EXECUTED
    assert ticket.is_closed is True

    with pytest.raises(DomainOperationError):
        ticket.add_comment(Comment(employee_id=100, comment="late comment"))


def test_invalid_transition_is_rejected():
    ticket = make_ticket()

    with pytest.raises(DomainOperationError):
        ticket.change_status(TicketStatus.EXECUTED, actor_employee_id=100)


def test_cancel_requires_comment():
    ticket = make_ticket()

    with pytest.raises(DomainOperationError):
        ticket.cancel(actor_employee_id=100, comment="   ")


def test_belong_detects_admin_comment_status_and_executor():
    ticket = make_ticket()
    ticket.comments.append(Comment(employee_id=101, comment="note"))
    ticket.executors.append(ExecutorAssignment(admin_id=100, executor_id=102))

    assert ticket.belong(100) is True
    assert ticket.belong(101) is True
    assert ticket.belong(102) is True
    assert ticket.belong(999) is False


def test_working_time_counts_at_work_periods():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ticket = Ticket.rehydrate(
        ticket_id=1,
        client_id=10,
        admin_id=100,
        text_of_ticket="Loaded",
        date_created=base,
        statuses=[
            TicketStatusRecord(actor_employee_id=100, status=TicketStatus.CREATED, date_created=base),
            TicketStatusRecord(actor_employee_id=100, status=TicketStatus.AT_WORK, date_created=base + timedelta(minutes=5)),
            TicketStatusRecord(actor_employee_id=100, status=TicketStatus.DEFERRED, date_created=base + timedelta(minutes=35)),
        ],
    )

    assert ticket.working_time() == 30 * 60
