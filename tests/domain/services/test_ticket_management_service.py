from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.services.ticket_execution_service import TicketExecutionService
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket
from tests.domain.test_ticket import PAST_2H, PAST_1H

MANAGER_ID = 10
EXECUTOR_ID = 20


def future_start() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=1)


def future_finish() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=2)


def make_created_ticket() -> Ticket:
    return Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=MANAGER_ID,
        text_of_ticket="Fix internet connection",
    )


def make_accepted_ticket() -> Ticket:
    ticket = make_created_ticket()

    TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
    )

    return ticket


def make_scheduled_ticket() -> Ticket:
    ticket = make_accepted_ticket()

    TicketManagementService.schedule(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        planned_start_at=future_start(),
        planned_finish_at=future_finish(),
    )

    return ticket


def make_assigned_ticket(*, executor_id: int = EXECUTOR_ID) -> Ticket:
    ticket = make_accepted_ticket()

    TicketManagementService.assign(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=executor_id,
    )

    return ticket




def make_ready_to_work_ticket(*, executor_id: int = EXECUTOR_ID) -> Ticket:
    ticket = make_accepted_ticket()

    TicketManagementService.ready_to_work(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=executor_id,
        planned_start_at=future_start(),
        planned_finish_at=future_finish(),
    )

    return ticket


def make_at_work_ticket() -> Ticket:
    ticket = make_assigned_ticket()

    TicketExecutionService.take_to_work(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
    )

    return ticket


def make_ready_for_review_ticket() -> Ticket:
    ticket = make_ready_to_work_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=EXECUTOR_ID,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=EXECUTOR_ID,
            actual_started_at=PAST_2H,
            actual_finished_at=PAST_1H,
            comment="Work registered later",
        )
    )

    return ticket

def make_paused_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_at_work_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=executor_id,
            status=TicketStatus.PAUSED,
            executor_id=executor_id,
            comment="Work paused",
        )
    )

    return ticket

def test_accept_created_ticket() -> None:
    ticket = make_created_ticket()

    record = TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        comment="accepted",
    )

    assert record.status == TicketStatus.ACCEPTED
    assert record.actor_employee_id == MANAGER_ID
    assert record.comment == "accepted"

    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert ticket.current_executor_id() == 0
    assert not ticket.is_closed


def test_accept_deferred_ticket() -> None:
    ticket = make_accepted_ticket()

    TicketManagementService.defer(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        comment="waiting for client data",
    )

    record = TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        comment="data received",
    )

    assert record.status == TicketStatus.ACCEPTED
    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_accept_rejects_already_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(DomainOperationError):
        TicketManagementService.accept(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_reject_created_ticket() -> None:
    ticket = make_created_ticket()

    record = TicketManagementService.reject(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        comment="invalid request",
    )

    assert record.status == TicketStatus.REJECTED
    assert record.actor_employee_id == MANAGER_ID
    assert record.comment == "invalid request"

    assert ticket.current_status() == TicketStatus.REJECTED
    assert ticket.is_closed
    assert ticket.date_finished == record.date_created


def test_reject_requires_comment() -> None:
    ticket = make_created_ticket()

    with pytest.raises(ItemValidationError):
        TicketManagementService.reject(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            comment="",
        )

    assert ticket.current_status() == TicketStatus.CREATED


def test_reject_rejects_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(DomainOperationError):
        TicketManagementService.reject(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            comment="too late",
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_defer_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    record = TicketManagementService.defer(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        comment="waiting for client data",
    )

    assert record.status == TicketStatus.DEFERRED
    assert record.actor_employee_id == MANAGER_ID
    assert record.comment == "waiting for client data"

    assert ticket.current_status() == TicketStatus.DEFERRED
    assert ticket.current_executor_id() == 0


def test_defer_requires_comment() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(ItemValidationError):
        TicketManagementService.defer(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            comment="",
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_defer_at_work_ticket() -> None:
    ticket = make_at_work_ticket()

    record = TicketManagementService.defer(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        comment="need client approval",
    )

    assert record.status == TicketStatus.DEFERRED
    assert ticket.current_status() == TicketStatus.DEFERRED
    assert ticket.current_executor_id() == 0


def test_schedule_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    planned_start_at = future_start()
    planned_finish_at = future_finish()

    record = TicketManagementService.schedule(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        planned_start_at=planned_start_at,
        planned_finish_at=planned_finish_at,
        comment="scheduled",
    )

    assert record.status == TicketStatus.SCHEDULED
    assert record.actor_employee_id == MANAGER_ID
    assert record.executor_id == 0
    assert record.planned_start_at == planned_start_at
    assert record.planned_finish_at == planned_finish_at
    assert record.comment == "scheduled"

    assert ticket.current_status() == TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0


def test_schedule_scheduled_ticket_again() -> None:
    ticket = make_scheduled_ticket()

    planned_start_at = future_start() + timedelta(days=1)
    planned_finish_at = future_finish() + timedelta(days=1)

    record = TicketManagementService.schedule(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        planned_start_at=planned_start_at,
        planned_finish_at=planned_finish_at,
        comment="rescheduled",
    )

    assert record.status == TicketStatus.SCHEDULED
    assert record.planned_start_at == planned_start_at
    assert record.planned_finish_at == planned_finish_at

    assert ticket.current_status() == TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0


def test_schedule_from_assigned_removes_executor() -> None:
    ticket = make_assigned_ticket()

    record = TicketManagementService.schedule(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        planned_start_at=future_start(),
    )

    assert record.status == TicketStatus.SCHEDULED
    assert record.executor_id == 0

    assert ticket.current_status() == TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0


def test_assign_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    record = TicketManagementService.assign(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=EXECUTOR_ID,
        comment="assigned to technician",
    )

    assert record.status == TicketStatus.ASSIGNED
    assert record.actor_employee_id == MANAGER_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.planned_start_at is None
    assert record.planned_finish_at is None
    assert record.comment == "assigned to technician"

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_assign_assigned_ticket_again_reassigns_executor() -> None:
    ticket = make_assigned_ticket()

    record = TicketManagementService.assign(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=30,
        comment="reassigned",
    )

    assert record.status == TicketStatus.ASSIGNED
    assert record.executor_id == 30

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == 30


def test_assign_from_ready_to_work_removes_planned_time() -> None:
    ticket = make_ready_to_work_ticket()

    record = TicketManagementService.assign(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=30,
    )

    assert record.status == TicketStatus.ASSIGNED
    assert record.executor_id == 30
    assert record.planned_start_at is None
    assert record.planned_finish_at is None

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == 30


def test_assign_requires_executor() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(ItemValidationError):
        TicketManagementService.assign(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            executor_id=0,
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_ready_to_work_from_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    planned_start_at = future_start()
    planned_finish_at = future_finish()

    record = TicketManagementService.ready_to_work(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=EXECUTOR_ID,
        planned_start_at=planned_start_at,
        planned_finish_at=planned_finish_at,
        comment="ready",
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.actor_employee_id == MANAGER_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.planned_start_at == planned_start_at
    assert record.planned_finish_at == planned_finish_at
    assert record.comment == "ready"

    assert ticket.current_status() == TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_ready_to_work_from_scheduled_adds_executor() -> None:
    ticket = make_scheduled_ticket()

    planned_start_at = future_start()

    record = TicketManagementService.ready_to_work(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=EXECUTOR_ID,
        planned_start_at=planned_start_at,
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.executor_id == EXECUTOR_ID
    assert record.planned_start_at == planned_start_at

    assert ticket.current_status() == TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_ready_to_work_from_assigned_adds_planned_time() -> None:
    ticket = make_assigned_ticket()

    planned_start_at = future_start()

    record = TicketManagementService.ready_to_work(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=EXECUTOR_ID,
        planned_start_at=planned_start_at,
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.executor_id == EXECUTOR_ID
    assert record.planned_start_at == planned_start_at

    assert ticket.current_status() == TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_ready_to_work_again_changes_executor_and_planned_time() -> None:
    ticket = make_ready_to_work_ticket()

    planned_start_at = future_start() + timedelta(days=1)

    record = TicketManagementService.ready_to_work(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=30,
        planned_start_at=planned_start_at,
        comment="changed executor and date",
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.executor_id == 30
    assert record.planned_start_at == planned_start_at

    assert ticket.current_status() == TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == 30


def test_ready_to_work_requires_executor() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(ItemValidationError):
        TicketManagementService.ready_to_work(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            executor_id=0,
            planned_start_at=future_start(),
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_cancel_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    record = TicketManagementService.cancel(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        comment="client cancelled",
    )

    assert record.status == TicketStatus.CANCELLED
    assert record.actor_employee_id == MANAGER_ID
    assert record.comment == "client cancelled"

    assert ticket.current_status() == TicketStatus.CANCELLED
    assert ticket.is_closed
    assert ticket.date_finished == record.date_created


def test_cancel_requires_comment() -> None:
    ticket = make_accepted_ticket()

    with pytest.raises(ItemValidationError):
        TicketManagementService.cancel(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            comment="",
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED


def test_cancel_rejects_created_ticket() -> None:
    ticket = make_created_ticket()

    with pytest.raises(DomainOperationError):
        TicketManagementService.cancel(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            comment="cannot cancel created ticket",
        )

    assert ticket.current_status() == TicketStatus.CREATED


def test_cancel_at_work_ticket() -> None:
    ticket = make_at_work_ticket()

    record = TicketManagementService.cancel(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        comment="client cancelled during work",
    )

    assert record.status == TicketStatus.CANCELLED
    assert ticket.current_status() == TicketStatus.CANCELLED
    assert ticket.is_closed


def test_management_operation_rejects_terminal_ticket() -> None:
    ticket = make_accepted_ticket()

    TicketManagementService.cancel(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        comment="client cancelled",
    )

    with pytest.raises(DomainOperationError):
        TicketManagementService.schedule(
            ticket=ticket,
            actor_employee_id=MANAGER_ID,
            planned_start_at=future_start(),
        )

    assert ticket.current_status() == TicketStatus.CANCELLED

def test_handle_client_disabled_rejects_created_ticket() -> None:
    ticket = make_created_ticket()

    changed = TicketManagementService.handle_client_disabled(
        ticket=ticket,
        actor_employee_id=10,
        comment="Client disabled"
    )

    assert changed
    assert ticket.current_status() == TicketStatus.REJECTED
    assert ticket.current_status_record().comment == "Client disabled"

def test_handle_client_disabled_defers_accepted_ticket() -> None:
    ticket = make_accepted_ticket()

    changed = TicketManagementService.handle_client_disabled(
        ticket=ticket,
        actor_employee_id=10,
        comment="1"
    )

    assert changed
    assert ticket.current_status() == TicketStatus.DEFERRED

@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_at_work_ticket,
        make_paused_ticket,
        make_ready_for_review_ticket,
        make_ready_for_review_ticket,
    ],
)
def test_handle_client_disabled_does_not_change_in_progress_ticket(
    ticket_factory,
) -> None:
    ticket = ticket_factory()

    original_status = ticket.current_status()
    original_count = len(ticket.statuses)

    changed = TicketManagementService.handle_client_disabled(
        ticket=ticket,
        actor_employee_id=10,
    )

    assert not changed
    assert ticket.current_status() == original_status
    assert len(ticket.statuses) == original_count