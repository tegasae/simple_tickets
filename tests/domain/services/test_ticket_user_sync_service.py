# tests/domain/services/test_ticket_user_sync_service.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.exceptions import DomainOperationError
from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_status_record import TicketStatusRecord
from src.domain.services.ticket_user_sync_service import TicketUserSyncService
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser, TicketUserStatus


BASE_TIME = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)


def make_linked_ticket_and_ticket_user() -> tuple[Ticket, TicketUser]:
    ticket_user = TicketUser.create(
        ticket_id=100,
        client_id=10,
        user_id=200,
        text_of_ticket="Need help",
    )

    ticket = Ticket.create_from_ticket_user(
        ticket_id=1,
        client_id=10,
        user_id=200,
        contact_user_id=0,
        text_of_ticket="Need help",
        user_ticket_id=100,
    )

    return ticket, ticket_user


def append_ticket_status(
    ticket: Ticket,
    *,
    actor_employee_id: int,
    status: TicketStatus,
    executor_id: int = 0,
    planned_start_at: datetime | None = None,
    planned_finish_at: datetime | None = None,
    actual_started_at: datetime | None = None,
    actual_finished_at: datetime | None = None,
    comment: str = "",
) -> None:
    record = TicketStatusRecord(
        actor_employee_id=actor_employee_id,
        status=status,
        executor_id=executor_id,
        planned_start_at=planned_start_at,
        planned_finish_at=planned_finish_at,
        actual_started_at=actual_started_at,
        actual_finished_at=actual_finished_at,
        comment=comment,
    )

    ticket.append_status(record)


def accept_ticket(ticket: Ticket, *, actor_admin_id: int = 500) -> None:
    append_ticket_status(
        ticket,
        actor_employee_id=actor_admin_id,
        status=TicketStatus.ACCEPTED,
    )


def reject_ticket(ticket: Ticket, *, actor_admin_id: int = 500) -> None:
    append_ticket_status(
        ticket,
        actor_employee_id=actor_admin_id,
        status=TicketStatus.REJECTED,
        comment="Rejected",
    )


def cancel_ticket(ticket: Ticket, *, actor_admin_id: int = 500) -> None:
    append_ticket_status(
        ticket,
        actor_employee_id=actor_admin_id,
        status=TicketStatus.CANCELLED,
        comment="Cancelled",
    )


def cancel_ticket_by_user(ticket: Ticket) -> None:
    append_ticket_status(
        ticket,
        actor_employee_id=0,
        status=TicketStatus.CANCELLED_BY_USER,
        comment="User cancelled",
    )


def assign_ticket(
    ticket: Ticket,
    *,
    actor_admin_id: int = 500,
    executor_id: int = 600,
) -> None:
    append_ticket_status(
        ticket,
        actor_employee_id=actor_admin_id,
        status=TicketStatus.ASSIGNED,
        executor_id=executor_id,
    )


def schedule_ticket(
    ticket: Ticket,
    *,
    actor_admin_id: int = 500,
) -> None:
    append_ticket_status(
        ticket,
        actor_employee_id=actor_admin_id,
        status=TicketStatus.SCHEDULED,
        planned_start_at=BASE_TIME,
        planned_finish_at=BASE_TIME + timedelta(hours=2),
    )


def ready_to_work_ticket(
    ticket: Ticket,
    *,
    actor_admin_id: int = 500,
    executor_id: int = 600,
) -> None:
    append_ticket_status(
        ticket,
        actor_employee_id=actor_admin_id,
        status=TicketStatus.READY_TO_WORK,
        executor_id=executor_id,
        planned_start_at=BASE_TIME,
        planned_finish_at=BASE_TIME + timedelta(hours=2),
    )


def start_work_ticket(
    ticket: Ticket,
    *,
    executor_id: int = 600,
) -> None:
    append_ticket_status(
        ticket,
        actor_employee_id=executor_id,
        status=TicketStatus.AT_WORK,
        executor_id=executor_id,
        actual_started_at=BASE_TIME,
    )


def pause_work_ticket(
    ticket: Ticket,
    *,
    executor_id: int = 600,
) -> None:
    append_ticket_status(
        ticket,
        actor_employee_id=executor_id,
        status=TicketStatus.PAUSED,
        executor_id=executor_id,
        comment="Pause",
    )

def ready_for_review_ticket(
    ticket: Ticket,
    *,
    executor_id: int = 600,
) -> None:
    append_ticket_status(
        ticket,
        actor_employee_id=executor_id,
        status=TicketStatus.READY_FOR_REVIEW,
        executor_id=executor_id,
        actual_started_at=BASE_TIME,
        actual_finished_at=BASE_TIME + timedelta(hours=2),
    )


def execute_ticket(
    ticket: Ticket,
    *,
    actor_admin_id: int = 500,
) -> None:
    append_ticket_status(
        ticket,
        actor_employee_id=actor_admin_id,
        status=TicketStatus.EXECUTED,
    )


def sync_ticket_user(
    ticket: Ticket,
    ticket_user: TicketUser,
    *,
    actor_employee_id: int = 500,
    comment: str = "",
) -> bool:
    return TicketUserSyncService.sync_from_ticket(
        ticket=ticket,
        ticket_user=ticket_user,
        actor_employee_id=actor_employee_id,
        comment=comment,
    )


def accept_and_sync(
    ticket: Ticket,
    ticket_user: TicketUser,
    *,
    actor_admin_id: int = 500,
) -> None:
    accept_ticket(
        ticket,
        actor_admin_id=actor_admin_id,
    )

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=actor_admin_id,
    )

    assert changed
    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert ticket_user.current_status() == TicketUserStatus.CONFIRMED_BY_ADMIN


def move_to_in_work_by_assignment_and_sync(
    ticket: Ticket,
    ticket_user: TicketUser,
    *,
    actor_admin_id: int = 500,
    executor_id: int = 600,
) -> None:
    assign_ticket(
        ticket,
        actor_admin_id=actor_admin_id,
        executor_id=executor_id,
    )

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=actor_admin_id,
    )

    assert changed
    assert ticket.current_status() == TicketStatus.ASSIGNED
    assert ticket_user.current_status() == TicketUserStatus.IN_WORK


def move_to_ready_for_review_and_sync(
    ticket: Ticket,
    ticket_user: TicketUser,
    *,
    executor_id: int = 600,
) -> None:
    ready_for_review_ticket(
        ticket,
        executor_id=executor_id,
    )

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=executor_id,
    )

    assert changed
    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert ticket_user.current_status() == TicketUserStatus.WAITING_FOR_CONFIRMATION


def test_created_from_ticket_user_has_no_sync_target() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=500,
    )

    assert not changed
    assert ticket.current_status() == TicketStatus.CREATED_FROM_TICKET_USER
    assert ticket_user.current_status() == TicketUserStatus.CREATED


def test_accepted_syncs_to_confirmed_by_admin() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    accept_ticket(
        ticket,
        actor_admin_id=500,
    )

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=500,
    )

    assert changed
    assert ticket.current_status() == TicketStatus.ACCEPTED
    assert ticket_user.current_status() == TicketUserStatus.CONFIRMED_BY_ADMIN


@pytest.mark.parametrize(
    "move_ticket_to_in_work_status",
    [
        schedule_ticket,
        assign_ticket,
        ready_to_work_ticket,
    ],
)
def test_pre_work_statuses_sync_to_in_work(
    move_ticket_to_in_work_status,
) -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    accept_and_sync(
        ticket,
        ticket_user,
    )

    move_ticket_to_in_work_status(ticket)

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=500,
    )

    assert changed
    assert ticket_user.current_status() == TicketUserStatus.IN_WORK


def test_at_work_syncs_to_in_work() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    accept_and_sync(
        ticket,
        ticket_user,
    )

    assign_ticket(
        ticket,
        actor_admin_id=500,
        executor_id=600,
    )
    start_work_ticket(
        ticket,
        executor_id=600,
    )

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=600,
    )

    assert changed
    assert ticket.current_status() == TicketStatus.AT_WORK
    assert ticket_user.current_status() == TicketUserStatus.IN_WORK


def test_paused_syncs_to_in_work() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    accept_and_sync(
        ticket,
        ticket_user,
    )

    assign_ticket(
        ticket,
        actor_admin_id=500,
        executor_id=600,
    )
    start_work_ticket(
        ticket,
        executor_id=600,
    )
    pause_work_ticket(
        ticket,
        executor_id=600,
    )

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=600,
    )

    assert changed
    assert ticket.current_status() == TicketStatus.PAUSED
    assert ticket_user.current_status() == TicketUserStatus.IN_WORK


def test_ready_for_review_syncs_to_waiting_for_confirmation() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    accept_and_sync(
        ticket,
        ticket_user,
    )
    move_to_in_work_by_assignment_and_sync(
        ticket,
        ticket_user,
    )

    ready_for_review_ticket(
        ticket,
        executor_id=600,
    )

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=600,
    )

    assert changed
    assert ticket.current_status() == TicketStatus.READY_FOR_REVIEW
    assert ticket_user.current_status() == TicketUserStatus.WAITING_FOR_CONFIRMATION


def test_executed_syncs_to_execution_confirmed_by_admin() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    accept_and_sync(
        ticket,
        ticket_user,
    )
    move_to_in_work_by_assignment_and_sync(
        ticket,
        ticket_user,
    )
    move_to_ready_for_review_and_sync(
        ticket,
        ticket_user,
    )

    execute_ticket(
        ticket,
        actor_admin_id=500,
    )

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=500,
    )

    assert changed
    assert ticket.current_status() == TicketStatus.EXECUTED
    assert ticket_user.current_status() == (
        TicketUserStatus.EXECUTION_CONFIRMED_BY_ADMIN
    )


def test_rejected_syncs_to_cancelled_by_admin() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    reject_ticket(
        ticket,
        actor_admin_id=500,
    )

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=500,
        comment="Rejected",
    )

    assert changed
    assert ticket.current_status() == TicketStatus.REJECTED
    assert ticket_user.current_status() == TicketUserStatus.CANCELLED_BY_ADMIN


def test_cancelled_syncs_to_cancelled_by_admin() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    accept_and_sync(
        ticket,
        ticket_user,
    )

    cancel_ticket(
        ticket,
        actor_admin_id=500,
    )

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=500,
        comment="Cancelled",
    )

    assert changed
    assert ticket.current_status() == TicketStatus.CANCELLED
    assert ticket_user.current_status() == TicketUserStatus.CANCELLED_BY_ADMIN


def test_cancelled_by_user_syncs_to_cancelled_by_user() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    cancel_ticket_by_user(ticket)

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=200,
        comment="User cancelled",
    )

    assert changed
    assert ticket.current_status() == TicketStatus.CANCELLED_BY_USER
    assert ticket_user.current_status() == TicketUserStatus.CANCELLED_BY_USER


def test_sync_returns_false_when_ticket_user_already_has_target_status() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    accept_ticket(
        ticket,
        actor_admin_id=500,
    )

    first_changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=500,
    )
    second_changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=500,
    )

    assert first_changed
    assert not second_changed
    assert ticket_user.current_status() == TicketUserStatus.CONFIRMED_BY_ADMIN


def test_terminal_ticket_user_is_not_overwritten_by_ticket_execution() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    accept_and_sync(
        ticket,
        ticket_user,
    )
    move_to_in_work_by_assignment_and_sync(
        ticket,
        ticket_user,
    )
    move_to_ready_for_review_and_sync(
        ticket,
        ticket_user,
    )

    ticket_user.confirm_execution_by_user(
        actor_employee_id=200,
        comment="Confirmed by user",
    )

    execute_ticket(
        ticket,
        actor_admin_id=500,
    )

    changed = sync_ticket_user(
        ticket,
        ticket_user,
        actor_employee_id=500,
    )

    assert not changed
    assert ticket.current_status() == TicketStatus.EXECUTED
    assert ticket_user.current_status() == (
        TicketUserStatus.EXECUTION_CONFIRMED_BY_USER
    )


def test_sync_rejects_zero_actor_for_real_target_status() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    accept_ticket(
        ticket,
        actor_admin_id=500,
    )

    with pytest.raises(DomainOperationError):
        sync_ticket_user(
            ticket,
            ticket_user,
            actor_employee_id=0,
        )


def test_sync_rejects_unlinked_ticket() -> None:
    ticket_user = TicketUser.create(
        ticket_id=100,
        client_id=10,
        user_id=200,
        text_of_ticket="Need help",
    )

    ticket = Ticket.create(
        ticket_id=1,
        client_id=10,
        admin_id=500,
        text_of_ticket="Internal ticket",
    )

    with pytest.raises(DomainOperationError):
        sync_ticket_user(
            ticket,
            ticket_user,
            actor_employee_id=500,
        )


def test_sync_rejects_ticket_user_id_mismatch() -> None:
    ticket, ticket_user = make_linked_ticket_and_ticket_user()

    other_ticket_user = TicketUser.create(
        ticket_id=101,
        client_id=10,
        user_id=200,
        text_of_ticket="Other request",
    )

    with pytest.raises(DomainOperationError):
        sync_ticket_user(
            ticket,
            other_ticket_user,
            actor_employee_id=500,
        )


def test_sync_rejects_client_mismatch() -> None:
    ticket, _ticket_user = make_linked_ticket_and_ticket_user()

    wrong_client_ticket_user = TicketUser.create(
        ticket_id=100,
        client_id=11,
        user_id=200,
        text_of_ticket="Wrong client",
    )

    with pytest.raises(DomainOperationError):
        sync_ticket_user(
            ticket,
            wrong_client_ticket_user,
            actor_employee_id=500,
        )


def test_sync_rejects_user_mismatch() -> None:
    ticket, _ticket_user = make_linked_ticket_and_ticket_user()

    wrong_user_ticket_user = TicketUser.create(
        ticket_id=100,
        client_id=10,
        user_id=201,
        text_of_ticket="Wrong user",
    )

    with pytest.raises(DomainOperationError):
        sync_ticket_user(
            ticket,
            wrong_user_ticket_user,
            actor_employee_id=500,
        )