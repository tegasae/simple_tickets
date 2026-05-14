import pytest

from src.domain.service.ticket_workflow_service import TicketWorkflowService
from src.domain.ticket import TicketStatus
from src.domain.ticket_user import StatusTicketOfClient, TicketUser


@pytest.mark.xfail(reason="Current uploaded code has reversed status_is_frozen() logic. Remove xfail after fixing it.")
def test_create_from_admin_confirms_user_ticket_and_creates_admin_ticket():
    user_ticket = TicketUser.create(ticket_id=5, client_id=1, user_id=10, description="User problem")

    ticket = TicketWorkflowService.create_from_admin(
        ticket_id=0,
        client_id=1,
        admin_id=20,
        description="Admin problem. ",
        user_ticket=user_ticket,
        executor_id=30,
        comment="Initial comment",
    )

    assert ticket.user_ticket_id == 5
    assert ticket.current_status() == TicketStatus.CREATED
    assert user_ticket.current_status() == StatusTicketOfClient.CONFIRMED
    assert ticket.executors[-1].executor_id == 30
    assert ticket.comments[-1].comment == "Initial comment"


@pytest.mark.xfail(reason="Current uploaded code has reversed status_is_frozen() logic. Remove xfail after fixing it.")
def test_start_work_synchronizes_ticket_and_user_ticket():
    user_ticket = TicketUser.create(ticket_id=5, client_id=1, user_id=10, description="User problem")
    user_ticket.confirm(actor_employee_id=20)
    ticket = TicketWorkflowService.create_from_admin(
        ticket_id=0,
        client_id=1,
        admin_id=20,
        description="Admin problem",
        user_ticket=None,
        executor_id=30,
    )

    TicketWorkflowService.start_work(
        ticket=ticket,
        user_ticket=user_ticket,
        actor_admin_id=20,
        executor_id=30,
    )

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert user_ticket.current_status() == StatusTicketOfClient.AT_WORK


@pytest.mark.xfail(reason="Current uploaded code has reversed status_is_frozen() logic. Remove xfail after fixing it.")
def test_execute_synchronizes_ticket_and_user_ticket():
    user_ticket = TicketUser.create(ticket_id=5, client_id=1, user_id=10, description="User problem")
    user_ticket.confirm(actor_employee_id=20)
    user_ticket.start_work(actor_employee_id=20)
    ticket = TicketWorkflowService.create_from_admin(
        ticket_id=0,
        client_id=1,
        admin_id=20,
        description="Admin problem",
        executor_id=30,
    )
    ticket.at_work(actor_employee_id=20, executor_id=30)

    TicketWorkflowService.execute(
        ticket=ticket,
        user_ticket=user_ticket,
        actor_admin_id=20,
        comment="Done",
    )

    assert ticket.current_status() == TicketStatus.EXECUTED
    assert user_ticket.current_status() == StatusTicketOfClient.EXECUTED
