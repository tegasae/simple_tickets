"""
TicketUser workflow transitions.

This module defines:

- initial TicketUser statuses;
- terminal TicketUser statuses;
- allowed transitions between TicketUser statuses;
- basic consistency validation of the transition graph.

The graph describes only workflow transitions.

Intrinsic properties of statuses, such as:

- whether the action is performed by a User or Admin;
- whether a comment is required;

belong to TicketUserStatusRule and are not defined here.
"""

from typing import Final

from .ticket_user_status import TicketUserStatus


FIRST_TICKET_USER_STATUSES: Final[
    frozenset[TicketUserStatus]
] = frozenset({
    TicketUserStatus.CREATED,
})


TERMINAL_TICKET_USER_STATUSES: Final[
    frozenset[TicketUserStatus]
] = frozenset({
    TicketUserStatus.CONFIRMED_BY_USER,
    TicketUserStatus.CONFIRMED_BY_ADMIN,
    TicketUserStatus.CANCELLED_BY_USER,
    TicketUserStatus.CANCELLED_BY_ADMIN,
})


TICKET_USER_TRANSITIONS: Final[
    dict[TicketUserStatus, frozenset[TicketUserStatus]]
] = {
    TicketUserStatus.CREATED: frozenset({
        TicketUserStatus.IN_WORK,
        TicketUserStatus.SUSPENDED,
        TicketUserStatus.CANCELLED_BY_USER,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.IN_WORK: frozenset({
        TicketUserStatus.WAITING_FOR_CONFIRMATION,
        TicketUserStatus.SUSPENDED,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.WAITING_FOR_CONFIRMATION: frozenset({
        TicketUserStatus.IN_WORK,
        TicketUserStatus.CONFIRMED_BY_USER,
        TicketUserStatus.CONFIRMED_BY_ADMIN,
        TicketUserStatus.SUSPENDED,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.SUSPENDED: frozenset({
        TicketUserStatus.IN_WORK,
        TicketUserStatus.WAITING_FOR_CONFIRMATION,
        TicketUserStatus.CONFIRMED_BY_ADMIN,
        TicketUserStatus.CANCELLED_BY_ADMIN,
    }),

    TicketUserStatus.CONFIRMED_BY_USER: frozenset(),

    TicketUserStatus.CONFIRMED_BY_ADMIN: frozenset(),

    TicketUserStatus.CANCELLED_BY_USER: frozenset(),

    TicketUserStatus.CANCELLED_BY_ADMIN: frozenset(),
}


def _validate_ticket_user_transitions() -> None:
    """
    Validate completeness and basic consistency of the TicketUser
    workflow graph.

    Validation guarantees that:

    - every TicketUserStatus has a transition definition;
    - terminal statuses have no outgoing transitions;
    - non-terminal statuses have at least one outgoing transition;
    - every transition target is a TicketUserStatus.
    """

    missing: list[TicketUserStatus] = [
        status
        for status in TicketUserStatus
        if status not in TICKET_USER_TRANSITIONS
    ]

    if missing:
        raise RuntimeError(
            "TicketUser statuses without transition rules: "
            + ", ".join(map(str, missing))
        )

    for status, next_statuses in TICKET_USER_TRANSITIONS.items():
        if status in TERMINAL_TICKET_USER_STATUSES:
            if next_statuses:
                raise RuntimeError(
                    f"Terminal TicketUser status {status} "
                    "cannot have outgoing transitions"
                )
            continue

        if not next_statuses:
            raise RuntimeError(
                f"Non-terminal TicketUser status {status} "
                "must have at least one outgoing transition"
            )

        invalid_targets = [
            next_status
            for next_status in next_statuses
            if not isinstance(next_status, TicketUserStatus)
        ]

        if invalid_targets:
            raise RuntimeError(
                f"TicketUser status {status} contains invalid "
                f"transition targets: {invalid_targets}"
            )


def _validate_first_ticket_user_statuses() -> None:
    """
    Validate initial TicketUser statuses.

    Initial statuses must not be terminal.
    """

    for status in FIRST_TICKET_USER_STATUSES:
        if status in TERMINAL_TICKET_USER_STATUSES:
            raise RuntimeError(
                f"Initial TicketUser status {status} "
                "cannot be terminal"
            )

_validate_ticket_user_transitions()
_validate_first_ticket_user_statuses()