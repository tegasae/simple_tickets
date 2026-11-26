
"""
Additional validators for Ticket workflow transitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.domain.exceptions import DomainOperationError

if TYPE_CHECKING:
    from src.domain.ticket import Ticket
    from src.domain.statuses.ticket_status_record import (
        TicketStatusRecord,
    )


def validate_current_executor(
    ticket: Ticket,
    record: TicketStatusRecord,
) -> None:
    """
    Require the action to be performed by the current executor.
    """
    if record.actor_employee_id != ticket.current_executor_id():
        raise DomainOperationError(
            "Only the current Ticket executor may perform "
            "this transition"
        )


def validate_start_work(
    ticket: Ticket,
    record: TicketStatusRecord,
) -> None:
    """
    Validate ASSIGNED -> AT_WORK.

    Normal work:
        Only the current executor may start work.

    Retrospective work:
        Another Admin may register already performed work.
    """
    if record.has_retrospective_work_time:
        return

    validate_current_executor(ticket, record)


def validate_no_retrospective_work(
    ticket: Ticket,
    record: TicketStatusRecord,
) -> None:
    """
    Validate PAUSED -> AT_WORK.

    Resuming work must not contain retrospective work time.
    """
    if record.has_retrospective_work_time:
        raise DomainOperationError(
            "PAUSED -> AT_WORK does not allow "
            "retrospective work time"
        )


def validate_pause_work(
    ticket: Ticket,
    record: TicketStatusRecord,
) -> None:
    """
    Validate AT_WORK -> PAUSED.

    Retrospectively registered work cannot be paused.

    Normal work may be paused only by the current executor.
    """
    current_record = ticket.current_status_record()

    if current_record.has_retrospective_work_time:
        raise DomainOperationError(
            "Retrospective work cannot be paused"
        )

    validate_current_executor(ticket, record)


def validate_submit_for_review(
    ticket: Ticket,
    record: TicketStatusRecord,
) -> None:
    """
    Validate AT_WORK -> READY_FOR_REVIEW.

    Normal work:
        Only the current executor may submit work for review.

    Retrospective work:
        Any Admin may submit the registered work for review.
    """
    current_record = ticket.current_status_record()

    if current_record.has_retrospective_work_time:
        return

    validate_current_executor(ticket, record)


def validate_user_cancellation(
    ticket: Ticket,
    record: TicketStatusRecord,
) -> None:
    """
    Validate user-initiated cancellation.

    The Ticket must be associated with an existing TicketUser.
    """
    if ticket.user_ticket_id <= 0:
        raise DomainOperationError(
            "Ticket cannot be cancelled by User "
            "without an associated TicketUser"
        )

def validate_not_current_executor(
    ticket: Ticket,
    record: TicketStatusRecord,
) -> None:
    """
    The current executor cannot perform this transition.
    """
    if record.actor_employee_id == ticket.current_executor_id():
        raise DomainOperationError(
            "The current Ticket executor cannot perform "
            "this transition"
        )