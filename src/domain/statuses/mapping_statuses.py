"""
Mapping between TicketStatus and TicketUserStatus.

TicketUser represents a simplified user-facing view of the internal
Ticket workflow.

Several Ticket statuses may correspond to the same TicketUser status.

The mapping describes state correspondence only.
It does not define allowed transitions and does not perform
Ticket/TicketUser synchronization.
"""

from typing import Final

from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_user_status import TicketUserStatus


TICKET_TO_TICKET_USER_STATUS: Final[
    dict[TicketStatus, TicketUserStatus]
] = {
    #
    # Initial state
    #
    TicketStatus.CREATED:
        TicketUserStatus.CREATED,

    TicketStatus.CREATED_FROM_TICKET_USER:
        TicketUserStatus.CREATED,

    #
    # Ticket is being processed by the service.
    #
    TicketStatus.ACCEPTED:
        TicketUserStatus.IN_WORK,

    TicketStatus.DEFERRED:
        TicketUserStatus.IN_WORK,

    TicketStatus.ASSIGNED:
        TicketUserStatus.IN_WORK,

    TicketStatus.AT_WORK:
        TicketUserStatus.IN_WORK,

    TicketStatus.PAUSED:
        TicketUserStatus.IN_WORK,

    #
    # Ticket is suspended because the related Client/User is disabled.
    #
    TicketStatus.SUSPENDED:
        TicketUserStatus.SUSPENDED,

    #
    # Work is finished and waiting for confirmation.
    #
    TicketStatus.READY_FOR_REVIEW:
        TicketUserStatus.WAITING_FOR_CONFIRMATION,

    #
    # Final states.
    #
    TicketStatus.CONFIRMED_BY_USER:
        TicketUserStatus.CONFIRMED_BY_USER,

    TicketStatus.EXECUTED:
        TicketUserStatus.CONFIRMED_BY_ADMIN,

    TicketStatus.REJECTED:
        TicketUserStatus.CANCELLED_BY_ADMIN,

    TicketStatus.CANCELLED:
        TicketUserStatus.CANCELLED_BY_ADMIN,

    TicketStatus.CANCELLED_BY_USER:
        TicketUserStatus.CANCELLED_BY_USER,
}


def _validate_ticket_to_ticket_user_status_mapping() -> None:
    """
    Validate completeness of the Ticket -> TicketUser status mapping.

    Every TicketStatus must have a corresponding TicketUserStatus.
    """

    missing: list[TicketStatus] = [
        status
        for status in TicketStatus
        if status not in TICKET_TO_TICKET_USER_STATUS
    ]

    if missing:
        raise RuntimeError(
            "Ticket statuses without TicketUser status mapping: "
            + ", ".join(map(str, missing))
        )

    invalid_targets = [
        ticket_user_status
        for ticket_user_status in TICKET_TO_TICKET_USER_STATUS.values()
        if not isinstance(ticket_user_status, TicketUserStatus)
    ]

    if invalid_targets:
        raise RuntimeError(
            "Invalid TicketUser statuses in mapping: "
            + ", ".join(map(str, invalid_targets))
        )


_validate_ticket_to_ticket_user_status_mapping()