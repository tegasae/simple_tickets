"""
TICKET_TRANSITIONS
   Allowed transitions between Ticket statuses.

Payload validation of a concrete TicketStatusRecord belongs to
TicketStatusRecord and is not implemented here.
"""


from typing import Final

from src.domain.statuses.ticket_status import TicketStatus

TICKET_TRANSITIONS: Final[
    dict[TicketStatus, frozenset[TicketStatus]]
] = {
    TicketStatus.CREATED: frozenset({
        TicketStatus.ACCEPTED,
        TicketStatus.REJECTED,
        TicketStatus.SUSPENDED,
    }),

    TicketStatus.CREATED_FROM_TICKET_USER: frozenset({
        TicketStatus.ACCEPTED,
        TicketStatus.REJECTED,
        TicketStatus.SUSPENDED,
    }),

    TicketStatus.REJECTED: frozenset(),

    TicketStatus.ACCEPTED: frozenset({
        TicketStatus.ASSIGNED,
        TicketStatus.DEFERRED,
        TicketStatus.SUSPENDED,
        TicketStatus.CANCELLED,
        TicketStatus.CANCELLED_BY_USER,
    }),

    TicketStatus.DEFERRED: frozenset({
        TicketStatus.ACCEPTED,
        TicketStatus.ASSIGNED,
        TicketStatus.SUSPENDED,
        TicketStatus.CANCELLED,
        TicketStatus.CANCELLED_BY_USER,
    }),

    TicketStatus.SUSPENDED: frozenset({
        TicketStatus.ACCEPTED,
        TicketStatus.DEFERRED,
        TicketStatus.ASSIGNED,
        TicketStatus.READY_FOR_REVIEW,
        TicketStatus.EXECUTED,
        TicketStatus.CANCELLED,
    }),

    TicketStatus.ASSIGNED: frozenset({
        TicketStatus.ACCEPTED,
        TicketStatus.ASSIGNED,
        TicketStatus.AT_WORK,
        TicketStatus.DEFERRED,
        TicketStatus.SUSPENDED,
        TicketStatus.CANCELLED,
        TicketStatus.CANCELLED_BY_USER,
    }),

    TicketStatus.AT_WORK: frozenset({
        TicketStatus.ASSIGNED,
        TicketStatus.PAUSED,
        TicketStatus.DEFERRED,
        TicketStatus.READY_FOR_REVIEW,
        TicketStatus.CANCELLED,
        TicketStatus.CANCELLED_BY_USER,
    }),

    TicketStatus.PAUSED: frozenset({
        TicketStatus.AT_WORK,
        TicketStatus.ASSIGNED,
        TicketStatus.DEFERRED,
        TicketStatus.SUSPENDED,
        TicketStatus.CANCELLED,
        TicketStatus.CANCELLED_BY_USER,
    }),

    TicketStatus.READY_FOR_REVIEW: frozenset({
        TicketStatus.ASSIGNED,
        TicketStatus.SUSPENDED,
        TicketStatus.EXECUTION_CONFIRMED_BY_USER,
        TicketStatus.EXECUTED,
        TicketStatus.CANCELLED,
        TicketStatus.CANCELLED_BY_USER,
    }),

    TicketStatus.EXECUTION_CONFIRMED_BY_USER: frozenset({
        TicketStatus.SUSPENDED,
        TicketStatus.EXECUTED,
    }),

    TicketStatus.EXECUTED: frozenset(),

    TicketStatus.CANCELLED: frozenset(),

    TicketStatus.CANCELLED_BY_USER: frozenset(),
}


TERMINAL_TICKET_STATUSES: Final[
    frozenset[TicketStatus]
] = frozenset({
    TicketStatus.REJECTED,
    TicketStatus.EXECUTED,
    TicketStatus.CANCELLED,
    TicketStatus.CANCELLED_BY_USER,
})


FIRST_TICKET_STATUSES: Final[
    frozenset[TicketStatus]
] = frozenset({
    TicketStatus.CREATED,
    TicketStatus.CREATED_FROM_TICKET_USER,
})



def _validate_ticket_transitions() -> None:
    """
    Validate completeness and basic consistency of the workflow graph.

    The validation ensures that:

    - every TicketStatus has a transition definition;
    - every terminal status has no outgoing transitions;
    - every non-terminal status has at least one outgoing transition;
    - every transition target is a valid TicketStatus.
    """

    missing: list[TicketStatus] = [
        status
        for status in TicketStatus
        if status not in TICKET_TRANSITIONS
    ]

    if missing:
        raise RuntimeError(
            "Ticket statuses without transition rules: "
            + ", ".join(map(str, missing))
        )

    for status, next_statuses in TICKET_TRANSITIONS.items():
        if status in TERMINAL_TICKET_STATUSES:
            if next_statuses:
                raise RuntimeError(
                    f"Terminal Ticket status {status} "
                    "cannot have outgoing transitions"
                )
            continue

        if not next_statuses:
            raise RuntimeError(
                f"Non-terminal Ticket status {status} "
                "must have at least one outgoing transition"
            )

        invalid_targets = [
            next_status
            for next_status in next_statuses
            if not isinstance(next_status, TicketStatus)
        ]

        if invalid_targets:
            raise RuntimeError(
                f"Ticket status {status} contains invalid "
                f"transition targets: {invalid_targets}"
            )


def _validate_first_ticket_statuses() -> None:
    """
    Validate initial Ticket statuses.

    Initial statuses must be valid TicketStatus values and must not
    be terminal.
    """

    for status in FIRST_TICKET_STATUSES:
        if status in TERMINAL_TICKET_STATUSES:
            raise RuntimeError(
                f"Initial Ticket status {status} cannot be terminal"
            )



_validate_ticket_transitions()
_validate_first_ticket_statuses()