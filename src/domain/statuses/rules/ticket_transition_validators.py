# Функции дополнительных проверок переходов




from typing import TYPE_CHECKING

from src.domain.exceptions import DomainOperationError

if TYPE_CHECKING:
    from src.domain.ticket import Ticket
    from src.domain.statuses.ticket_status_record import TicketStatusRecord




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


def validate_user_cancellation(
    ticket: Ticket,
    record: TicketStatusRecord,
) -> None:
    """
    Validate CREATED -> CANCELLED_BY_USER.

    A standalone Ticket cannot be cancelled by User.
    """
    if ticket.user_ticket_id <= 0 or ticket.user_id <= 0:
        raise DomainOperationError(
            "Standalone Ticket cannot be cancelled by User"
        )
