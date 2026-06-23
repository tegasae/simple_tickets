# tests/domain/services/test_ticket_workflow_service_manager.py

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.service.ticket_workflow_service import TicketWorkflowService

from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket


NOW = datetime.now(timezone.utc)

FUTURE_START = NOW + timedelta(hours=1)
FUTURE_FINISH = NOW + timedelta(hours=2)


def make_created_ticket() -> Ticket:
    return Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=10,
        text_of_ticket="Fix internet connection",
    )


def make_accepted_ticket() -> Ticket:
    ticket = make_created_ticket()

    TicketWorkflowService.accept(
        ticket=ticket,
        actor_employee_id=10,
    )

    return ticket


def make_scheduled_ticket() -> Ticket:
    ticket = make_accepted_ticket()

    TicketWorkflowService.schedule(
        ticket=ticket,
        actor_employee_id=10,
        planned_start_at=FUTURE_START,
        planned_finish_at=FUTURE_FINISH,
    )

    return ticket


def make_assigned_ticket(*, executor_id: int = 20) -> Ticket:
    ticket = make_accepted_ticket()

    TicketWorkflowService.assign(
        ticket=ticket,
        actor_employee_id=10,
        executor_id=executor_id,
    )

    return ticket


def make_ready_to_work_ticket(*, executor_id: int = 20) -> Ticket:
    ticket = make_accepted_ticket()

    TicketWorkflowService.ready_to_work(
        ticket=ticket,
        actor_employee_id=10,
        executor_id=executor_id,
        planned_start_at=FUTURE_START,
        planned_finish_at=FUTURE_FINISH,
    )

    return ticket


def make_at_work_ticket(*, executor_id: int = 20) -> Ticket:
    ticket = make_assigned_ticket(executor_id=executor_id)

    TicketWorkflowService.take_to_work(
        ticket=ticket,
        actor_employee_id=executor_id,
    )

    return ticket


# ----------------------------
# accept()
# ----------------------------


def test_accept_created_ticket() -> None:
    ticket = make_created_ticket()

    record = TicketWorkflowService.accept(
        ticket=ticket,
        actor_employee_id=10,
        comment="accepted",
    )

    assert record.status == TicketStatus.ACCEPTED
    assert record.actor_employee_id == 10
    assert record.comment == "accepted"

    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert ticket.current_executor_id() == 0
    assert not ticket.is_closed


def test_accept_rejects_non_created_ticket() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(DomainOperationError):
        TicketWorkflowService.accept(
            ticket=ticket,
            actor_employee_id=10,
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


# ----------------------------
# reject()
# ----------------------------


def test_reject_created_ticket() -> None:
    ticket = make_created_ticket()

    record = TicketWorkflowService.reject(
        ticket=ticket,
        actor_employee_id=10,
        comment="invalid request",
    )

    assert record.status == TicketStatus.REJECTED
    assert record.actor_employee_id == 10
    assert record.comment == "invalid request"

    assert ticket.current_status() == TicketStatus.REJECTED
    assert ticket.is_closed
    assert ticket.date_finished == record.date_created


def test_reject_requires_comment() -> None:
    ticket = make_created_ticket()

    with pytest.raises(ItemValidationError):
        TicketWorkflowService.reject(
            ticket=ticket,
            actor_employee_id=10,
            comment="",
        )

    assert ticket.current_status() == TicketStatus.CREATED


def test_reject_rejects_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(DomainOperationError):
        TicketWorkflowService.reject(
            ticket=ticket,
            actor_employee_id=10,
            comment="too late",
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


# ----------------------------
# defer()
# ----------------------------


def test_defer_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    record = TicketWorkflowService.defer(
        ticket=ticket,
        actor_employee_id=10,
        comment="waiting for client data",
    )

    assert record.status == TicketStatus.DEFERRED
    assert record.actor_employee_id == 10
    assert record.comment == "waiting for client data"

    assert ticket.current_status() == TicketStatus.DEFERRED
    assert ticket.current_executor_id() == 0


def test_defer_requires_comment() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(ItemValidationError):
        TicketWorkflowService.defer(
            ticket=ticket,
            actor_employee_id=10,
            comment="",
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_defer_at_work_ticket_as_manager_operation() -> None:
    ticket = make_at_work_ticket(executor_id=20)

    record = TicketWorkflowService.defer(
        ticket=ticket,
        actor_employee_id=10,
        comment="need client approval",
    )

    assert record.status == TicketStatus.DEFERRED

    assert ticket.current_status() == TicketStatus.DEFERRED
    assert ticket.current_executor_id() == 0


# ----------------------------
# schedule()
# ----------------------------


def test_schedule_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    record = TicketWorkflowService.schedule(
        ticket=ticket,
        actor_employee_id=10,
        planned_start_at=FUTURE_START,
        planned_finish_at=FUTURE_FINISH,
        comment="scheduled",
    )

    assert record.status == TicketStatus.SCHEDULED
    assert record.actor_employee_id == 10
    assert record.executor_id == 0
    assert record.planned_start_at == FUTURE_START
    assert record.planned_finish_at == FUTURE_FINISH
    assert record.comment == "scheduled"

    assert ticket.current_status() == TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0


def test_schedule_scheduled_ticket_again() -> None:
    ticket = make_scheduled_ticket()

    new_start = FUTURE_START + timedelta(days=1)
    new_finish = FUTURE_FINISH + timedelta(days=1)

    record = TicketWorkflowService.schedule(
        ticket=ticket,
        actor_employee_id=10,
        planned_start_at=new_start,
        planned_finish_at=new_finish,
        comment="rescheduled",
    )

    assert record.status == TicketStatus.SCHEDULED
    assert record.planned_start_at == new_start
    assert record.planned_finish_at == new_finish

    assert ticket.current_status() == TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0


def test_schedule_from_assigned_removes_executor() -> None:
    ticket = make_assigned_ticket(executor_id=20)

    record = TicketWorkflowService.schedule(
        ticket=ticket,
        actor_employee_id=10,
        planned_start_at=FUTURE_START,
    )

    assert record.status == TicketStatus.SCHEDULED
    assert record.executor_id == 0

    assert ticket.current_status() == TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0


# ----------------------------
# assign()
# ----------------------------


def test_assign_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    record = TicketWorkflowService.assign(
        ticket=ticket,
        actor_employee_id=10,
        executor_id=20,
        comment="assigned to technician",
    )

    assert record.status == TicketStatus.ASSIGNED
    assert record.actor_employee_id == 10
    assert record.executor_id == 20
    assert record.planned_start_at is None
    assert record.planned_finish_at is None
    assert record.comment == "assigned to technician"

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == 20


def test_assign_assigned_ticket_again_reassigns_executor() -> None:
    ticket = make_assigned_ticket(executor_id=20)

    record = TicketWorkflowService.assign(
        ticket=ticket,
        actor_employee_id=10,
        executor_id=30,
        comment="reassigned",
    )

    assert record.status == TicketStatus.ASSIGNED
    assert record.executor_id == 30

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == 30


def test_assign_from_ready_to_work_removes_planned_time() -> None:
    ticket = make_ready_to_work_ticket(executor_id=20)

    record = TicketWorkflowService.assign(
        ticket=ticket,
        actor_employee_id=10,
        executor_id=30,
    )

    assert record.status == TicketStatus.ASSIGNED
    assert record.executor_id == 30
    assert record.planned_start_at is None

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == 30


def test_assign_requires_executor() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(ItemValidationError):
        TicketWorkflowService.assign(
            ticket=ticket,
            actor_employee_id=10,
            executor_id=0,
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


# ----------------------------
# ready_to_work()
# ----------------------------


def test_ready_to_work_from_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    record = TicketWorkflowService.ready_to_work(
        ticket=ticket,
        actor_employee_id=10,
        executor_id=20,
        planned_start_at=FUTURE_START,
        planned_finish_at=FUTURE_FINISH,
        comment="ready",
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.actor_employee_id == 10
    assert record.executor_id == 20
    assert record.planned_start_at == FUTURE_START
    assert record.planned_finish_at == FUTURE_FINISH
    assert record.comment == "ready"

    assert ticket.current_status() == TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == 20


def test_ready_to_work_from_scheduled_adds_executor() -> None:
    ticket = make_scheduled_ticket()

    record = TicketWorkflowService.ready_to_work(
        ticket=ticket,
        actor_employee_id=10,
        executor_id=20,
        planned_start_at=FUTURE_START,
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.executor_id == 20
    assert record.planned_start_at == FUTURE_START

    assert ticket.current_status() == TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == 20


def test_ready_to_work_from_assigned_adds_planned_time() -> None:
    ticket = make_assigned_ticket(executor_id=20)

    record = TicketWorkflowService.ready_to_work(
        ticket=ticket,
        actor_employee_id=10,
        executor_id=20,
        planned_start_at=FUTURE_START,
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.executor_id == 20
    assert record.planned_start_at == FUTURE_START

    assert ticket.current_status() == TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == 20


def test_ready_to_work_again_changes_executor_or_planned_time() -> None:
    ticket = make_ready_to_work_ticket(executor_id=20)

    new_start = FUTURE_START + timedelta(days=1)

    record = TicketWorkflowService.ready_to_work(
        ticket=ticket,
        actor_employee_id=10,
        executor_id=30,
        planned_start_at=new_start,
        comment="changed executor and date",
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.executor_id == 30
    assert record.planned_start_at == new_start

    assert ticket.current_status() == TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == 30


def test_ready_to_work_requires_executor() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(ItemValidationError):
        TicketWorkflowService.ready_to_work(
            ticket=ticket,
            actor_employee_id=10,
            executor_id=0,
            planned_start_at=FUTURE_START,
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


# ----------------------------
# cancel()
# ----------------------------


def test_cancel_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    record = TicketWorkflowService.cancel(
        ticket=ticket,
        actor_employee_id=10,
        comment="client cancelled",
    )

    assert record.status == TicketStatus.CANCELLED
    assert record.actor_employee_id == 10
    assert record.comment == "client cancelled"

    assert ticket.current_status() == TicketStatus.CANCELLED
    assert ticket.is_closed
    assert ticket.date_finished == record.date_created


def test_cancel_requires_comment() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(ItemValidationError):
        TicketWorkflowService.cancel(
            ticket=ticket,
            actor_employee_id=10,
            comment="",
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_cancel_rejects_created_ticket() -> None:
    ticket = make_created_ticket()

    with pytest.raises(DomainOperationError):
        TicketWorkflowService.cancel(
            ticket=ticket,
            actor_employee_id=10,
            comment="cannot cancel created ticket",
        )

    assert ticket.current_status() == TicketStatus.CREATED


def test_cancel_at_work_ticket_as_manager_operation() -> None:
    ticket = make_at_work_ticket(executor_id=20)

    record = TicketWorkflowService.cancel(
        ticket=ticket,
        actor_employee_id=10,
        comment="client cancelled during work",
    )

    assert record.status == TicketStatus.CANCELLED

    assert ticket.current_status() == TicketStatus.CANCELLED
    assert ticket.is_closed


# ----------------------------
# Terminal protection
# ----------------------------


def test_manager_operation_rejects_terminal_ticket() -> None:
    ticket = make_accepted_ticket()

    TicketWorkflowService.cancel(
        ticket=ticket,
        actor_employee_id=10,
        comment="client cancelled",
    )

    with pytest.raises(DomainOperationError):
        TicketWorkflowService.schedule(
            ticket=ticket,
            actor_employee_id=10,
            planned_start_at=FUTURE_START,
        )

    assert ticket.current_status() == TicketStatus.CANCELLED