
from typing import Final

from src.domain.statuses.ticket_status import TicketStatus
from src.domain.statuses.rules.ticket_transition_rule import (
    TicketTransitionRule,
)
from src.domain.statuses.rules.ticket_transition_validators import (
    validate_current_executor,
    validate_start_work,
    validate_no_retrospective_work,
)


# Transition without additional validators.
DEFAULT_RULE = TicketTransitionRule()


TICKET_TRANSITIONS: Final[
    dict[TicketStatus, dict[TicketStatus, TicketTransitionRule]]
] = {
    TicketStatus.CREATED: {
        TicketStatus.ACCEPTED: DEFAULT_RULE,
        TicketStatus.REJECTED: DEFAULT_RULE,
        TicketStatus.SUSPENDED: DEFAULT_RULE,
    },

    TicketStatus.CREATED_FROM_TICKET_USER: {
        TicketStatus.ACCEPTED: DEFAULT_RULE,
        TicketStatus.REJECTED: DEFAULT_RULE,
        TicketStatus.CANCELLED_BY_USER: DEFAULT_RULE,
        TicketStatus.SUSPENDED: DEFAULT_RULE,
    },

    TicketStatus.CREATED_FROM_REQUEST_USER: {
        TicketStatus.ACCEPTED: DEFAULT_RULE,
        TicketStatus.REJECTED: DEFAULT_RULE,
        TicketStatus.CANCELLED_BY_USER: DEFAULT_RULE,
        TicketStatus.SUSPENDED: DEFAULT_RULE,
    },

    TicketStatus.REJECTED: {},

    TicketStatus.ACCEPTED: {
        TicketStatus.ASSIGNED: DEFAULT_RULE,
        TicketStatus.DEFERRED: DEFAULT_RULE,
        TicketStatus.SUSPENDED: DEFAULT_RULE,
        TicketStatus.CANCELLED: DEFAULT_RULE,
    },

    TicketStatus.DEFERRED: {
        TicketStatus.ACCEPTED: DEFAULT_RULE,
        TicketStatus.ASSIGNED: DEFAULT_RULE,
        TicketStatus.SUSPENDED: DEFAULT_RULE,
        TicketStatus.CANCELLED: DEFAULT_RULE,
    },

    TicketStatus.ASSIGNED: {
        TicketStatus.ACCEPTED: DEFAULT_RULE,
        TicketStatus.ASSIGNED: DEFAULT_RULE,

        TicketStatus.AT_WORK: TicketTransitionRule(
            validators=(validate_start_work,),
        ),

        TicketStatus.DEFERRED: DEFAULT_RULE,
        TicketStatus.SUSPENDED: DEFAULT_RULE,
        TicketStatus.CANCELLED: DEFAULT_RULE,
    },

    TicketStatus.AT_WORK: {
        TicketStatus.ASSIGNED: DEFAULT_RULE,

        TicketStatus.PAUSED: TicketTransitionRule(
            validators=(validate_current_executor,),
        ),

        TicketStatus.DEFERRED: DEFAULT_RULE,

        TicketStatus.READY_FOR_REVIEW: TicketTransitionRule(
            validators=(validate_current_executor,),
        ),

        TicketStatus.CANCELLED: DEFAULT_RULE,
    },

    TicketStatus.PAUSED: {
        TicketStatus.AT_WORK: TicketTransitionRule(
            validators=(
                validate_no_retrospective_work,
                validate_current_executor,
            ),
        ),

        TicketStatus.ASSIGNED: DEFAULT_RULE,
        TicketStatus.DEFERRED: DEFAULT_RULE,
        TicketStatus.SUSPENDED: DEFAULT_RULE,
        TicketStatus.CANCELLED: DEFAULT_RULE,
    },

    TicketStatus.READY_FOR_REVIEW: {
        TicketStatus.ASSIGNED: DEFAULT_RULE,
        TicketStatus.CONFIRMED_BY_USER: DEFAULT_RULE,
        TicketStatus.EXECUTED: DEFAULT_RULE,
        TicketStatus.CANCELLED: DEFAULT_RULE,
    },

    TicketStatus.CONFIRMED_BY_USER: {},
    TicketStatus.EXECUTED: {},
    TicketStatus.CANCELLED: {},
    TicketStatus.CANCELLED_BY_USER: {},
    TicketStatus.SUSPENDED: {},
}


FIRST_TICKET_STATUSES: Final[
    frozenset[TicketStatus]
] = frozenset({
    TicketStatus.CREATED,
    TicketStatus.CREATED_FROM_TICKET_USER,
    TicketStatus.CREATED_FROM_REQUEST_USER,
})


TERMINAL_TICKET_STATUSES: Final[
    frozenset[TicketStatus]
] = frozenset({
    TicketStatus.REJECTED,
    TicketStatus.EXECUTED,
    TicketStatus.CANCELLED,
    TicketStatus.CANCELLED_BY_USER,
    TicketStatus.CONFIRMED_BY_USER,
    TicketStatus.SUSPENDED,
})


def _validate_ticket_transitions() -> None:
    """
    Validate completeness and consistency of workflow transitions.
    """

    missing = [
        status
        for status in TicketStatus
        if status not in TICKET_TRANSITIONS
    ]

    if missing:
        raise RuntimeError(
            "Ticket statuses without transition rules: "
            + ", ".join(map(str, missing))
        )

    if FIRST_TICKET_STATUSES & TERMINAL_TICKET_STATUSES:
        raise RuntimeError(
            "Initial Ticket statuses cannot be terminal"
        )

    for status, transitions in TICKET_TRANSITIONS.items():

        if not isinstance(status, TicketStatus):
            raise RuntimeError(
                f"Invalid Ticket transition source: {status}"
            )

        if status in TERMINAL_TICKET_STATUSES:
            if transitions:
                raise RuntimeError(
                    f"Terminal Ticket status {status} "
                    "cannot have outgoing transitions"
                )
            continue

        if not transitions:
            raise RuntimeError(
                f"Non-terminal Ticket status {status} "
                "must have at least one outgoing transition"
            )

        for next_status, rule in transitions.items():

            if not isinstance(next_status, TicketStatus):
                raise RuntimeError(
                    f"Invalid transition target: {next_status}"
                )

            if not isinstance(rule, TicketTransitionRule):
                raise RuntimeError(
                    "Invalid transition rule: "
                    f"{status} -> {next_status}"
                )


_validate_ticket_transitions()
