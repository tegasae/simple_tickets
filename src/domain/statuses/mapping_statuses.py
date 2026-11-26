
"""
Mapping between TicketStatus and TicketUserStatus.

TicketUser is a simplified user-facing representation of
the Ticket workflow.

Several Ticket statuses can correspond to the same
TicketUser status.

TicketStatus.CREATED is intentionally unmapped:
it represents an internal Ticket created by an Admin,
not a user-initiated request.

This mapping describes state correspondence only.

It does not:
- decide whether a Ticket has a related TicketUser;
- validate workflow transitions;
- synchronize the two aggregates.
"""

from typing import Final

from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.ticket_user_status import TicketUserStatus


TICKET_TO_TICKET_USER_STATUS: Final[
    dict[TicketStatus, TicketUserStatus]
] = {
    # User-initiated requests.
    TicketStatus.CREATED_FROM_REQUEST_USER:
        TicketUserStatus.CREATED,

    TicketStatus.CREATED_FROM_TICKET_USER:
        TicketUserStatus.CREATED,

    # Internal processing.
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

    # Suspended processing.
    TicketStatus.SUSPENDED:
        TicketUserStatus.SUSPENDED,

    # Work completed, awaiting confirmation.
    TicketStatus.READY_FOR_REVIEW:
        TicketUserStatus.WAITING_FOR_CONFIRMATION,

    # Terminal states.
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
    Validate mapping completeness and type correctness.

    Every TicketStatus except CREATED must have
    exactly one TicketUserStatus mapping.

    Sources and targets must be actual enum members,
    not strings containing their values.
    """

    if type(TICKET_TO_TICKET_USER_STATUS) is not dict:
        raise RuntimeError(
            "TICKET_TO_TICKET_USER_STATUS must be a dict"
        )

    # Validate source types.
    invalid_sources = [
        status
        for status in TICKET_TO_TICKET_USER_STATUS
        if type(status) is not TicketStatus
    ]

    if invalid_sources:
        raise RuntimeError(
            "Invalid Ticket status mapping sources: "
            f"{invalid_sources}"
        )

    # CREATED is intentionally excluded.
    expected = set(TicketStatus) - {
        TicketStatus.CREATED,
    }

    actual = set(TICKET_TO_TICKET_USER_STATUS)

    missing = expected - actual
    unexpected = actual - expected

    if missing or unexpected:
        raise RuntimeError(
            "Invalid Ticket -> TicketUser mapping coverage. "
            f"Missing: {missing}; unexpected: {unexpected}"
        )

    # Validate target types.
    invalid_targets = [
        status
        for status in TICKET_TO_TICKET_USER_STATUS.values()
        if type(status) is not TicketUserStatus
    ]

    if invalid_targets:
        raise RuntimeError(
            "Invalid TicketUser status mapping targets: "
            f"{invalid_targets}"
        )


_validate_ticket_to_ticket_user_status_mapping()
