from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.services.ticket_execution_service import TicketExecutionService
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket


MANAGER_ID = 10
EXECUTOR_ID = 20
OTHER_EXECUTOR_ID = 30


def make_created_ticket() -> Ticket:
    return Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=MANAGER_ID,
        text_of_ticket="Fix internet connection",
    )


def make_assigned_ticket(*, executor_id: int = EXECUTOR_ID) -> Ticket:
    ticket = make_created_ticket()

    TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
    )

    TicketManagementService.assign(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=executor_id,
    )

    return ticket


def make_ready_to_work_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_created_ticket()

    TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
    )

    TicketManagementService.ready_to_work(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=executor_id,
        planned_start_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    return ticket


def make_at_work_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_assigned_ticket(executor_id=executor_id)

    TicketExecutionService.take_to_work(
        ticket=ticket,
        actor_employee_id=executor_id,
    )

    return ticket


def make_paused_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_at_work_ticket(executor_id=executor_id)

    TicketExecutionService.pause_work(
        ticket=ticket,
        actor_employee_id=executor_id,
    )

    return ticket


def make_offline_work_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_assigned_ticket(executor_id=executor_id)

    actual_started_at = datetime.now(timezone.utc) - timedelta(hours=2)
    actual_finished_at = datetime.now(timezone.utc) - timedelta(hours=1)

    TicketExecutionService.register_offline_work(
        ticket=ticket,
        actor_employee_id=executor_id,
        actual_started_at=actual_started_at,
        actual_finished_at=actual_finished_at,
    )

    return ticket


def test_take_to_work_from_assigned_ticket() -> None:
    ticket = make_assigned_ticket()

    record = TicketExecutionService.take_to_work(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        comment="started work",
    )

    assert record.status == TicketStatus.AT_WORK
    assert record.actor_employee_id == EXECUTOR_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_started_at is not None
    assert record.comment == "started work"

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_take_to_work_from_ready_to_work_ticket() -> None:
    ticket = make_ready_to_work_ticket()

    record = TicketExecutionService.take_to_work(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
    )

    assert record.status == TicketStatus.AT_WORK
    assert record.executor_id == EXECUTOR_ID

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_take_to_work_rejects_not_current_executor() -> None:
    ticket = make_assigned_ticket()

    with pytest.raises(DomainOperationError):
        TicketExecutionService.take_to_work(
            ticket=ticket,
            actor_employee_id=OTHER_EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_take_to_work_rejects_ticket_without_executor() -> None:
    ticket = make_created_ticket()

    TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
    )

    with pytest.raises(DomainOperationError):
        TicketExecutionService.take_to_work(
            ticket=ticket,
            actor_employee_id=EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert ticket.current_executor_id() == 0


def test_pause_work() -> None:
    ticket = make_at_work_ticket()

    record = TicketExecutionService.pause_work(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        comment="waiting for access",
    )

    assert record.status == TicketStatus.PAUSED
    assert record.actor_employee_id == EXECUTOR_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.comment == "waiting for access"

    assert ticket.current_status() == TicketStatus.PAUSED
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_pause_work_rejects_not_current_executor() -> None:
    ticket = make_at_work_ticket()

    with pytest.raises(DomainOperationError):
        TicketExecutionService.pause_work(
            ticket=ticket,
            actor_employee_id=OTHER_EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_resume_work() -> None:
    ticket = make_paused_ticket()

    record = TicketExecutionService.resume_work(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        comment="access received",
    )

    assert record.status == TicketStatus.AT_WORK
    assert record.actor_employee_id == EXECUTOR_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_started_at is not None
    assert record.comment == "access received"

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_resume_work_rejects_not_current_executor() -> None:
    ticket = make_paused_ticket()

    with pytest.raises(DomainOperationError):
        TicketExecutionService.resume_work(
            ticket=ticket,
            actor_employee_id=OTHER_EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.PAUSED
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_register_offline_work() -> None:
    ticket = make_assigned_ticket()

    actual_started_at = datetime.now(timezone.utc) - timedelta(hours=3)
    actual_finished_at = datetime.now(timezone.utc) - timedelta(hours=1)

    record = TicketExecutionService.register_offline_work(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        actual_started_at=actual_started_at,
        actual_finished_at=actual_finished_at,
        comment="work was completed offline",
    )

    assert record.status == TicketStatus.OFFLINE_WORK
    assert record.actor_employee_id == EXECUTOR_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_started_at == actual_started_at
    assert record.actual_finished_at == actual_finished_at
    assert record.comment == "work was completed offline"

    assert ticket.current_status() == TicketStatus.OFFLINE_WORK
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_register_offline_work_rejects_not_current_executor() -> None:
    ticket = make_assigned_ticket()

    actual_started_at = datetime.now(timezone.utc) - timedelta(hours=3)
    actual_finished_at = datetime.now(timezone.utc) - timedelta(hours=1)

    with pytest.raises(DomainOperationError):
        TicketExecutionService.register_offline_work(
            ticket=ticket,
            actor_employee_id=OTHER_EXECUTOR_ID,
            actual_started_at=actual_started_at,
            actual_finished_at=actual_finished_at,
        )

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_submit_for_review_from_at_work() -> None:
    ticket = make_at_work_ticket()

    record = TicketExecutionService.submit_for_review(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        comment="ready for review",
    )

    assert record.status == TicketStatus.READY_FOR_REVIEW
    assert record.actor_employee_id == EXECUTOR_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_finished_at is not None
    assert record.comment == "ready for review"

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_submit_for_review_from_offline_work_preserves_finish_time() -> None:
    ticket = make_offline_work_ticket()

    offline_finished_at = ticket.current_status_record().actual_finished_at

    record = TicketExecutionService.submit_for_review(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        comment="offline work submitted",
    )

    assert record.status == TicketStatus.READY_FOR_REVIEW
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_finished_at == offline_finished_at

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_submit_for_review_rejects_assigned_ticket() -> None:
    ticket = make_assigned_ticket()

    with pytest.raises(DomainOperationError):
        TicketExecutionService.submit_for_review(
            ticket=ticket,
            actor_employee_id=EXECUTOR_ID,
        )

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == EXECUTOR_ID