from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError, ItemValidationError
from src.domain.services.ticket_execution_service import TicketExecutionService
from src.domain.services.ticket_management_service import TicketManagementService
from src.domain.services.ticket_review_service import TicketReviewService
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.ticket import Ticket


MANAGER_ID = 10
EXECUTOR_ID = 20
REVIEWER_ID = 30
NEW_EXECUTOR_ID = 40


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


def make_at_work_ticket() -> Ticket:
    ticket = make_created_ticket()

    TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
    )

    TicketManagementService.assign(
        ticket=ticket,
        actor_employee_id=MANAGER_ID,
        executor_id=EXECUTOR_ID,
    )

    TicketExecutionService.take_to_work(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
    )

    return ticket


def make_ready_for_review_ticket() -> Ticket:
    ticket = make_at_work_ticket()

    TicketExecutionService.submit_for_review(
        ticket=ticket,
        actor_employee_id=EXECUTOR_ID,
        comment="work completed",
    )

    return ticket


def test_confirm_execution_closes_ticket() -> None:
    ticket = make_ready_for_review_ticket()

    record = TicketReviewService.confirm_execution(
        ticket=ticket,
        actor_employee_id=REVIEWER_ID,
        comment="confirmed by client",
    )

    assert record.status == TicketStatus.EXECUTED
    assert record.actor_employee_id == REVIEWER_ID
    assert record.comment == "confirmed by client"

    assert ticket.current_status() == TicketStatus.EXECUTED
    assert ticket.current_executor_id() == 0
    assert ticket.is_closed
    assert ticket.date_finished == record.date_created


def test_confirm_execution_rejects_ticket_not_ready_for_review() -> None:
    ticket = make_at_work_ticket()

    with pytest.raises(DomainOperationError):
        TicketReviewService.confirm_execution(
            ticket=ticket,
            actor_employee_id=REVIEWER_ID,
        )

    assert ticket.current_status() == TicketStatus.AT_WORK


def test_return_to_work_keeps_current_executor() -> None:
    ticket = make_ready_for_review_ticket()

    before = datetime.now(timezone.utc)

    record = TicketReviewService.return_to_work(
        ticket=ticket,
        actor_employee_id=REVIEWER_ID,
        comment="please fix the result",
    )

    after = datetime.now(timezone.utc)

    assert record.status == TicketStatus.AT_WORK
    assert record.actor_employee_id == REVIEWER_ID
    assert record.executor_id == EXECUTOR_ID
    assert record.actual_started_at is not None
    assert before <= record.actual_started_at <= after
    assert record.comment == "please fix the result"

    assert ticket.current_status() == TicketStatus.AT_WORK
    assert ticket.current_executor_id() == EXECUTOR_ID


def test_return_to_assigned_can_change_executor() -> None:
    ticket = make_ready_for_review_ticket()

    record = TicketReviewService.return_to_assigned(
        ticket=ticket,
        actor_employee_id=REVIEWER_ID,
        executor_id=NEW_EXECUTOR_ID,
        comment="another specialist is required",
    )

    assert record.status == TicketStatus.ASSIGNED
    assert record.actor_employee_id == REVIEWER_ID
    assert record.executor_id == NEW_EXECUTOR_ID
    assert record.planned_start_at is None
    assert record.planned_finish_at is None

    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == NEW_EXECUTOR_ID


def test_return_to_assigned_requires_executor() -> None:
    ticket = make_ready_for_review_ticket()

    with pytest.raises(ItemValidationError):
        TicketReviewService.return_to_assigned(
            ticket=ticket,
            actor_employee_id=REVIEWER_ID,
            executor_id=0,
        )

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW


def test_return_to_scheduled_removes_executor() -> None:
    ticket = make_ready_for_review_ticket()

    planned_start_at = future_start()
    planned_finish_at = future_finish()

    record = TicketReviewService.return_to_scheduled(
        ticket=ticket,
        actor_employee_id=REVIEWER_ID,
        planned_start_at=planned_start_at,
        planned_finish_at=planned_finish_at,
        comment="need new schedule",
    )

    assert record.status == TicketStatus.SCHEDULED
    assert record.actor_employee_id == REVIEWER_ID
    assert record.executor_id == 0
    assert record.planned_start_at == planned_start_at
    assert record.planned_finish_at == planned_finish_at
    assert record.comment == "need new schedule"

    assert ticket.current_status() == TicketStatus.SCHEDULED
    assert ticket.current_executor_id() == 0


def test_return_to_ready_to_work_sets_executor_and_schedule() -> None:
    ticket = make_ready_for_review_ticket()

    planned_start_at = future_start()
    planned_finish_at = future_finish()

    record = TicketReviewService.return_to_ready_to_work(
        ticket=ticket,
        actor_employee_id=REVIEWER_ID,
        executor_id=NEW_EXECUTOR_ID,
        planned_start_at=planned_start_at,
        planned_finish_at=planned_finish_at,
        comment="new executor and schedule",
    )

    assert record.status == TicketStatus.READY_TO_WORK
    assert record.actor_employee_id == REVIEWER_ID
    assert record.executor_id == NEW_EXECUTOR_ID
    assert record.planned_start_at == planned_start_at
    assert record.planned_finish_at == planned_finish_at
    assert record.comment == "new executor and schedule"

    assert ticket.current_status() == TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == NEW_EXECUTOR_ID


def test_return_to_ready_to_work_requires_executor() -> None:
    ticket = make_ready_for_review_ticket()

    with pytest.raises(ItemValidationError):
        TicketReviewService.return_to_ready_to_work(
            ticket=ticket,
            actor_employee_id=REVIEWER_ID,
            executor_id=0,
            planned_start_at=future_start(),
        )

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW


def test_return_to_deferred_requires_comment() -> None:
    ticket = make_ready_for_review_ticket()

    with pytest.raises(ItemValidationError):
        TicketReviewService.return_to_deferred(
            ticket=ticket,
            actor_employee_id=REVIEWER_ID,
            comment="",
        )

    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW


def test_return_to_deferred_creates_deferred_status() -> None:
    ticket = make_ready_for_review_ticket()

    record = TicketReviewService.return_to_deferred(
        ticket=ticket,
        actor_employee_id=REVIEWER_ID,
        comment="waiting for client confirmation",
    )

    assert record.status == TicketStatus.DEFERRED
    assert record.actor_employee_id == REVIEWER_ID
    assert record.comment == "waiting for client confirmation"

    assert ticket.current_status() == TicketStatus.DEFERRED
    assert ticket.current_executor_id() == 0


def test_reviewer_operation_rejects_ticket_not_ready_for_review() -> None:
    ticket = make_at_work_ticket()

    with pytest.raises(DomainOperationError):
        TicketReviewService.return_to_scheduled(
            ticket=ticket,
            actor_employee_id=REVIEWER_ID,
            planned_start_at=future_start(),
        )

    assert ticket.current_status() == TicketStatus.AT_WORK


def test_reviewer_operation_rejects_terminal_ticket() -> None:
    ticket = make_ready_for_review_ticket()

    TicketReviewService.confirm_execution(
        ticket=ticket,
        actor_employee_id=REVIEWER_ID,
    )

    with pytest.raises(DomainOperationError):
        TicketReviewService.return_to_work(
            ticket=ticket,
            actor_employee_id=REVIEWER_ID,
        )

    assert ticket.current_status() == TicketStatus.EXECUTED