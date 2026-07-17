# tests/domain/services/test_ticket_management_service.py

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import (
    DomainOperationError,
    ItemValidationError,
)
from src.domain.services.ticket_management_service import (
    TicketManagementService,
)
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.ticket import Ticket


NOW = datetime.now(timezone.utc)

PAST_2H = NOW - timedelta(hours=2)
PAST_1H = NOW - timedelta(hours=1)

FUTURE_1H = NOW + timedelta(hours=1)
FUTURE_2H = NOW + timedelta(hours=2)

ADMIN_ID = 10
EXECUTOR_ID = 20
OTHER_EXECUTOR_ID = 30


# ----------------------------
# Helpers
# ----------------------------


def make_ticket() -> Ticket:
    return Ticket.create(
        ticket_id=1,
        client_id=100,
        admin_id=ADMIN_ID,
        text_of_ticket="Fix internet connection",
    )


def accept_ticket(ticket: Ticket) -> Ticket:
    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ACCEPTED,
        )
    )
    return ticket


def make_accepted_ticket() -> Ticket:
    return accept_ticket(make_ticket())


def make_deferred_ticket() -> Ticket:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.DEFERRED,
            comment="Waiting for customer information",
        )
    )

    return ticket


def make_scheduled_ticket() -> Ticket:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.SCHEDULED,
            planned_start_at=FUTURE_1H,
        )
    )

    return ticket


def make_assigned_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.ASSIGNED,
            executor_id=executor_id,
        )
    )

    return ticket


def make_ready_to_work_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_assigned_ticket(
        executor_id=executor_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.READY_TO_WORK,
            executor_id=executor_id,
            planned_start_at=FUTURE_1H,
        )
    )

    return ticket


def make_at_work_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_assigned_ticket(
        executor_id=executor_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=executor_id,
            status=TicketStatus.AT_WORK,
            executor_id=executor_id,
            actual_started_at=PAST_2H,
            date_created=PAST_2H,
        )
    )

    return ticket


def make_paused_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_at_work_ticket(
        executor_id=executor_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=executor_id,
            status=TicketStatus.PAUSED,
            executor_id=executor_id,
            date_created=PAST_1H,
        )
    )

    return ticket


def make_ready_for_review_ticket(
    *,
    executor_id: int = EXECUTOR_ID,
) -> Ticket:
    ticket = make_at_work_ticket(
        executor_id=executor_id,
    )

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=executor_id,
            status=TicketStatus.READY_FOR_REVIEW,
            executor_id=executor_id,
            actual_finished_at=PAST_1H,
            date_created=PAST_1H,
        )
    )

    return ticket


def make_rejected_ticket() -> Ticket:
    ticket = make_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.REJECTED,
            comment="Invalid request",
        )
    )

    return ticket


def make_executed_ticket() -> Ticket:
    ticket = make_ready_for_review_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.EXECUTED,
        )
    )

    return ticket


def make_cancelled_ticket() -> Ticket:
    ticket = make_accepted_ticket()

    ticket.append_status(
        TicketStatusRecord(
            actor_employee_id=ADMIN_ID,
            status=TicketStatus.CANCELLED,
            comment="Customer cancelled request",
        )
    )

    return ticket


# ----------------------------
# accept()
# ----------------------------


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_ticket,
        make_deferred_ticket,
    ],
    ids=[
        "created",
        "deferred",
    ],
)
def test_accept_creates_accepted_record_from_allowed_statuses(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    record = TicketManagementService.accept(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        comment="Accepted for processing",
    )

    assert record is ticket.current_status_record()
    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert record.actor_employee_id == ADMIN_ID
    assert record.comment == "Accepted for processing"
    assert record.executor_id == 0


# ----------------------------
# reject()
# ----------------------------


def test_reject_creates_rejected_terminal_record() -> None:
    ticket = make_ticket()

    record = TicketManagementService.reject(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        comment="Request is outside our responsibility",
    )

    assert record is ticket.current_status_record()
    assert ticket.current_status() == TicketStatus.REJECTED
    assert ticket.is_terminal()
    assert ticket.is_closed
    assert record.actor_employee_id == ADMIN_ID
    assert record.comment == "Request is outside our responsibility"
    assert record.executor_id == 0


def test_reject_requires_non_empty_reason() -> None:
    ticket = make_ticket()
    status_count_before = len(ticket.statuses)

    with pytest.raises(
        ItemValidationError,
        match="REJECTED requires comment",
    ):
        TicketManagementService.reject(
            ticket=ticket,
            actor_employee_id=ADMIN_ID,
            comment="   ",
        )

    assert len(ticket.statuses) == status_count_before
    assert ticket.current_status() == TicketStatus.CREATED


# ----------------------------
# defer()
# ----------------------------


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_accepted_ticket,
        make_scheduled_ticket,
        make_assigned_ticket,
        make_ready_to_work_ticket,
        make_at_work_ticket,
        make_paused_ticket,
        make_ready_for_review_ticket,
    ],
    ids=[
        "accepted",
        "scheduled",
        "assigned",
        "ready_to_work",
        "at_work",
        "paused",
        "ready_for_review",
    ],
)
def test_defer_creates_deferred_record_from_allowed_statuses(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    record = TicketManagementService.defer(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        comment="Waiting for access approval",
    )

    assert record is ticket.current_status_record()
    assert ticket.current_status() == TicketStatus.DEFERRED
    assert record.actor_employee_id == ADMIN_ID
    assert record.comment == "Waiting for access approval"
    assert record.executor_id == 0
    assert record.planned_start_at is None
    assert record.actual_started_at is None


def test_defer_requires_non_empty_reason() -> None:
    ticket = make_accepted_ticket()
    status_count_before = len(ticket.statuses)

    with pytest.raises(
        ItemValidationError,
        match="DEFERRED requires comment",
    ):
        TicketManagementService.defer(
            ticket=ticket,
            actor_employee_id=ADMIN_ID,
            comment="",
        )

    assert len(ticket.statuses) == status_count_before
    assert ticket.current_status() == TicketStatus.ACCEPTED


# ----------------------------
# schedule()
# ----------------------------


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_accepted_ticket,
        make_deferred_ticket,
        make_scheduled_ticket,
        make_assigned_ticket,
        make_ready_to_work_ticket,
        make_at_work_ticket,
        make_paused_ticket,
        make_ready_for_review_ticket,
    ],
    ids=[
        "accepted",
        "deferred",
        "scheduled",
        "assigned",
        "ready_to_work",
        "at_work",
        "paused",
        "ready_for_review",
    ],
)
def test_schedule_creates_scheduled_record_from_allowed_statuses(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    record = TicketManagementService.schedule(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        planned_start_at=FUTURE_1H,
        planned_finish_at=FUTURE_2H,
        comment="Scheduled for tomorrow",
    )

    assert record is ticket.current_status_record()
    assert ticket.current_status() == TicketStatus.SCHEDULED
    assert record.actor_employee_id == ADMIN_ID
    assert record.executor_id == 0
    assert record.planned_start_at == FUTURE_1H
    assert record.planned_finish_at == FUTURE_2H
    assert record.comment == "Scheduled for tomorrow"


def test_schedule_rejects_finish_before_start() -> None:
    ticket = make_accepted_ticket()
    status_count_before = len(ticket.statuses)

    with pytest.raises(
        ItemValidationError,
        match="Planned finish cannot be before planned start",
    ):
        TicketManagementService.schedule(
            ticket=ticket,
            actor_employee_id=ADMIN_ID,
            planned_start_at=FUTURE_2H,
            planned_finish_at=FUTURE_1H,
        )

    assert len(ticket.statuses) == status_count_before
    assert ticket.current_status() == TicketStatus.ACCEPTED


# ----------------------------
# assign()
# ----------------------------


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_accepted_ticket,
        make_deferred_ticket,
        make_scheduled_ticket,
        make_assigned_ticket,
        make_ready_to_work_ticket,
        make_at_work_ticket,
        make_paused_ticket,
        make_ready_for_review_ticket,
    ],
    ids=[
        "accepted",
        "deferred",
        "scheduled",
        "assigned",
        "ready_to_work",
        "at_work",
        "paused",
        "ready_for_review",
    ],
)
def test_assign_creates_assigned_record_from_allowed_statuses(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    record = TicketManagementService.assign(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        executor_id=OTHER_EXECUTOR_ID,
        comment="Assigned to field engineer",
    )

    assert record is ticket.current_status_record()
    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket.current_executor_id() == OTHER_EXECUTOR_ID
    assert record.actor_employee_id == ADMIN_ID
    assert record.executor_id == OTHER_EXECUTOR_ID
    assert record.comment == "Assigned to field engineer"
    assert record.planned_start_at is None


def test_assign_requires_positive_executor_id() -> None:
    ticket = make_accepted_ticket()
    status_count_before = len(ticket.statuses)

    with pytest.raises(
        ItemValidationError,
        match="Status assigned requires executor",
    ):
        TicketManagementService.assign(
            ticket=ticket,
            actor_employee_id=ADMIN_ID,
            executor_id=0,
        )

    assert len(ticket.statuses) == status_count_before
    assert ticket.current_status() == TicketStatus.ACCEPTED


# ----------------------------
# ready_to_work()
# ----------------------------


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_accepted_ticket,
        make_deferred_ticket,
        make_scheduled_ticket,
        make_assigned_ticket,
        make_ready_to_work_ticket,
        make_at_work_ticket,
        make_paused_ticket,
        make_ready_for_review_ticket,
    ],
    ids=[
        "accepted",
        "deferred",
        "scheduled",
        "assigned",
        "ready_to_work",
        "at_work",
        "paused",
        "ready_for_review",
    ],
)
def test_ready_to_work_creates_record_from_allowed_statuses(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    record = TicketManagementService.ready_to_work(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        executor_id=OTHER_EXECUTOR_ID,
        planned_start_at=FUTURE_1H,
        planned_finish_at=FUTURE_2H,
        comment="Engineer and time slot confirmed",
    )

    assert record is ticket.current_status_record()
    assert ticket.current_status() == TicketStatus.READY_TO_WORK
    assert ticket.current_executor_id() == OTHER_EXECUTOR_ID
    assert record.actor_employee_id == ADMIN_ID
    assert record.executor_id == OTHER_EXECUTOR_ID
    assert record.planned_start_at == FUTURE_1H
    assert record.planned_finish_at == FUTURE_2H
    assert record.comment == "Engineer and time slot confirmed"


def test_ready_to_work_requires_positive_executor_id() -> None:
    ticket = make_accepted_ticket()
    status_count_before = len(ticket.statuses)

    with pytest.raises(
        ItemValidationError,
        match="Status ready_to_work requires executor",
    ):
        TicketManagementService.ready_to_work(
            ticket=ticket,
            actor_employee_id=ADMIN_ID,
            executor_id=0,
            planned_start_at=FUTURE_1H,
        )

    assert len(ticket.statuses) == status_count_before
    assert ticket.current_status() == TicketStatus.ACCEPTED


# ----------------------------
# cancel()
# ----------------------------


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_accepted_ticket,
        make_deferred_ticket,
        make_scheduled_ticket,
        make_assigned_ticket,
        make_ready_to_work_ticket,
        make_at_work_ticket,
        make_paused_ticket,
        make_ready_for_review_ticket,
    ],
    ids=[
        "accepted",
        "deferred",
        "scheduled",
        "assigned",
        "ready_to_work",
        "at_work",
        "paused",
        "ready_for_review",
    ],
)
def test_cancel_creates_cancelled_terminal_record_from_allowed_statuses(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    record = TicketManagementService.cancel(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        comment="Customer cancelled the request",
    )

    assert record is ticket.current_status_record()
    assert ticket.current_status() == TicketStatus.CANCELLED
    assert ticket.is_terminal()
    assert ticket.is_closed
    assert record.actor_employee_id == ADMIN_ID
    assert record.comment == "Customer cancelled the request"
    assert record.executor_id == 0


def test_cancel_requires_non_empty_reason() -> None:
    ticket = make_accepted_ticket()
    status_count_before = len(ticket.statuses)

    with pytest.raises(
        ItemValidationError,
        match="CANCELLED requires comment",
    ):
        TicketManagementService.cancel(
            ticket=ticket,
            actor_employee_id=ADMIN_ID,
            comment="",
        )

    assert len(ticket.statuses) == status_count_before
    assert ticket.current_status() == TicketStatus.ACCEPTED


# ----------------------------
# Invalid workflow transitions
# ----------------------------


@pytest.mark.parametrize(
    ("operation_name", "operation"),
    [
        (
            "defer",
            lambda ticket: TicketManagementService.defer(
                ticket=ticket,
                actor_employee_id=ADMIN_ID,
                comment="Reason",
            ),
        ),
        (
            "schedule",
            lambda ticket: TicketManagementService.schedule(
                ticket=ticket,
                actor_employee_id=ADMIN_ID,
                planned_start_at=FUTURE_1H,
            ),
        ),
        (
            "assign",
            lambda ticket: TicketManagementService.assign(
                ticket=ticket,
                actor_employee_id=ADMIN_ID,
                executor_id=EXECUTOR_ID,
            ),
        ),
        (
            "ready_to_work",
            lambda ticket: TicketManagementService.ready_to_work(
                ticket=ticket,
                actor_employee_id=ADMIN_ID,
                executor_id=EXECUTOR_ID,
                planned_start_at=FUTURE_1H,
            ),
        ),
        (
            "cancel",
            lambda ticket: TicketManagementService.cancel(
                ticket=ticket,
                actor_employee_id=ADMIN_ID,
                comment="Reason",
            ),
        ),
    ],
)
def test_management_operations_reject_invalid_transition_from_created(
    operation_name: str,
    operation: Callable[[Ticket], object],
) -> None:
    ticket = make_ticket()
    status_count_before = len(ticket.statuses)

    with pytest.raises(
        DomainOperationError,
        match="transition is not allowed",
    ):
        operation(ticket)

    assert len(ticket.statuses) == status_count_before
    assert ticket.current_status() == TicketStatus.CREATED




def test_reject_rejects_invalid_transition_from_accepted() -> None:
    ticket = make_accepted_ticket()
    status_count_before = len(ticket.statuses)

    with pytest.raises(
        DomainOperationError,
        match="transition is not allowed",
    ):
        TicketManagementService.reject(
            ticket=ticket,
            actor_employee_id=ADMIN_ID,
            comment="Reason",
        )

    assert len(ticket.statuses) == status_count_before
    assert ticket.current_status() == TicketStatus.ACCEPTED


# ----------------------------
# handle_client_disabled()
# ----------------------------


def test_handle_client_disabled_rejects_created_ticket() -> None:
    ticket = make_ticket()

    changed = TicketManagementService.handle_client_disabled(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        comment="Client account was disabled",
    )

    record = ticket.current_status_record()

    assert changed is True
    assert ticket.current_status() == TicketStatus.REJECTED
    assert ticket.is_terminal()
    assert record.actor_employee_id == ADMIN_ID
    assert record.comment == "Client account was disabled"


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_accepted_ticket,
        make_scheduled_ticket,
        make_assigned_ticket,
        make_ready_to_work_ticket,
    ],
    ids=[
        "accepted",
        "scheduled",
        "assigned",
        "ready_to_work",
    ],
)
def test_handle_client_disabled_defers_required_statuses(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()

    changed = TicketManagementService.handle_client_disabled(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        comment="Client account was disabled",
    )

    record = ticket.current_status_record()

    assert changed is True
    assert ticket.current_status() == TicketStatus.DEFERRED
    assert record.actor_employee_id == ADMIN_ID
    assert record.comment == "Client account was disabled"
    assert record.executor_id == 0


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_deferred_ticket,
        make_at_work_ticket,
        make_paused_ticket,
        make_ready_for_review_ticket,
        make_rejected_ticket,
        make_executed_ticket,
        make_cancelled_ticket,
    ],
    ids=[
        "deferred",
        "at_work",
        "paused",
        "ready_for_review",
        "rejected",
        "executed",
        "cancelled",
    ],
)
def test_handle_client_disabled_keeps_other_statuses_unchanged(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()
    status_before = ticket.current_status()
    status_count_before = len(ticket.statuses)

    changed = TicketManagementService.handle_client_disabled(
        ticket=ticket,
        actor_employee_id=ADMIN_ID,
        comment="",
    )

    assert changed is False
    assert ticket.current_status() == status_before
    assert len(ticket.statuses) == status_count_before


@pytest.mark.parametrize(
    "ticket_factory",
    [
        make_ticket,
        make_accepted_ticket,
    ],
    ids=[
        "created",
        "accepted",
    ],
)
def test_handle_client_disabled_requires_reason_when_ticket_changes(
    ticket_factory: Callable[[], Ticket],
) -> None:
    ticket = ticket_factory()
    current_status_before = ticket.current_status()
    status_count_before = len(ticket.statuses)

    with pytest.raises(
        ItemValidationError,
        match="requires comment",
    ):
        TicketManagementService.handle_client_disabled(
            ticket=ticket,
            actor_employee_id=ADMIN_ID,
            comment="   ",
        )

    assert ticket.current_status() == current_status_before
    assert len(ticket.statuses) == status_count_before