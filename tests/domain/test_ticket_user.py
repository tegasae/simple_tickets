from datetime import datetime, timezone

import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.ticket_components import Comment
from src.domain.ticket_user import StatusRecordTicketUser, StatusTicketOfClient, TicketUser


def make_user_ticket() -> TicketUser:
    return TicketUser.create(ticket_id=1, client_id=10, user_id=100, description="Need help")


def test_ticket_user_create_adds_created_status():
    ticket = make_user_ticket()

    assert ticket.current_status() == StatusTicketOfClient.CREATED
    assert len(ticket.statuses) == 1


def test_ticket_user_constructor_does_not_create_status_history():
    ticket = TicketUser(ticket_id=1, client_id=10, user_id=100, contact_user_id=0, description="Plain")

    assert ticket.statuses == []
    with pytest.raises(DomainOperationError):
        ticket.current_status()


def test_ticket_user_rehydrate_requires_status_history():
    with pytest.raises(DomainOperationError):
        TicketUser.rehydrate(
            ticket_id=1,
            client_id=10,
            user_id=100,
            contact_user_id=0,
            description="Loaded",
            statuses=[],
            date_created=datetime.now(timezone.utc),
        )


#@pytest.mark.xfail(reason="Current uploaded code has reversed status_is_frozen() logic. Remove xfail after fixing it.")
def test_ticket_user_confirm_start_execute_and_reject_after_close():
    ticket = make_user_ticket()

    ticket.confirm(actor_employee_id=200)
    ticket.start_work(actor_employee_id=200)
    ticket.execute(actor_employee_id=200)

    assert ticket.current_status() == StatusTicketOfClient.EXECUTED
    assert ticket.is_closed is True

    with pytest.raises(DomainOperationError):
        ticket.add_comment(Comment(employee_id=100, comment="late"))


def test_ticket_user_invalid_transition_is_rejected():
    ticket = make_user_ticket()

    with pytest.raises(DomainOperationError):
        ticket.execute(actor_employee_id=100)


def test_ticket_user_belong_detects_participants():
    ticket = make_user_ticket()
    ticket.contact_user_id = 101
    ticket.comments.append(Comment(employee_id=102, comment="note"))
    ticket.statuses.append(StatusRecordTicketUser(actor_employee_id=103, status=StatusTicketOfClient.CONFIRMED))

    assert ticket.belong(100) is True
    assert ticket.belong(101) is True
    assert ticket.belong(102) is True
    assert ticket.belong(103) is True
    assert ticket.belong(999) is False
